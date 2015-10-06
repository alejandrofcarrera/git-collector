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
        raise EnvironmentError("Configuration is not valid or Redis is not online")


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
            raise EnvironmentError("Configuration is not valid or Gitlab is not online")

    def rd_connect(self):
        try:
            self.rd_instance_pr = redis_create_pool(config.REDIS_DB_PR)
            self.rd_instance_us = redis_create_pool(config.REDIS_DB_US)
            self.rd_instance_br = redis_create_pool(config.REDIS_DB_BR)
            self.rd_instance_co = redis_create_pool(config.REDIS_DB_CO)
        except EnvironmentError as e:
            raise e

    # Get Functions

    def get_projects_from_redis(self):
        __projects = self.rd_instance_pr.keys("projects:*:")
        __projects_id = map(lambda x: int(x.split(":")[1]), __projects)
        __projects = map(lambda x: self.rd_instance_pr.hgetall(x), __projects)
        return dict(zip(__projects_id, __projects))

    def get_projects_from_gitlab(self):
        __projects = self.gl_instance.get_projects()
        __projects_id = map(lambda x: int(x.get('id')), __projects)
        return dict(zip(__projects_id, __projects))

    # Add Functions

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
            config.print_message(" * Added to Redis - Project %d" % int(pr_id))

    def add_branches_to_redis(self, pr_id):
        __branches = self.gl_instance.get_projects_repository_branches_byId(id=pr_id)
        for i in __branches:
            parser.clean_info_branch(i)
            self.rd_instance_br.hmset("projects:" + str(pr_id) + ":branches:" + i.get("id"), i)

        # Print alert
        if config.DEBUGGER:
            config.print_message(" * Added to Redis - %d Branches (%d)" % (len(__branches), int(pr_id)))

    def update_projects(self):

        # Get Projects Metadata (Gitlab)
        __pr_gl = self.get_projects_from_gitlab()
        __pr_gl_id = __pr_gl.keys()

        # Get Projects Metadata (Redis Cache)
        __pr_rd = self.get_projects_from_redis()
        __pr_rd_id = __pr_rd.keys()

        # Generate difference and intersection projects
        __pr_new = list(set(__pr_gl_id).difference(set(__pr_rd_id)))
        __pr_mod = list(set(__pr_gl_id).intersection(set(__pr_rd_id)))
        __pr_del = list(set(__pr_rd_id).difference(set(__pr_gl_id)))

        # Print alert
        if config.DEBUGGER:
            config.print_message(" * Detected %d new projects" % len(__pr_new))
            config.print_message(" * Detected %d deleted projects" % len(__pr_del))
            config.print_message(" * Detected %d projects with possible updates" % len(__pr_mod))

        # Insert New Project Metadata
        for i in __pr_new:
            self.add_project_to_redis(i, __pr_gl[i])
            self.add_branches_to_redis(i)

        # Delete Projects

        # Update Projects
