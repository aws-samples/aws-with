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


def gather_command_outputs(logger, options, commands_list):
    """ gather the command outputs together """
    outputs = []
    for cmd in commands_list:

        # check if we have an output object that shouldn't be suppressed from --quiet...
        if "output" in cmd.keys():
            command_output = cmd["output"]["output"]
            oo_single_key = False
            oo_single_empty_key = False
            if isinstance(command_output, dict):
                oo_key_count = len(command_output.keys())
                oo_single_key = oo_key_count == 1
                if oo_single_key:
                    oo_key_values = len(command_output[command_output.keys()[0]])
                    oo_single_empty_key = oo_key_values == 0

            # check for literally no output...
            if options.quiet and (command_output is None or command_output == ""):
                logger.debug("Command output is actually empty, skipping: %s", cmd["output"])

            # check if output contains a single empty object...
            elif options.quiet and oo_single_empty_key:
                logger.debug("Command output is effectively empty, skipping: %s", cmd["output"])

            else:
                outputs.append(cmd["output"])
    return outputs
