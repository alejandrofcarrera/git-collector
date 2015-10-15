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


# Inject Functions

def inject_branch_commits(rd, pr_id, br_name, commits):
    commits_push = []
    c = 0
    for i in commits:
        if c == 10000:
            rd.zadd("p_" + str(pr_id) + ":" + br_name, *commits_push)
            commits_push = [i]
            c = 1
        else:
            commits_push.append(i)
            c += 1
    rd.zadd("p_" + str(pr_id) + ":" + br_name, *commits_push)


def inject_project_commits(rd, pr_id, commits):
    commits_push = []
    c = 0
    for i in commits:
        if c == 10000:
            rd.zadd("p_" + str(pr_id), *commits_push)
            commits_push = [i]
            c = 1
        else:
            commits_push.append(i)
            c += 1
    rd.zadd("p_" + str(pr_id), *commits_push)


def inject_user_commits(rd, pr_id, user_id, commits):
    c = 0
    commits_push = []
    for i in commits:
        if c == 10000:
            rd.zadd(user_id + ":p_" + str(pr_id), *commits_push)
            commits_push = [i]
            c = 1
        else:
            commits_push.append(i)
            c += 1
    rd.zadd(user_id + ":p_" + str(pr_id), *commits_push)

