"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  This file is part of the Smart Developer Hub Project:
    http://www.smartdeveloperhub.org
  Center for Open Middleware
        http://www.centeropenmiddleware.com/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2015 Center for Open Middleware.
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

# Collector Package Configuration
NAME = "gl-collector"
VERSION = "1.0.0"
DEBUGGER = True
LONGNAME = "Gitlab Collector"
DELAY = os.environ.get("COLL_DELAY", 60 * 60 * 3)

# Collector Hook Configuration to get changes from Gitlab
COLLECTOR_WEBHOOK_IP = os.environ.get("COLL_WEBHOOK_IP", "10.0.2.2")

# Collector Configuration to create Flask API
COLLECTOR_LISTEN_PROT = os.environ.get("COLL_LISTEN_PROT", "http")
COLLECTOR_LISTEN_PORT = int(os.environ.get("COLL_LISTEN_PORT", 5000))
COLLECTOR_LISTEN_IP = os.environ.get("COLL_LISTEN_IP", "0.0.0.0")

# Collector Configuration Folder
COLLECTOR_GIT_FOLDER = "/tmp/gl-collector/"

# Gitlab Configuration to get data
GITLAB_PROT = os.environ.get("COLL_GITLAB_PROT", "http")
GITLAB_IP = os.environ.get("COLL_GITLAB_IP", "127.0.0.1")
GITLAB_PORT = int(os.environ.get("COLL_GITLAB_PORT", 8000))
GITLAB_USER = os.environ.get("COLL_GITLAB_USER", "root")
GITLAB_PASS = os.environ.get("COLL_GITLAB_PASS", "12345678")
GITLAB_VER_SSL = bool(os.environ.get("COLL_GITLAB_VERIFY_SSL", False))

# Redis Configuration to set data
REDIS_IP = os.environ.get("COLL_REDIS_IP", "127.0.0.1")
REDIS_PORT = int(os.environ.get("COLL_REDIS_PORT", 6379))
REDIS_PASS = os.environ.get("COLL_REDIS_PASS", None)

# Redis Configuration (Main Entities)
REDIS_DB_PR = int(os.environ.get("COLL_REDIS_DB_PROJECT", 0))
REDIS_DB_BR = int(os.environ.get("COLL_REDIS_DB_BRANCH", 1))
REDIS_DB_CO = int(os.environ.get("COLL_REDIS_DB_COMMIT", 2))
REDIS_DB_US = int(os.environ.get("COLL_REDIS_DB_USER", 3))

# Redis Configuration (Relations)
REDIS_DB_BR_CO = int(os.environ.get("COLL_REDIS_DB_BRANCH_COMMIT", 4))
REDIS_DB_US_CO = int(os.environ.get("COLL_REDIS_DB_COMMITTER_COMMIT", 5))

# Fields about User
# http://doc.gitlab.com/ce/api/users.html#for-admin
GITLAB_USER_FIELDS = [
    "username", "name", "twitter", "created_at", "bio",
    "linkedin", "email", "state", "avatar_url",
    "skype", "id", "website_url", "first_commit_at",
    "emails", "last_commit_at", "current_sign_in_at",
    "web_url", "website_url"
]

# Fields about Group
# http://doc.gitlab.com/ce/api/groups.html#list-project-groups
GITLAB_GROUP_FIELDS = [
    "id", "name", "path", "description", "avatar_url", "web_url"
]

# Fields about Repository
# http://doc.gitlab.com/ce/api/projects.html#get-single-project
GITLAB_REPO_FIELDS = [
    "first_commit_at", "contributors", "http_url_to_repo", "web_url",
    "owner", "id", "archived", "public", "description", "default_branch",
    "last_commit_at", "last_activity_at", "name", "created_at", "avatar_url",
    "tags", "namespace"
]

# Fields about Branch
# http://doc.gitlab.com/ce/api/projects.html#list-single-branch
GITLAB_BRANCH_FIELDS = [
    "name", "protected"
]


def print_message(msg):
    if DEBUGGER:
        logging.warn("[DEBUG] %s" % msg)
    else:
        logging.info("[INFO] %s" % msg)


def print_error(msg):
    if DEBUGGER:
        logging.warn("[ERROR] %s" % msg)
    else:
        logging.info("[ERROR] %s" % msg)