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
import shutil
import base64
import os
import settings as config
import inject

__author__ = 'Alejandro F. Carrera'


# Add Functions

def non_user_to_redis(self, em_user):

    # Check if user email exists at non gitlab users
    __em_b16 = base64.b16encode(em_user)
    if len(self.rd_instance_us.keys("nu_" + __em_b16)) == 0:

        # Save user
        self.rd_instance_us.hset("nu_" + __em_b16, "primary_email", em_user)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Detected and added Committer %s" % em_user)


# Delete Functions

def user_from_redis(self, us_id):

    # Delete user
    __u_id_old = "u_" + str(us_id)
    self.rd_instance_us.delete(__u_id_old)
    self.rd_instance_us_pr.delete(__u_id_old)

    # Get all commits linked to this user
    __pr_us = self.rd_instance_us_co.keys(__u_id_old + ":*")
    __pr_co = []

    for i in __pr_us:
        __pr_co += self.rd_instance_us_co.zrange(i, 0, -1)
        self.rd_instance_us_co.delete(i)

    if len(__pr_us) > 0:

        __users = {}

        for i in __pr_co:

            # Get information about each commit
            __pr_id = i.split(":")[0]
            __co_info = self.rd_instance_co.hgetall(i)
            __co_em = str(__co_info.get("author_email")).lower()
            __co_em_b16 = base64.b16encode(__co_em)
            __u_id_new = "nu_" + __co_em_b16

            # Create new non user if he does not exist
            non_user_to_redis(self, __co_em)
            if __u_id_new not in __users:
                __users[__u_id_new] = {
                    'first_commit_at': 0,
                    'last_commit_at': 0,
                    'co_project': {},
                    'co_ids': {},
                    'branches': {}
                }

            # Linking between commits - projects - non user
            if __pr_id not in __users[__u_id_new]["co_project"]:
                __users[__u_id_new]["co_project"][__pr_id] = []
            __users[__u_id_new]["co_project"][__pr_id].append(__pr_id + ":" + __co_info.get("id"))
            __users[__u_id_new]["co_project"][__pr_id].append(__co_info.get("created_at"))
            __users[__u_id_new]["co_ids"][__pr_id + ":" + __co_info.get("id")] = "1"

            # Change information about author at each commit
            self.rd_instance_co.hset(i, "author", __u_id_new)

            # Create information about last/first commit
            if __users[__u_id_new].get("first_commit_at") == 0 or \
               __users[__u_id_new].get("first_commit_at") > __co_info.get("created_at"):
                __users[__u_id_new]["first_commit_at"] = __co_info.get("created_at")
                self.rd_instance_us.hset(__u_id_new, "first_commit_at", __co_info.get("created_at"))
            if __users[__u_id_new].get("last_commit_at") == 0 or \
               __users[__u_id_new].get("last_commit_at") < __co_info.get("created_at"):
                __users[__u_id_new]["last_commit_at"] = __co_info.get("created_at")
                self.rd_instance_us.hset(__u_id_new, "last_commit_at", __co_info.get("created_at"))

        # Get and delete information about branches
        __br = self.rd_instance_us_br.smembers(__u_id_old)
        self.rd_instance_us_br.delete(__u_id_old)

        # Add links between user and commits/projects
        for i in __users.keys():
            for j in __users[i]["co_project"].keys():
                inject.inject_user_commits(
                    self.rd_instance_us_co, j.replace("p_", ""), i, __users[i]["co_project"][j]
                )
                __cont = eval(self.rd_instance_pr.hgetall(j).get("contributors"))
                if __u_id_old not in __cont:
                    __cont.remove(__u_id_old)
                if __u_id_new not in __cont:
                    __cont.append(__u_id_new)
                    self.rd_instance_pr.hset(j, "contributors", __cont)
            self.rd_instance_us_pr.sadd(i, *__users[i]["co_project"].keys())

            for j in __br:
                __us_co = __users[i]["co_ids"].keys()
                __br_co = self.rd_instance_br_co.zrange(j, 0, -1)
                if len(set(__br_co).intersection(set(__us_co))) > 0:
                    __cont = eval(self.rd_instance_br.hgetall(j).get("contributors"))
                    if __u_id_old not in __cont:
                        __cont.remove(__u_id_old)
                    if __u_id_new not in __cont:
                        __cont.append(__u_id_new)
                        self.rd_instance_br.hset(j, "contributors", __cont)
                    __users[i]["branches"][j] = "1"

        # Add links between users and branches
        for i in __users.keys():
            self.rd_instance_us_br.sadd(i, *__users[i]["branches"].keys())

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Removed User %d" % int(us_id))


def group_from_redis(self, gr_id):

    # Set flag to deleted
    self.rd_instance_us.hset("g_" + str(gr_id), "state", "deleted")

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Removed Group %d" % int(gr_id))


def project_to_filesystem(pr_info):
    cur_dir = os.getcwd()
    if os.path.exists(config.COLLECTOR_GIT_FOLDER + pr_info.get("name")):
        os.chdir(config.COLLECTOR_GIT_FOLDER)
        shutil.move(
            config.COLLECTOR_GIT_FOLDER + pr_info.get("name"),
            config.COLLECTOR_GIT_FOLDER + pr_info.get("name") + "_deleted"
        )
        os.chdir(cur_dir)


def project_from_redis(self, pr_id):

    # Get Info about project
    __pr_info = self.rd_instance_pr.hgetall("p_" + str(pr_id))

    # Move folder to deleted folder
    project_to_filesystem(__pr_info)

    # Set flag to deleted
    self.rd_instance_pr.hset("p_" + str(pr_id), "state", "deleted")

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Removed Project %d " % int(pr_id))
