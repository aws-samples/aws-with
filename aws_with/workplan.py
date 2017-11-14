"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
"""

import sys
import os
import threading
import boto3
import botocore

from . import regions, utils, organizations, commands

def examine_regions(logger, options):
    """ for each region provided, use it as a regex to search for regions... """
    logger.debug("Getting list of regions")
    regions_list = regions.get_regions_list(logger)
    if options.regions:
        matched_regions = map(lambda x: regions.get_regions_from_regex(logger, x, regions_list),
                              options.regions)
        options.regions = sorted(set(utils.flatten_list(matched_regions)))
        if not options.regions:
            print("error: no matching regions found")
            sys.exit(1)
        logger.info("Set regions: %s", ", ".join(options.regions))

    # if we don't have any regions set, then try and get it from the current session...
    if not options.regions:
        logger.debug("No regions specified on command line, guessing...")
        options.regions = [boto3.session.Session().region_name]
        if options.regions == [None]:
            options.regions = ["<default>"]
            logger.info("No region set, using default")
        else:
            logger.info("Set regions: %s", ", ".join(options.regions))


def examine_accounts(logger, options, org_client):
    """ if we don't have any accounts set, then try and get guess our current account_id... """
    logger.debug("Getting list of accounts")
    if not options.accounts:
        logger.debug("No accounts specified on command line, guessing...")
        try:
            # if we have any kind of AWS credentials set then this should work...
            account_id = boto3.client("sts").get_caller_identity()["Account"]
            options.accounts = [account_id]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
            print("error: unable to work out existing account ID, "
                  "please check your AWS credentials, or specify it with the '-a' option")
            sys.exit(1)

    logger.info("Set accounts: %s", ", ".join(options.accounts))

    # if we were given OUs then convert them into a list of accounts
    logger.debug("Checking if we need to traverse an Organization")
    if options.ous:
        logger.debug("Getting list of accounts from OUs")
        mapped_list = map(lambda path: organizations.get_accounts_for_ou(logger, options,
                                                                         org_client, path),
                          options.ous)
        options.accounts = utils.flatten_list(mapped_list)
        if options.no_master:
            master = org_client.describe_organization()["Organization"]["MasterAccountId"]
            logger.debug("Removing the master account (%s) from the list of accounts", master)
            options.accounts = filter(lambda x: x["Id"] != master, options.accounts)

    logger.info("Set accounts: %s", options.accounts)


def examine_command(logger, options):
    """ look at the command and guess if it is an AWS CLI built in command """
    if not options.no_cli_guess and options.command:
        try:
            import awscli.clidriver
            logger.debug("Guessing if the supplied command is an AWS CLI command..")
            cli = awscli.clidriver.CLIDriver()
            cli_help = cli.create_help_command()
            aws_cli_commands = map(lambda x: x, cli_help.command_table)

            if options.command[0] in aws_cli_commands:
                options.command.insert(0, "aws")
                logger.debug("Assuming command is an AWS CLI, new command is: %s", options.command)
        except ImportError:
            logger.debug("awscli module not found or failed to load")


def build_work_plan(logger, options, sts_client):
    """ create a big list of commands we need to run... """
    logger.info("Starting analysis on work plan")
    commands_list = []

    # iterate over accounts and regions...
    for account in options.accounts:

        logger.debug("Looking at account: %s", account)
        account_id = account["Id"] if isinstance(account, dict) else account

        # work out if we need to call STS to assume a new role...
        if options.role:

            # call STS to get credentials for the account and role...
            try:
                arn = "arn:aws:iam::{}:role/{}".format(account_id, options.role)
                logger.debug("Calling STS to get temporary credentials for: %s", arn)
                assumed_role = sts_client.assume_role(
                    RoleArn=arn,
                    RoleSessionName="{}@{}".format(os.environ["USER"], os.environ["HOSTNAME"]),
                    ExternalId="{}@{}".format(os.environ["USER"], os.environ["HOSTNAME"])
                )

            except botocore.exceptions.BotoCoreError as be_bce:
                print("error switching role ({}@{}): {}".format(options.role,
                                                                account_id, be_bce.args))
                sys.exit(1)

            except botocore.exceptions.ClientError as be_ce:
                print("error switching role ({}@{}): {}".format(options.role,
                                                                account_id, be_ce.args))
                sys.exit(1)

        for region in options.regions:
            logger.debug("Looking at region: %s", region)
            cmd = {}
            cmd["command"] = options.command
            cmd["environment"] = {}
            cmd["role"] = options.role
            cmd["account_id"] = account_id
            cmd["account"] = account
            cmd["region"] = region
            env = cmd["environment"]

            if region != "<default>":
                env["AWS_DEFAULT_REGION"] = region
            if options.profile:
                session = boto3.session.Session(profile_name=options.profile)
                env["AWS_ACCESS_KEY_ID"] = session.get_credentials().access_key
            if options.role:
                env["AWS_ACCESS_KEY_ID"] = assumed_role["Credentials"]["AccessKeyId"]

            logger.debug("Adding command to work plan: %s", cmd)
            cmd["options"] = options

            # add credentials and sensitive information after we have output debug info...
            if options.profile:
                env["AWS_SECRET_ACCESS_KEY"] = session.get_credentials().secret_key
            if options.role:
                env["AWS_SECRET_ACCESS_KEY"] = assumed_role["Credentials"]["SecretAccessKey"]
                env["AWS_SESSION_TOKEN"] = assumed_role["Credentials"]["SessionToken"]

            commands_list.append(cmd)

    return commands_list


def execute_work_plan(logger, options, commands_list):
    """ run through commands_list and run various commands in the thread pool """
    logger.info("Executing work plan across a thread pool of size: %s", options.threads)
    utils.GLOBALS["main_thread_lock"] = threading.Lock()
    utils.GLOBALS["thread_pool_lock"] = threading.BoundedSemaphore(options.threads)
    utils.GLOBALS["thread_count"] = len(commands_list)
    logger.debug("Locks created, task list size = %s", utils.GLOBALS["thread_count"])

    # obtain the main thread lock...
    logger.debug("Acquiring main thread lock")
    utils.GLOBALS["main_thread_lock"].acquire()

    for cmd in commands_list:
        logger.debug("waiting for next thread to be available")
        utils.GLOBALS["thread_pool_lock"].acquire()
        logger.debug("thread is available, starting thread")
        threading.Thread(target=commands.run_command, args=(logger, options, cmd, )).start()

    # block on the main thread lock being released...
    logger.debug("Blocking main thread, waiting on commands to finish")
    utils.GLOBALS["main_thread_lock"].acquire()
    logger.debug("Main thread lock released, working on output")
