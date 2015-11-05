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
import st_clean

__author__ = 'Alejandro F. Carrera'


def get_keys_from_redis(self, key_str):
    __str = key_str[0] + "_"
    if key_str == "projects":
        __mt = self.rd_instance_pr.keys(__str + "*")
        __mt_result = []
        for i in __mt:
            if not self.rd_instance_pr.hgetall(i).get("state") == "deleted":
                __mt_result.append(i)
    else:
        __mt = self.rd_instance_us.keys(__str + "*")
        __mt_result = []
        for i in __mt:
            if not self.rd_instance_us.hgetall(i).get("state") == "deleted":
                __mt_result.append(i)
    return map(lambda x: int(x.replace(__str, "")), __mt_result)


def get_values_from_redis(self, key_str):
    __dc_keys = get_keys_from_redis(self, key_str)
    dict_keys = map(lambda x: key_str[0] + "_" + str(x), __dc_keys)
    if key_str == "projects":
        __mt = map(lambda x: self.rd_instance_pr.hgetall(str(x)), dict_keys)
    else:
        __mt = map(lambda x: self.rd_instance_us.hgetall(str(x)), dict_keys)
    return dict(zip(dict_keys, __mt))


def get_keys_and_values_from_gitlab(self, key_str):
    if key_str == "projects":
        __mt = self.gl_instance.get_projects()
        for i in __mt:
            st_clean.project(i)
    elif key_str == "users":
        __mt = self.gl_instance.get_users()
        for i in __mt:
            i['emails'] = [i.get('email')]
            __em_lst = self.gl_instance.get_users_emails_byUid(uid=i.get('id'))
            for j in __em_lst:
                i['emails'].append(j.get('email'))
            i['emails'] = json.dumps(i['emails'])
            st_clean.user(i)
    elif key_str == "groups":
        __mt = self.gl_instance.get_groups()
        for i in __mt:
            st_clean.group(i)
            i["members"] = []
            [i["members"].append(x.get("id")) for x in
             self.gl_instance.get_groups_members_byId(id=i.get("id"))]
    __mt_id = map(lambda w: int(w.get('id')), __mt)
    return dict(zip(__mt_id, __mt))
