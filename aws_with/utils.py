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

import itertools
import logging

GLOBALS = {}

def flatten_list(the_list):
    """ take a list of lists and flatten it to just a list """
    return [] if the_list is None else list(itertools.chain.from_iterable(the_list))


def split_list(the_list, splitter):
    """ take a list and split each item and put the split items back into the main list"""
    return [] if the_list is None else flatten_list(map(lambda x: x.split(splitter), the_list))


def generic_paginator(logger, paged_function, result_object, **kwargs):
    """ call an API until there are no more results """
    logger.debug("in generic_paginator, for: %s", paged_function)
    for key, value in kwargs.items():
        logger.debug("                   params: %s=%s", key, value)
    full_results = []
    next_token = ""
    while next_token is not None:
        if next_token != "":
            kwargs.update({"NextToken":next_token})
        result = paged_function(**kwargs)
        full_results.extend(result[result_object])
        next_token = result.get("NextToken", None)
        logger.debug("               next_token: %s", next_token)
    return full_results


def setup_logging(options):
    """ set up logging... """
    logger = logging.getLogger("aws_with")
    logger.setLevel(logging.ERROR)
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s(%(threadName)s): %(message)s')
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    if options.verbosity is None:
        options.verbosity = 0
    if options.verbosity >= 1:
        logger.setLevel(logging.INFO)
    if options.verbosity >= 2:
        logger.setLevel(logging.DEBUG)
    logger.debug("Logger set up")
    return logger
