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
import argparse
from . import utils


def create_args_parser():
    """ process command line arguments and perform sanity checks """
    parser = argparse.ArgumentParser(description="Run the same command across a number of "
                                                 "AWS accounts and/or regions.",
                                     usage="%(prog)s [options] [COMMAND]",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
NOTE:  -R, -o and -a can take a comma-separated list or the option may be given multiple times.

EXAMPLES:

    aws_with --role=admins-role
    Assume the IAM role 'admins-role' within the current AWS account and then run a shell.

    aws_with --role=admins-role --accounts=123456789012
    Assume the IAM role 'admins-role' in the account 123456789012 and then run a shell.

    aws_with --regions='us-*' ec2 describe-instances
    List all EC2 instances across all US regions.

    aws_with --ous=/Technology/Development s3 ls
    List all S3 buckets owned by any account under the Organizations OU 'Development'.
    The 'Development' OU is itself under the 'Technology' OU off the Root OU.

    aws_with -o /Production,/Staging/Final -R '*' \\
        cloudformation update-stack --stack-name 'security-checks' ...
    Update a stack across all accounts under the 'Production' Organizations OU
    or under the /Staging/Final OU and across all regions.
""")

    parser.add_argument("-V", "--version",
                        dest="show_version", action="store_true",
                        help="Show the version number and exit")

    parser.add_argument("-R", "--regions",
                        dest="regions", action="append",
                        help="Run the command for all regions that match PATTERNS")

    parser.add_argument("-r", "--role",
                        dest="role", action="store",
                        help="Use STS assumeRole to take on a different IAM role. If not "
                             "specified then ROLE defaults to OrganizationAccountAccessRole")

    parser.add_argument("-o", "--ous",
                        dest="ous", action="append",
                        help="Run the command for all child accounts under "
                             "the Organizations OU PATHS")

    parser.add_argument("-a", "--accounts",
                        dest="accounts", action="append",
                        help="Run the command for all the listed ACCOUNTS")

    parser.add_argument("-x", "--no-recursive",
                        dest="no_recursive", action="store_true",
                        help="When scanning Organizations for accounts, don't look recursively")

    parser.add_argument("-t", "--threads",
                        dest="threads", action="store", default=2, type=int,
                        help="Set the number of threads to use when running commands (default: 2)")

    parser.add_argument("-f", "--output",
                        dest="format", action="store", default="json",
                        type=str, choices=["json", "yaml", "text"],
                        help="Set the output format to use")

    parser.add_argument("-q", "--quiet",
                        dest="quiet", action="store_true",
                        help="Suppress output if a command is successful but has no output")

    parser.add_argument("-e", "--stop-on-error",
                        dest="stop_on_error", action="store_true",
                        help="Stop running commands if one throws an error")

    parser.add_argument("-v", "--verbose",
                        dest="verbosity", action="count",
                        help="Output debug messages, increase messages with -v -v")

    parser.add_argument("-g", "--no-cli-guess",
                        dest="no_cli_guess", action="store_true",
                        help="Do not attempt to guess if the command is an AWS CLI command")

    parser.add_argument("-m", "--no-master",
                        dest="no_master", action="store_true",
                        help="Do not include the Organizations master account in searches")

    parser.add_argument("-p", "--profile",
                        dest="profile", action="store",
                        help="Use the saved AWS credentials/profile called PROFILE")

    parser.add_argument("command", nargs=argparse.REMAINDER, metavar="COMMAND",
                        help="This is the command that should be run across regions/accounts/OUs."
                             "  COMMAND is mandatory when the -R or -o options are used, "
                             "otherwise it is optional and a shell will be run if it is omitted.")

    return parser

def show_version():
    """ display version information and then exit """
    print("aws_with version: {}".format(sys.modules["aws_with"].VERSION))
    sys.exit(0)

def error(message):
    """ display an error related to command line arguments and quit """
    print(message + "\nhint: try -h for help")
    sys.exit(1)

def args_basic_checks(parsed_options):
    """ perform basic sanity checks on the command line arguments """
    if parsed_options.show_version:
        show_version()

    if len(sys.argv) == 2 and parsed_options.verbosity > 0:
        show_version()

    if parsed_options.threads < 1:
        parsed_options.threads = 1

    check_none = [parsed_options.role, parsed_options.regions,
                  parsed_options.ous, parsed_options.accounts]

    if check_none == [None]*len(check_none):
        error("error: you must specify at least one of -r, -R, -o or -a")

    if parsed_options.accounts and parsed_options.ous:
        error("error: you cannot specify both -a and -o")

    if parsed_options.regions and parsed_options.command == 0:
        error("error: if you specify -R or -o then you must supply a command to run")

    if parsed_options.ous and parsed_options.command == 0:
        error("error: if you specify -R or -o then you must supply a command to run")

    if parsed_options.accounts and len(parsed_options.accounts) > 1 and parsed_options.command:
        error("error: if you specify multiple accounts with -a then "
              "you must supply a command to run")

def check_args():
    """ process command line arguments """
    parser = create_args_parser()
    parsed_options = parser.parse_args()
    args_basic_checks(parsed_options)

    # if -a or -o are specified the -r has a default value so set it...
    if parsed_options.accounts is not None or parsed_options.ous is not None:
        if parsed_options.role is None:
            parsed_options.role = "OrganizationAccountAccessRole"

    # expand out parsed_options that can take a list of values...
    parsed_options.ous = sorted(set(utils.split_list(parsed_options.ous, ",")))
    parsed_options.accounts = sorted(set(utils.split_list(parsed_options.accounts, ",")))
    parsed_options.regions = sorted(set(utils.split_list(parsed_options.regions, ",")))
    return parsed_options
