"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  This file is part of the Smart Developer Hub Project:
    http://www.smartdeveloperhub.org
  Center for Open Middleware
        http://www.centeropenmiddleware.com/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2016 Center for Open Middleware.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Licensed under the Apache License, Version 2.0 (the 'License');
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
            http://www.apache.org/licenses/LICENSE-2.0
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an 'AS IS' BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
"""

import time
import settings as config
import utils_git
import threading
import utils_db


__author__ = 'Alejandro F. Carrera'


def print_running():
    config.print_message(' * [Worker] Running')


def print_finishing():
    config.print_message(' * [Worker] Finished')


class CollectorTask(object):

    def __init__(self, redis_instance):
        self.thread = None
        self.data = None
        self.rd = redis_instance
        self.list = None

    def start(self):
        if self.thread is not None:
            if self.thread.isAlive():
                print_running()
        self.thread = threading.Thread(target=self.start_worker)
        self.thread.start()
        print_running()

    def status(self):
        if self.thread is None:
            return 'not_started'
        else:
            if self.thread.isAlive():
                return 'running'
            else:
                return 'finished'

    def start_worker(self):
        if self.list is not None:
            rep_active = self.list
        else:
            rep_active = utils_db.get_repositories_active(self.rd)
        for i in rep_active:
            time.sleep(10)
            rep_info = utils_db.get_repository(self.rd, i, True)
            utils_git.repository_clone(rep_info)
        print_finishing()