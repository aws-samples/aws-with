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

import os
import subprocess
import json
import copy
from . import utils, monkey


monkey.apply_patches()


def run_command(logger, options, command_list):
    """ safe version for run_command_unsafe that takes care of locks """
    try:
        logger.debug("calling run_command_unsafe...")
        run_command_unsafe(logger, options, command_list)
    finally:
        utils.GLOBALS["thread_count"] = utils.GLOBALS["thread_count"] - 1
        logger.debug("commands still remaining: %s", utils.GLOBALS["thread_count"])
        if utils.GLOBALS["thread_count"] == 0:
            utils.GLOBALS["main_thread_lock"].release()
        logger.debug("thread is finished, releasing lock")
        utils.GLOBALS["thread_pool_lock"].release()


def run_command_unsafe(logger, options, command_list):
    """ run a command """

    if utils.GLOBALS["stop_because_of_error"]:
        return

    env = copy.deepcopy(os.environ)
    env.update(command_list["environment"])
    output = {}

    # check if this is a single command to run a SHELL...
    if not command_list["command"]:
        logger.debug("launching shell: %s", os.environ["SHELL"])
        command_list["command"] = os.environ["SHELL"]
        prompt = "[\\u({}:{})@\\h \\W]\\$ "
        env["PS1"] = prompt.format(command_list["account"], command_list["role"])
        subprocess.call(command_list["command"], env=env)
        return

    # copy some details from the command request to the command output...
    if isinstance(command_list["account"], dict):
        output["account"] = command_list["account"]["Id"]
        output["path"] = command_list["account"]["Path"]
    else:
        output["account"] = command_list["account"]

    output["role"] = command_list["role"]
    output["region"] = command_list["region"]
    output["command"] = " ".join(command_list["command"])

    # run the command and capture the output...
    try:
        output["output"] = subprocess.check_output(command_list["command"],
                                                   env=env, stderr=subprocess.STDOUT,
                                                   shell=False, universal_newlines=True)
        # try and parse the command output as JSON...
        try:
            output["output"] = json.loads(output["output"])
        except (ValueError, SyntaxError):
            pass

        command_list["output"] = output

    except subprocess.CalledProcessError as cpe:
        logger.info("Command returned non-zero exit code")
        output["error"] = {}
        output["error"]["message"] = format(cpe)
        output["output"] = cpe.output
        output["error"]["returncode"] = cpe.returncode
        command_list["output"] = output
        if options.stop_on_error:
            utils.GLOBALS["stop_because_of_error"] = True

    except OSError as ose:
        logger.info("Command failed to start")
        output["output"] = ""
        output["error"] = {}
        output["error"]["message"] = format(ose)
        command_list["output"] = output
        if options.stop_on_error:
            utils.GLOBALS["stop_because_of_error"] = True
