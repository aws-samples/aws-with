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

from . import utils


def get_child_ous(logger, org_client, org_unit):
    """ given an OU, find all the OUs within that OU... """
    logger.debug("Getting OUs for: %s", org_unit)
    result = [org_unit]

    # for this OU, get all the children...
    args = dict(ParentId=org_unit["Id"])
    children = utils.generic_paginator(logger, org_client.list_organizational_units_for_parent,
                                       "OrganizationalUnits", **args)

    # update child paths and then call ourselves recursively to find all children
    for child in children:
        child["Path"] = "{}/{}".format(org_unit["Path"], child["Name"]).replace("//", "/")
        result.extend(get_child_ous(logger, org_client, child))

    return result


def get_ou_from_path(logger, org_client, path):
    """ given a path, traverse Organizations OUs to locate the required OU... """
    logger.debug("Getting OU from path: %s", path)

    current_ou = org_client.list_roots()["Roots"][0]["Id"]
    if path == "/":
        return {"Id":current_ou, "Path":path}

    for dir_name in path.split("/")[1:]:
        logger.debug("Getting OU from path: %s, looking for: %s", path, dir_name)
        found = False
        args = dict(ParentId=current_ou)
        children = utils.generic_paginator(logger, org_client.list_organizational_units_for_parent,
                                           "OrganizationalUnits", **args)

        for org_unit in children:
            if org_unit["Name"] == dir_name:
                current_ou = org_unit["Id"]
                found = True
                break

        if not found:
            raise ValueError("OU path not found")

    return {"Id":current_ou, "Path":path}


def get_accounts_for_ou(logger, options, org_client, path):
    """ given a path, get all the AWS accounts within that part of an Organization... """
    logger.debug("Getting accounts for OU: %s", path)
    org_unit = get_ou_from_path(logger, org_client, path)
    ous = []
    if options.no_recursive:
        ous.append(org_unit)
    else:
        ous.extend(get_child_ous(logger, org_client, org_unit))

    result = []
    for org_unit in ous:
        args = {"ParentId":org_unit["Id"]}
        accounts = utils.generic_paginator(logger, org_client.list_accounts_for_parent,
                                           "Accounts", **args)
        for acc in accounts:
            acc["Path"] = org_unit["Path"]
        result.extend(accounts)
    return result
