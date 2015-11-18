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

import base64

__author__ = 'Alejandro F. Carrera'


# inject array of commits at branch db
# rd = redis database with keys and relations (i.e rd_instance_br_co)
# pr_id = project's id at gitlab
# br_name = branch's name
# commits = list of commits (hash + timestamp)
def inject_branch_commits(rd, pr_id, br_name, commits):

    # Generate pseudo-hash-id
    __br_base64 = base64.b16encode(br_name)

    # Generate project id
    __pr_id = "p_" + str(pr_id)

    # Generate key (project id + pseudo-hash-id)
    __br_id = __pr_id + ":" + __br_base64

    # Delete old values
    if len(rd.keys(__br_id)) > 0:
        rd.delete(__br_id)

    commits_push = []
    c = 0
    for i in commits:
        if c == 10000:
            rd.zadd(__br_id, *commits_push)
            commits_push = [i]
            c = 1
        else:
            commits_push.append(i)
            c += 1
    rd.zadd(__br_id, *commits_push)
