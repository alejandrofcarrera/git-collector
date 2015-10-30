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

__author__ = 'Alejandro F. Carrera'


# function that return structure with differences (users)
def diff_users(user_one, user_two):
    k_users = {
        "username": "string",
        "name": "string",
        "avatar_url": "string",
        "state": "string",
        "web_url": "string",
        "primary_email": "string",
        "id": "int",
        "emails": "array",
        "created_at": "long",
        "current_sign_in_at": "long"
    }
    return diff_structure(k_users, user_one, user_two)


# function that return structure with differences (projects)
def diff_projects(project_one, project_two):
    k_projects = {
        "name": "string",
        "public": "string",
        "owner": "string",
        "http_url_to_repo": "string",
        "default_branch": "string",
        "web_url": "string",
        "state": "string",
        "id": "int",
        "last_activity_at": "long",
        "created_at": "long",
        "tags": "array"
    }
    return diff_structure(k_projects, project_one, project_two)


# function that return structure with differences (group)
def diff_groups(group_one, group_two):
    k_groups = {
        "name": "string",
        "path": "string",
        "web_url": "string",
        "id": "int",
        "members": "array"
    }
    return diff_structure(k_groups, group_one, group_two)


# function that return structure with differences
def diff_structure(st_keys, st_one, st_two):
    st_new = {}
    for i in st_one.keys():
        if st_keys[i] == "string" and str(st_one[i]) != str(st_two[i]):
            st_new[i] = st_one[i]
        elif st_keys[i] == "int" and int(st_one[i]) != int(st_two[i]):
            st_new[i] = st_one[i]
        elif st_keys[i] == "long" and long(st_one[i]) != long(st_two[i]):
            st_new[i] = st_one[i]
        elif st_keys[i] == "array":
            a_st_one = eval(st_one[i])
            b_st_one = eval(st_two[i])
            em_news = list(set(a_st_one).difference(set(b_st_one)))
            em_deleted = list(set(b_st_one).difference(set(a_st_one)))
            if len(em_news) > 0 or len(em_deleted) > 0:
                st_new[i] = a_st_one
        else:
            pass
    if len(st_new.keys()) > 0:
        return st_new
    else:
        return None
