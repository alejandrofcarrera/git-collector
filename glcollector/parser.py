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
import json

__author__ = 'Alejandro F. Carrera'

str_time_keys = [
    'created_at', 'updated_at', 'last_activity_at',
    'due_date', 'authored_date', 'committed_date',
    'first_commit_at', 'last_commit_at', 'current_sign_in_at'
]


def join_users(user_one, user_two):
    k_users = {
        "username": "string",
        "name": "string",
        "avatar_url": "string",
        "state": "string",
        "id": "int",
        "emails": "array",
        "created_at": "long"
    }
    new_user = {}
    for i in user_one.keys():
        if k_users[i] == "string" and str(user_one[i]) != str(user_two[i]):
            new_user[i] = user_one[i]
            if i == "state" and str(user_one[i]) == "blocked":
                new_user["gitlab_status"] = "blocked"
        elif k_users[i] == "int" and int(user_one[i]) != int(user_two[i]):
            new_user[i] = user_one[i]
        elif k_users[i] == "long" and long(user_one[i]) != long(user_two[i]):
            new_user[i] = user_one[i]
        elif k_users[i] == "array":
            a_user_one = json.loads(user_one[i])
            b_user_one = json.loads(user_two[i])
            em_news = list(set(a_user_one).difference(set(b_user_one)))
            if len(em_news) > 0:
                new_user[i] = a_user_one
        else:
            pass
    if len(new_user.keys()) > 0:
        return new_user
    else:
        return None


def get_info_commit(pr_name, commit):
    cur_dir = os.getcwd()
    os.chdir(config.COLLECTOR_GIT_FOLDER + pr_name)
    __info_std = "git log --pretty=oneline --shortstat -1 " + commit.get("id")
    __info_std = commands.getoutput(__info_std)
    __p = re.search(r"\d+ file", __info_std)
    if __p is None:
        commit["files_changed"] = 0
        commit["lines_added"] = 0
        commit["lines_removed"] = 0
    else:
        __p = __p.start()
        __info_std = __info_std[__p:]
        __info_std = __info_std.split(", ")
        if "files" not in __info_std[0]:
            commit["files_changed"] = int(__info_std[0].replace(" file changed", ""))
        else:
            commit["files_changed"] = int(__info_std[0].replace(" files changed", ""))
        if len(__info_std) > 1:
            if "insertion" in __info_std[1]:
                if "insertions" not in __info_std[1]:
                    commit["lines_added"] = int(__info_std[1].replace(" insertion(+)", ""))
                else:
                    commit["lines_added"] = int(__info_std[1].replace(" insertions(+)", ""))
            else:
                commit["lines_added"] = 0
                if "deletions" not in __info_std[1]:
                    commit["lines_removed"] = int(__info_std[1].replace(" deletion(-)", ""))
                else:
                    commit["lines_removed"] = int(__info_std[1].replace(" deletions(-)", ""))
        if len(__info_std) > 2:
            if "deletions" not in __info_std[2]:
                commit["lines_removed"] = int(__info_std[2].replace(" deletion(-)", ""))
            else:
                commit["lines_removed"] = int(__info_std[2].replace(" deletions(-)", ""))
        else:
            commit["lines_removed"] = 0
        os.chdir(cur_dir)


def clean_info_commit(o):
    for k in o.keys():
        if o[k] is None or o[k] == '' or o[k] == "null":
            del o[k]
        elif k in str_time_keys:
            o[k] = long(parser.parse(o.get(k)).strftime("%s")) * 1000
        else:
            pass


def clean_info_user(o):
    for k in o.keys():
        if k not in config.GITLAB_USER_FIELDS:
            del o[k]
        elif k == "email":
            o["primary_email"] = o.get(k)
            del o[k]
        elif o[k] is None or o[k] == '' or o[k] == "null":
            del o[k]
        elif k in str_time_keys:
            o[k] = long(parser.parse(o.get(k)).strftime("%s")) * 1000
        else:
            pass


def clean_info_group(o):
    for k in o.keys():
        if k not in config.GITLAB_GROUP_FIELDS:
            del o[k]
        elif o[k] is None or o[k] == '' or o[k] == "null":
            del o[k]
        else:
            pass


def clean_info_project(o):
    for k in o.keys():
        if k not in config.GITLAB_REPO_FIELDS:
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
    for k in o.keys():
        if k not in config.GITLAB_BRANCH_FIELDS:
            del o[k]
        elif k == "name":
            o["id"] = base64.b16encode(o.get(k))
        elif o[k] is False:
            o[k] = 'false'
        elif o[k] is True:
            o[k] = 'true'
        else:
            pass
