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
import parser
import redis
import base64
import json

from glapi import GlAPI

__author__ = 'Alejandro F. Carrera'


# Redis Help Functions
def redis_create_pool(db):
    __redis_db = redis.ConnectionPool(
        host=config.REDIS_IP,
        port=config.REDIS_PORT,
        db=db,
        password=config.REDIS_PASS
    )
    __redis_db = redis.Redis(connection_pool=__redis_db)
    try:
        __redis_db.client_list()
        return __redis_db
    except Exception as e:
        raise EnvironmentError("- Configuration is not valid or Redis is not online")


class Collector(object):

    """GitLab Collector Class

    Attributes:
        gl_instance (GitLab): GitLab object
        rd_instance (Redis): Redis object
    """

    def __init__(self):
        self.gl_instance = None
        self.rd_instance_pr = None
        self.rd_instance_us = None
        self.rd_instance_br = None
        self.rd_instance_co = None
        try:
            self.gl_connect()
            self.rd_connect()
        except EnvironmentError as e:
            raise e

    # Connection Functions

    def gl_connect(self):
        __host = "%s://%s:%d" % (config.GITLAB_PROT, config.GITLAB_IP, config.GITLAB_PORT)
        __gl = GlAPI(__host, ssl=config.GITLAB_VER_SSL)
        try:
            __gl.login(login=config.GITLAB_USER, password=config.GITLAB_PASS)
            self.gl_instance = __gl
        except Exception as e:
            raise EnvironmentError("- Configuration is not valid or Gitlab is not online")

    def rd_connect(self):
        try:
            self.rd_instance_pr = redis_create_pool(config.REDIS_DB_PR)
            self.rd_instance_us = redis_create_pool(config.REDIS_DB_US)
            self.rd_instance_br = redis_create_pool(config.REDIS_DB_BR)
            self.rd_instance_co = redis_create_pool(config.REDIS_DB_CO)
        except EnvironmentError as e:
            raise e

    # Get Functions

    def get_keys_and_values_from_redis(self, key_str):
        if key_str == "projects":
            __mt = self.rd_instance_pr.keys(key_str + ":*:")
        elif key_str == "users" or key_str == "groups":
            __mt = self.rd_instance_us.keys(key_str + ":*:")
        __mt_id = map(lambda x: int(x.split(":")[1]), __mt)
        if key_str == "projects":
            __mt = map(lambda x: self.rd_instance_pr.hgetall(x), __mt)
        elif key_str == "users" or key_str == "groups":
            __mt = map(lambda x: self.rd_instance_us.hgetall(x), __mt)
        return dict(zip(__mt_id, __mt))

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

    # Add Functions

    def add_user_to_redis(self, us_id, us_info):
        parser.clean_info_user(us_info)
        self.rd_instance_us.hmset("users:" + str(us_id) + ":", us_info)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Added User %d" % int(us_id))

    def add_group_to_redis(self, gr_id, gr_info):
        parser.clean_info_group(gr_info)
        gr_info["members"] = []
        [gr_info["members"].append(x.get("id")) for x in self.gl_instance.get_groups_members_byId(id=gr_id)]
        self.rd_instance_us.hmset("groups:" + str(gr_id) + ":", gr_info)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Added Group %d" % int(gr_id))

    def add_project_to_redis(self, pr_id, pr_info):
        if pr_info.get("owner") is None:
            pr_info["owner"] = "groups:" + str(pr_info.get("namespace").get("id"))
        else:
            pr_info["owner"] = "users:" + str(pr_info.get("owner").get("id"))
        pr_info['tags'] = map(
            lambda x: x.get("name").encode("ascii", "ignore"),
            self.gl_instance.get_projects_repository_tags_byId(id=pr_id)
        )
        parser.clean_info_project(pr_info)
        self.rd_instance_pr.hmset("projects:" + str(pr_id) + ":", pr_info)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Added Project %d" % int(pr_id))

    def add_branches_to_redis(self, pr_id):
        __branches = self.gl_instance.get_projects_repository_branches_byId(id=pr_id)
        for i in __branches:
            parser.clean_info_branch(i)
            self.rd_instance_br.hmset("projects:" + str(pr_id) + ":branches:" + i.get("id") + ":", i)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Added %d Branches from project (%d)" % (len(__branches), int(pr_id)))

        return __branches

    def update_information(self, update):

        config.print_message("* Updating %s ..." % update)

        __mt_gl = self.get_keys_and_values_from_gitlab(update)
        __mt_rd = self.get_keys_and_values_from_redis(update)
        __mt_gl_id = __mt_gl.keys()
        __mt_rd_id = __mt_rd.keys()

        # Generate difference and intersection metadata
        __mt_new = list(set(__mt_gl_id).difference(set(__mt_rd_id)))
        __mt_mod = list(set(__mt_gl_id).intersection(set(__mt_rd_id)))
        __mt_del = list(set(__mt_rd_id).difference(set(__mt_gl_id)))

        # Print alert
        if config.DEBUGGER:
            config.print_message("- %d new | %d deleted | %d possible updates" %
                                 (len(__mt_new), len(__mt_del), len(__mt_mod)))

        # Insert New Detected Metadata
        for i in __mt_new:
            if update == "users":
                self.add_user_to_redis(i, __mt_gl[i])
            elif update == "groups":
                self.add_group_to_redis(i, __mt_gl[i])
            elif update == "projects":
                self.add_project_to_redis(i, __mt_gl[i])
                self.add_branches_to_redis(i)
