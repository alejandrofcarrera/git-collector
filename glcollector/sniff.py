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

import json

__author__ = 'Alejandro F. Carrera'


def get_keys_from_redis(self, key_str):
    if key_str == "projects":
        __mt = self.rd_instance_pr.keys(key_str + ":*:commits:")
    else:
        __mt = self.rd_instance_us.keys(key_str + ":*:")
    return map(lambda x: int(x.split(":")[1]), __mt)


def get_values_from_redis(self, key_str):
    dict_keys = get_keys_from_redis(self, key_str)
    if key_str == "projects":
        __mt = map(lambda x: self.rd_instance_pr.hgetall(
            "projects:" + str(x) + ":"
        ), dict_keys)
    elif key_str == "users":
        __mt = map(lambda x: self.rd_instance_us.hgetall(
            "users:" + str(x) + ":"
        ), dict_keys)
    else:
        __mt = map(lambda x: self.rd_instance_us.hgetall(
            "groups:" + str(x) + ":"
        ), dict_keys)
    return dict(zip(dict_keys, __mt))


def get_keys_and_values_from_gitlab(self, key_str):
    if key_str == "projects":
        __mt = self.gl_instance.get_projects()
    elif key_str == "users":
        __mt = self.gl_instance.get_users()
        for i in __mt:
            i['emails'] = [i.get('email')]
            del i['email']
            __em_lst = self.gl_instance.get_users_emails_byUid(uid=i.get('id'))
            for j in __em_lst:
                i['emails'].append(j.get('email'))
            i['emails'] = json.dumps(i['emails'])

    elif key_str == "groups":
        __mt = self.gl_instance.get_groups()
    __mt_id = map(lambda x: int(x.get('id')), __mt)
    return dict(zip(__mt_id, __mt))