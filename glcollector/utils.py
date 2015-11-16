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

import redis
from glapi import GlAPI

import user as util_user
import group as util_group
import project as util_project
import settings as config
import sniff

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
        rd_instance_* (Redis): Redis object link with DB
    """

    def __init__(self):
        self.gl_instance = None
        self.rd_instance_pr = None
        self.rd_instance_br = None
        self.rd_instance_co = None
        self.rd_instance_us = None
        self.rd_instance_br_co = None
        self.rd_instance_us_co = None
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
            self.rd_instance_br = redis_create_pool(config.REDIS_DB_BR)
            self.rd_instance_co = redis_create_pool(config.REDIS_DB_CO)
            self.rd_instance_us = redis_create_pool(config.REDIS_DB_US)
            self.rd_instance_br_co = redis_create_pool(config.REDIS_DB_BR_CO)
            self.rd_instance_us_co = redis_create_pool(config.REDIS_DB_US_CO)
        except EnvironmentError as e:
            raise e

    def update_information(self, update):

        __mt_gl = sniff.get_keys_and_values_from_gitlab(self, update)
        __mt_rd_id = sniff.get_keys_from_redis(self, update)
        __mt_gl_id = __mt_gl.keys()

        # Generate difference and intersection metadata
        __mt_diff = set(__mt_gl_id).difference(set(__mt_rd_id))
        __mt_int = set(__mt_gl_id).intersection(set(__mt_rd_id))
        __mt_mod = list(__mt_diff.union(__mt_int))
        __mt_del = list(set(__mt_rd_id).difference(set(__mt_gl_id)))

        # Print alert
        if config.DEBUGGER:
            config.print_message("- [ %s ] New or possible updates: %d | Deleted: %d" %
                                 (update, len(__mt_mod), len(__mt_del)))

        # Insert / Modify Information
        for i in __mt_mod:
            if update == "users":
                util_user.save(self, i, __mt_gl[i])
            elif update == "groups":
                util_group.save(self, i, __mt_gl[i])
            elif update == "projects":
                util_project.save(self, i, __mt_gl[i])

        # Delete Information
        for i in __mt_del:
            if update == "users":
                util_user.delete(self, i)
            elif update == "groups":
                util_group.delete(self, i)
            elif update == "projects":
                util_project.delete(self, i)
