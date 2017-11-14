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
import json
import yaml
import boto3
import botocore

from . import cli, utils, workplan, commands, output


def main():
    """ main function """

    # create a dict of globals which are accessed by different threads
    utils.GLOBALS["stop_because_of_error"] = False
    utils.GLOBALS["thread_count"] = 0

    # process command line arguments...
    options = cli.check_args()

    # setup logging
    logger = utils.setup_logging(options)
    logger.debug("Got optoins: %s", options)

    # if a profile option was specified then set it up...
    if options.profile:
        try:
            logger.info("loading aws configuration profile: %s", options.profile)
            boto3.setup_default_session(profile_name=options.profile)
        except botocore.exceptions.BotoCoreError as bce:
            print("error: " + format(bce))
            sys.exit(1)

    # create boto3 clients...
    logger.debug("Creating AWS clients")
    try:
        org = boto3.client("organizations")
        sts = boto3.client("sts")
    except botocore.exceptions.BotoCoreError as bce:
        print("error: " + format(bce))
        sys.exit(1)

    # main program logic...
    workplan.examine_regions(logger, options)
    workplan.examine_accounts(logger, options, org)
    workplan.examine_command(logger, options)
    commands_list = workplan.build_work_plan(logger, options, sts)

    # make sure we have at least one command to run...
    if not commands_list:
        print("warning: no matching accounts/regions - nothing to do...")
        sys.exit(1)

    # don't bother using a thread pool if there is only one command...
    if not options.command:
        logger.debug("Calling run_command_unsafe() without threadpool as shell command")
        commands.run_command_unsafe(logger, options, commands_list[0])
        sys.exit(0)

    workplan.execute_work_plan(logger, options, commands_list)
    outputs = output.gather_command_outputs(logger, options, commands_list)


    logger.info("Nearly done, collating thread outputs")
    if options.format == "json":
        print(json.dumps(outputs, indent=4, sort_keys=True))
    elif options.format == "yaml":
        print(yaml.safe_dump(outputs, default_flow_style=False,
                             encoding="utf-8", allow_unicode=True, indent=4))
    else:
        for out in outputs:
            header = "{}@{} in {}:".format(out["role"], out["account"], out["region"])
            print("-" * len(header))
            print(header)
            print("-" * len(header))
            print("")
            print(out["output"])
            print("")
            print("")

if __name__ == '__main__':
    main()
