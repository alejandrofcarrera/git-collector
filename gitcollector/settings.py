"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  This file is part of the Smart Developer Hub Project:
    http://www.smartdeveloperhub.org
  Center for Open Middleware
        http://www.centeropenmiddleware.com/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2016 Center for Open Middleware.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
            http://www.apache.org/licenses/LICENSE-2.0
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
"""

import os
import logging

__author__ = 'Alejandro F. Carrera'


def gen_password():
    chars = '!$%&/()=?^_-.:,;ABCDEFGHJKLMNPQRSTUVWXYZ' + \
            'abcdefghjklmnpqrstuvwxyz0123456789'
    return ''.join(
        [chars[ord(c) % len(chars)] for c in os.urandom(12)]
    )

# Collector Configuration
GC_NAME = "git-collector"
GC_VERSION = "1.0.0"
GC_LONGNAME = "Git Collector"
GC_DELAY = int(os.environ.get("GC_DELAY", 60 * 60 * 3))
GC_IP = os.environ.get("GC_LISTEN_IP", "0.0.0.0")
GC_HOST = os.environ.get("GC_HOST", "127.0.0.1")
GC_PORT = int(os.environ.get("GC_LISTEN_PORT", 5000))

# Collector Temporal Configuration
GC_FOLDER = "/tmp/git-collector"

# Collector Database Configuration
GC_DB_IP = os.environ.get("GC_RED_IP", "127.0.0.1")
GC_DB_PORT = int(os.environ.get("GC_RED_PORT", 6379))
GC_DB_PASS = os.environ.get("GC_RED_PASS", None)

# Collector - Redis Database
GC_DB_REPOSITORIES = int(os.environ.get("GC_REPOSITORIES", 0))
GC_DB_REPOSITORIES_URL = int(os.environ.get("GC_REPOSITORIES_URL", 1))
GC_DB_BRANCHES = int(os.environ.get("GC_BRANCH", 2))
GC_DB_COMMITS = int(os.environ.get("GC_COMMIT", 3))
GC_DB_BRANCH_COMMIT = int(os.environ.get("GC_BRANCH_COMMIT", 4))
GC_DB_COMMITTER_COMMIT = int(os.environ.get("GC_COMMITTER_COMMIT", 5))

# Collector - AMQP
GC_AMQP_BROKER_HOST = os.environ.get("GC_MQ_IP", "127.0.0.1")
GC_AMQP_BROKER_PORT = int(os.environ.get("GC_MQ_PORT", 5672))
GC_AMQP_VIRTUAL_HOST = os.environ.get("GC_MQ_VHOST", "/")
GC_AMQP_EXCNAME = os.environ.get("GC_MQ_EXCNAME", "gitcollector")

# Collector Password Auto-generated
GC_USE_PASSWORD = int(os.environ.get("GC_PASSWORD", 0))
GC_PASSWORD = gen_password() if GC_USE_PASSWORD else None

logging.basicConfig(
    filename="/var/log/" + GC_NAME + ".log",
    filemode='a',
    format='%(asctime)s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG
)


def print_message(msg):
    logging.info("%s" % msg)


def print_error(msg):
    logging.error("%s" % msg)
