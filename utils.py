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
import gitlab
import redis

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
        self.rd_instance_meta = None
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
        __gl = gitlab.Gitlab(host=__host, verify_ssl=config.GITLAB_VER_SSL)
        try:
            self.gl_instance = __gl.login(user=config.GITLAB_USER, password=config.GITLAB_PASS)
        except Exception as e:
            raise EnvironmentError("Configuration is not valid or Gitlab is not online")

    def rd_connect(self):
        try:
            self.rd_instance_meta = redis_create_pool(config.REDIS_DB_META)
            self.rd_instance_br = redis_create_pool(config.REDIS_DB_BR)
            self.rd_instance_co = redis_create_pool(config.REDIS_DB_CO)
        except EnvironmentError as e:
            raise e

    # Help Functions

    def get_projects_from_redis(self):
        return lambda w: int(w.split(':')[1]), self.rd_instance_meta.keys("projects:*:")

    def get_projects_from_gitlab(self):
        return self.gl_instance.git.getprojectsall()

    def set_projects_to_redis(self):

        # Get Projects Metadata (Gitlab and Redis Cache)
        __pr_gl = self.get_projects_from_gitlab()
        __pr_rd_id = self.get_projects_from_redis()
        __pr_gl_id = (lambda w: w.get('id'), __pr_gl)

        # Generate difference and intersection projects
        __pr_new = list(set(__pr_gl_id).difference(set(__pr_rd_id)))
        __pr_mod = list(set(__pr_gl_id).intersection(set(__pr_rd_id)))
        __pr_del = list(set(__pr_rd_id).difference(set(__pr_gl_id)))

        # Print alert
        if config.DEBUGGER:
            config.print_message(" * Detected %d new projects" % len(__pr_new))
            config.print_message(" * Detected %d deleted projects" % len(__pr_del))
            config.print_message(" * Detected %d projects with possible updates" % len(__pr_mod))

        # Insert Projects

        # Delete Projects

        # Update Projects
