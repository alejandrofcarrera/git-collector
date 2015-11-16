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
import user as util_user
import st_clean
import commands
import base64
import inject
import os
import re

__author__ = 'Alejandro F. Carrera'


# Get commit's information from git log
# pr_id = project identifier at gitlab
# pr_name = name of project
# commit = sha identifier
def get_commit_info(pr_id, pr_name, commit):

    # Save (temp) current directory
    cur_dir = os.getcwd()

    # Generate pseudo-name-id
    __pr_id = str(pr_id) + "_" + pr_name

    # Change current directory to folder
    os.chdir(config.COLLECTOR_GIT_FOLDER + __pr_id)

    # Generate command line (git log)
    __info_std = "git log --pretty=oneline --shortstat -1 " + commit.get("id")
    __info_std = commands.getoutput(__info_std)

    # Create regular expresion to search "number file pattern"
    __p = re.compile(r"\d+ file")
    __last = None

    # Find last occurrence
    for m in __p.finditer(__info_std):
        __last = m

    # Check if it is not exist
    if __last is None:
        commit["files_changed"] = 0
        commit["lines_added"] = 0
        commit["lines_removed"] = 0

    # Files have been changed
    else:
        __p = m.start()
        __info_std = __info_std[__p:]
        __info_std = __info_std.split(", ")
        if "files" not in __info_std[0]:
            commit["files_changed"] = int(__info_std[0].replace(" file changed", ""))
        else:
            commit["files_changed"] = int(__info_std[0].replace(" files changed", ""))
        if len(__info_std) > 1:
            if "insertion" in __info_std[1]:
                if "insertions" not in __info_std[1]:
                    commit["lines_added"] = int(__info_std[1].replace(" insertion(+)", ""))
                else:
                    commit["lines_added"] = int(__info_std[1].replace(" insertions(+)", ""))
            else:
                commit["lines_added"] = 0
                if "deletions" not in __info_std[1]:
                    commit["lines_removed"] = int(__info_std[1].replace(" deletion(-)", ""))
                else:
                    commit["lines_removed"] = int(__info_std[1].replace(" deletions(-)", ""))
        if len(__info_std) > 2:
            if "deletions" not in __info_std[2]:
                commit["lines_removed"] = int(__info_std[2].replace(" deletion(-)", ""))
            else:
                commit["lines_removed"] = int(__info_std[2].replace(" deletions(-)", ""))
        else:
            commit["lines_removed"] = 0

    # Revert current directory
    os.chdir(cur_dir)


# Add/Remove branch's commits information
# pr_id = project identifier at gitlab
# pr_name = name of project
# br_name = branch's name
def update(self, pr_id, pr_name, br_name):

    # Generate pseudo-key-id
    __pr_id = "p_" + str(pr_id)
    __br_id = __pr_id + ":" + base64.b16encode(br_name)

    # Data structure for branch's collaborators
    __br_info_collaborators = set()

    # Create Redis Data structure (id + score, in this case timestamp)
    __co_br = []

    # Get all commits from specific branch (gitlab) ids + commit's info
    __co_gl_val = self.gl_instance.get_projects_repository_commits_byId(id=pr_id, ref_name=br_name)
    __co_gl_id = map(lambda x: x.get("id"), __co_gl_val)
    __co_gl_val = dict(zip(__co_gl_id, __co_gl_val))

    # Get all commits from specific branch (redis) ids + created_at
    __co_rd_id = []
    __co_rd_val = {}
    if len(self.rd_instance_br_co.keys(__br_id)) > 0:
        __br_info_collaborators = set(eval(
            self.rd_instance_br.hgetall(__br_id).get("contributors")
        ))
        __co_rd_val = dict(self.rd_instance_br_co.zrange(__br_id, 0, -1, withscores=True))
        __co_rd_id = __co_rd_val.keys()

    # Generate difference and intersection metadata
    __mt_new = list(set(__co_gl_id).difference(set(__co_rd_id)))
    __mt_del = list(set(__co_rd_id).difference(set(__co_gl_id)))
    __mt_int = set(__co_gl_id).intersection(set(__co_rd_id))
    __mt_mod = list(set(__mt_new).union(__mt_int))

    # Fill branch's commits without deleted
    [__co_br.extend([i, long(__co_rd_val[i])]) for i in __mt_mod]

    # Regenerate structure of branch
    if len(__mt_new) > 0 or len(__mt_del) > 0:
        self.rd_instance_br_co.delete(__br_id)

    # Update or add commits to redis
    for i in __mt_new:

        # Get commit identifier (sha) + info
        __co_id = i

        # Get email from commit and add as contributor
        __co_em = __co_gl_val[i].get('author_email').lower()
        __user_key = "nu_" + base64.b16encode(__co_em)
        self.rd_instance_us_co.sadd(__user_key, __br_id + ":" + __co_id)
        __br_info_collaborators.add(__user_key)

        # Get information from gitlab or redis
        if len(self.rd_instance_co.keys(__co_id)) == 0:
            __co_info = __co_gl_val[i]
            st_clean.commit(__co_info)

            # Get commit information from git log
            get_commit_info(pr_id, pr_name, __co_info)
            __co_info["author"] = "nu_" + base64.b16encode(__co_em)

            # Insert commit information
            self.rd_instance_co.hmset(__co_id, __co_info)

        else:
            __co_info = self.rd_instance_co.hgetall(__co_id)

        # Set values at Redis Structure (id + timestamp)
        __co_br.append(__co_id)
        __co_br.append(long(__co_info.get("created_at")))

    for i in __mt_del:

        # Get commit identifier (sha) + info
        __co_id = i
        __co_info = self.rd_instance_co.hgetall(__co_id)

        # Get email from commit and add as contributor
        __co_em = __co_info.get('author_email').lower()
        __user_key = "nu_" + base64.b16encode(__co_em)
        self.rd_instance_us_co.srem(__user_key, __br_id + ":" + __co_id)

    # Check if contributors keep being same
    if len(__mt_del) > 0:
        __br_info_collaborators_tmp = __br_info_collaborators.copy()
        for i in __br_info_collaborators:
            count_co = 0
            __br_us_co = self.rd_instance_us_co.smembers(i)
            for j in __br_us_co:
                if str(j).startswith(__br_id):
                    count_co = 1
                    break
            if count_co == 0:
                __br_info_collaborators_tmp.remove(i)
        __br_info_collaborators = __br_info_collaborators_tmp

    # Inject commits to branch from data structure filled
    if len(__mt_new) > 0 or len(__mt_del) > 0:
        inject.inject_branch_commits(self.rd_instance_br_co, pr_id, br_name, __co_br)

    # Insert information to branch
    self.rd_instance_br.hset(__br_id, 'contributors', list(__br_info_collaborators))

    if len(__mt_new) > 0:

        # Print alert
        if config.DEBUGGER:
            config.print_message("* (%d) Added %s: %d Commits" % (int(pr_id), br_name, len(__mt_new)))

    if len(__mt_del) > 0:

        # Print alert
        if config.DEBUGGER:
            config.print_message("* (%d) Deleted %s: %d Commits" % (int(pr_id), br_name, len(__mt_del)))