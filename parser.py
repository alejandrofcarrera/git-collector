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

import settings as config
from dateutil import parser
import commands, os, base64, re

__author__ = 'Alejandro F. Carrera'

str_time_keys = [
    'created_at', 'updated_at', 'last_activity_at',
    'due_date', 'authored_date', 'committed_date',
    'first_commit_at', 'last_commit_at'
]


def clean_info_commit(o):
    for k in o.keys():
        if o[k] is None or o[k] == '' or o[k] == "null":
            del o[k]
        elif k in str_time_keys:
            o[k] = long(parser.parse(o.get(k)).strftime("%s")) * 1000
        else:
            pass


def get_info_commit(pr_name, id_commit, msg_commit):
    cur_dir = os.getcwd()
    os.chdir(config.COLLECTOR_GIT_FOLDER + pr_name)
    __info_std = "git log --pretty=oneline --shortstat -1 " + id_commit
    __info_std = commands.getoutput(__info_std)
    __p = re.search(r"\d+ file", __info_std)
    if __p is None:
        return {
            "files_changed": 0,
            "lines_added": 0,
            "lines_removed": 0
        }
    else:
        __p = __p.start()
    __info_std = __info_std[__p:]
    __info_std = __info_std.split(", ")
    if "files" not in __info_std[0]:
        __info_res = {"files_changed": int(__info_std[0].replace(" file changed", ""))}
    else:
        __info_res = {"files_changed": int(__info_std[0].replace(" files changed", ""))}
    if len(__info_std) > 1:
        if "insertion" in __info_std[1]:
            if "insertions" not in __info_std[1]:
                __info_res["lines_added"] = int(__info_std[1].replace(" insertion(+)", ""))
            else:
                __info_res["lines_added"] = int(__info_std[1].replace(" insertions(+)", ""))
        else:
            __info_res["lines_added"] = 0
            if "deletions" not in __info_std[1]:
                __info_res["lines_removed"] = int(__info_std[1].replace(" deletion(-)", ""))
            else:
                __info_res["lines_removed"] = int(__info_std[1].replace(" deletions(-)", ""))
    if len(__info_std) > 2:
        if "deletions" not in __info_std[2]:
            __info_res["lines_removed"] = int(__info_std[2].replace(" deletion(-)", ""))
        else:
            __info_res["lines_removed"] = int(__info_std[2].replace(" deletions(-)", ""))
    else:
        __info_res["lines_removed"] = 0
    os.chdir(cur_dir)
    return __info_res


def clean_info_user(o):
    k_users = [
        "username", "name", "twitter", "created_at",
        "linkedin", "email", "state", "avatar_url",
        "skype", "id", "website_url", "first_commit_at",
        "emails", "last_commit_at"
    ]
    for k in o.keys():
        if k not in k_users:
            del o[k]
        elif o[k] is None or o[k] == '' or o[k] == "null":
            del o[k]
        elif k in str_time_keys:
            o[k] = long(parser.parse(o.get(k)).strftime("%s")) * 1000
        else:
            pass


def clean_info_group(o):
    k_groups = [
        "name", "path", "description", "avatar_url", "web_url"
    ]
    for k in o.keys():
        if k not in k_groups:
            del o[k]
        elif o[k] is None or o[k] == '' or o[k] == "null":
            del o[k]
        else:
            pass


def clean_info_project(o):
    k_projects = [
        "first_commit_at", "contributors", "http_url_to_repo", "web_url",
        "owner", "id", "archived", "public", "description", "default_branch",
        "last_commit_at", "last_activity_at", "name", "created_at", "avatar_url",
        "tags"
    ]
    for k in o.keys():
        if k not in k_projects:
            del o[k]
        elif o[k] is None or o[k] == '' or o[k] == "null":
            del o[k]
        elif k in str_time_keys:
            o[k] = long(parser.parse(o.get(k)).strftime("%s")) * 1000
        elif o[k] is False:
            o[k] = 'false'
        elif o[k] is True:
            o[k] = 'true'
        else:
            pass


def clean_info_branch(o):
    k_branches = [
        "name", "protected"
    ]
    for k in o.keys():
        if k not in k_branches:
            del o[k]
        elif k == "name":
            o["id"] = base64.b16encode(o.get(k))
        elif o[k] is False:
            o[k] = 'false'
        elif o[k] is True:
            o[k] = 'true'
        else:
            pass
