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


class Collector(object):

    """GitLab Collector Class

    Attributes:
        gl_instance (GitLab): GitLab object
        rd_instance (Redis): Redis object
    """

    def __init__(self):
        self.gl_instance = None
        self.rd_instance = None
        try:
            self.gl_connect()
            self.rd_connect()
        except EnvironmentError as e:
            raise e

    def gl_connect(self):
        __host = "%s://%s:%d" % (config.GITLAB_PROT, config.GITLAB_IP, config.GITLAB_PORT)
        __gl = gitlab.Gitlab(host=__host, verify_ssl=config.GITLAB_VER_SSL)
        try:
            self.gl_instance = __gl.login(user=config.GITLAB_USER, password=config.GITLAB_PASS)
        except Exception as e:
            raise EnvironmentError(" * %s (%s) Configuration is not valid or Gitlab is not online" %
                (config.LONGNAME, config.VERSION))

    def rd_connect(self):
        __rd = redis.ConnectionPool(
                host=self.cfg.get("REDIS_IP"),
                port=self.cfg.get("REDIS_PORT"),
                db=self.cfg.get("REDIS_DB"),
                password=self.cfg.get("REDIS_PASS")
            )
        __rd = redis.Redis(connection_pool=__rd)
        try:
            __rd.client_list()
            self.rd_instance = __rd
        except Exception as e:
            raise EnvironmentError(" * %s (%s) Configuration is not valid or Redis is not online" %
                (config.LONGNAME, config.VERSION))
