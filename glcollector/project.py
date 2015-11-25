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

import commit as util_commit
import settings as config
import st_clean
import st_diff
import commands
import base64
import shutil
import os


__author__ = 'Alejandro F. Carrera'


# Add project (project registered at gitlab) to redis
# pr_id = project identifier at gitlab
# pr_info = information cleaned from gitlab
def save(self, pr_id, pr_info):

    # Save project at fs if it is necessary
    save_fs(pr_info)

    # Generate pseudo-key-id
    __p_id = "p_" + str(pr_id)

    # Get project's owner from metadata
    if pr_info.get("owner") is None:
        pr_info["owner"] = "g_" + str(pr_info.get("namespace").get("id"))
    else:
        pr_info["owner"] = "u_" + str(pr_info.get("owner").get("id"))
    del pr_info["namespace"]

    # Get project's tags from Gitlab API
    pr_info['tags'] = map(
        lambda x: x.get("name").encode("ascii", "ignore"),
        self.gl_instance.get_projects_repository_tags_byId(id=pr_id)
    )

    # Generate state (boolean)
    pr_info['state'] = 'archived' if pr_info['archived'] == 'true' else 'active'
    del pr_info['archived']

    # Check if project exists at db
    if len(self.rd_instance_pr.keys(__p_id)) == 0:

        # Save project
        self.rd_instance_pr.hmset(__p_id, pr_info)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Added Project: %d" % int(pr_id))

    # Project exists at redis
    else:

        # Get info at redis
        pr_rd = self.rd_instance_pr.hgetall(__p_id)

        # Detect different information from two projects
        __new_project = st_diff.projects(pr_info, pr_rd)

        if __new_project is not None:

            # Generate new project
            self.rd_instance_pr.hmset(__p_id, pr_info)

            # Print alert
            if config.DEBUGGER:
                config.print_message("- Updated Project: %d" % int(pr_id))

    # Project has changes at branches, commits, metadata ...
    save_code(self, pr_id, pr_info.get("name"))


def save_code(self, pr_id, pr_name):

    # Generate pseudo-key-id
    __p_id = "p_" + str(pr_id)

    # Generate metadata from gitlab
    __branches_gl_info = {}
    __branches = self.gl_instance.get_projects_repository_branches_byId(id=pr_id)
    [__branches_gl_info.update({
        x.get("name"): x
    })for x in __branches]

    # Generate metadata from redis
    __branches_rd_info = {}
    __branches = self.rd_instance_br.keys(__p_id + ":*")
    [__branches_rd_info.update({
        base64.b16decode(x.split(":")[1]): self.rd_instance_br.hgetall(x)
    }) for x in __branches]

    # Generate difference and intersection metadata
    __mt_diff = set(__branches_gl_info.keys()).difference(set(__branches_rd_info.keys()))
    __mt_int = set(__branches_gl_info.keys()).intersection(set(__branches_rd_info.keys()))
    __mt_mod = list(__mt_diff.union(__mt_int))
    __mt_del = list(set(__branches_rd_info.keys()).difference(set(__branches_gl_info.keys())))

    # Structure for removed commits
    __mt_del_commits = set()

    # Delete information about Branch
    count = 0
    for i in __mt_del:

        # Number of deleted branches
        count += 1

        # Print alert
        if config.DEBUGGER:
            config.print_message(
                "* (%d) [%d/%d] Deleted %s" %(int(pr_id), count, len(__mt_del), i)
            )

        # Get information from redis
        __br_info = __branches_rd_info[i]

        # Generate pseudo-key-id and remove info
        __br_id = __p_id + ":" + __br_info.get("id")
        self.rd_instance_br.delete(__br_id)
        self.rd_instance_br_co.delete(__br_id)

        # Remove links with contributors
        __br_con = eval(__br_info.get("contributors"))
        for j in __br_con:
            __us_com = self.rd_instance_us_co.smembers(j)
            for x in __us_com:
                if str(x).startswith(__br_id):
                    __mt_del_commits.add(str(x).split(":")[0] + ":" + str(x).split(":")[2])
                    self.rd_instance_us_co.srem(j, x)

    # Remove all unique commits
    if len(__mt_del_commits) > 0:
        __rd_branch_co = set()
        __rd_branch = self.rd_instance_br.keys(__p_id + "*")
        for i in __rd_branch:
            __rd_branch_co = __rd_branch_co.union(
                set(dict(self.rd_instance_br_co.zrange(i, 0, -1)).keys())
            )
        for i in __mt_del_commits:
            if i not in __rd_branch_co:
                self.rd_instance_co.delete(i)
            
    # Update information about Branch
    count = 0
    for i in __mt_mod:

        # Number of reviewed branches
        count += 1

        # Print alert
        if config.DEBUGGER:
            config.print_message(
                "* (%d) [%d/%d] Reviewed %s" %(int(pr_id), count, len(__mt_mod), i)
            )

        # Clean information
        __br_info = __branches_gl_info[i]
        st_clean.branch(__br_info)

        # Generate pseudo-key-id
        __br_id = __p_id + ":" + __br_info.get("id")

        # Save / Replace information at redis
        self.rd_instance_br.hmset(__br_id, __br_info)

        # Update information about branch's commits
        util_commit.update(self, pr_id, pr_name, i)


# create project filesystem
# pr_info = information cleaned from gitlab
def save_fs(pr_info):

    # Create folder to allocate all repositories if it does not exist
    if not os.path.exists(config.COLLECTOR_GIT_FOLDER):
        os.makedirs(config.COLLECTOR_GIT_FOLDER)

    # Save (temp) current directory
    cur_dir = os.getcwd()

    # Generate pseudo-name-id and get url
    __pr_id = str(pr_info.get("id")) + "_" + pr_info.get("name")
    __pr_url = pr_info.get("http_url_to_repo")

    # Insert credentials HTTP/S
    __replace = "http://"
    if str(__pr_url).startswith("https://"):
        __replace = "https://"
    __pr_url = str(__pr_url).replace(
        __replace, __replace + config.GITLAB_USER + ":" + config.GITLAB_PASS + "@"
        )

    # Change current directory to folder
    os.chdir(config.COLLECTOR_GIT_FOLDER)

    # Check repository does not exist
    if not os.path.exists(__pr_id):

        # Clone (mirror like bare repository)
        commands.getstatusoutput("git clone --mirror " + __pr_url + " " + __pr_id)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Cloned Project: " + pr_info.get("name"))

    # Repository exists
    else:

        # Change current directory to repository
        os.chdir(config.COLLECTOR_GIT_FOLDER + __pr_id)

        # Clone (mirror like bare repository)
        commands.getstatusoutput("git pull " + __pr_url)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Pulled Project: " + pr_info.get("name"))

    # Revert current directory
    os.chdir(cur_dir)


# Delete project (project registered at gitlab) at redis
# pr_id = project identifier at gitlab
def delete(self, pr_id):

    # Generate pseudo-key-id
    __p_id = "p_" + str(pr_id)

    # Check project exists
    if len(self.rd_instance_pr.keys(__p_id)) > 0:

        # Get Info about project
        __pr_info = self.rd_instance_pr.hgetall(__p_id)

        # Move folder to deleted folder
        delete_fs(__pr_info)

        # Set flag to deleted
        self.rd_instance_pr.hset(__p_id, "state", "deleted")

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Removed Project %d " % int(pr_id))


# delete project filesystem
# pr_info = information cleaned from redis
def delete_fs(pr_info):

    # Save (temp) current directory
    cur_dir = os.getcwd()

    # Generate pseudo-name-id and get url
    __pr_id = str(pr_info.get("id")) + "_" + pr_info.get("name")

    # Check folder where allocate all repositories
    if os.path.exists(config.COLLECTOR_GIT_FOLDER):

        # Change current directory to folder
        os.chdir(config.COLLECTOR_GIT_FOLDER)

        # Check repository exists
        if os.path.exists(config.COLLECTOR_GIT_FOLDER + __pr_id):

            # Rename repository plus _deleted
            shutil.move(
                config.COLLECTOR_GIT_FOLDER + __pr_id,
                config.COLLECTOR_GIT_FOLDER + __pr_id + "_deleted"
            )

        # Revert current directory
        os.chdir(cur_dir)

