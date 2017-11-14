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

import re
import boto3
from . import utils


def get_regions_list(logger):
    """ get a list of AWS regions """
    logger.debug("getting a list of AWS regions...")
    ec2 = boto3.client("ec2", region_name="us-east-1")
    return utils.generic_paginator(logger, ec2.describe_regions, "Regions")

def get_regions_from_regex(logger, regex, region_list):
    """ search the regions list using regular expressions """
    logger.debug("getting regions that match: %s", regex)
    regex_pattern = re.compile("^" + regex.replace("*", ".*") + "$")
    filtered_regions = filter(lambda x: regex_pattern.match(x["RegionName"]), region_list)
    return map(lambda x: x["RegionName"], filtered_regions)
