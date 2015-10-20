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
import json
import os
import settings as config
import parser, inject, sniff

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


# TODO: test what happens with owned projects by group
def group_from_redis(self, gr_id):

    # Delete group from redis
    self.rd_instance_us.delete("groups:" + str(gr_id) + ":")

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Removed Group %d" % int(gr_id))


def project_from_redis(self, pr_id):

    # Get Collaborators
    __col_list = json.loads(
        self.rd_instance_pr.hgetall(
            "projects:" + str(pr_id) + ":"
        ).get("contributors")
    )

    # Delete project from redis
    self.rd_instance_pr.delete("projects:" + str(pr_id) + ":")
    self.rd_instance_pr.delete("projects:" + str(pr_id) + ":commits:")

    # Delete all branches
    __br = self.rd_instance_br("projects:" + str(pr_id) + ":*:commits:")
    __br = map(lambda x: x.split(":")[3], __br)
    for i in __br:
        self.rd_instance_br.delete("projects:" + str(pr_id) + ":" + str(i) + ":")
        self.rd_instance_br.delete("projects:" + str(pr_id) + ":" + str(i) + ":commits:")

    # Delete all commits
    __co = self.rd_instance_co("projects:" + str(pr_id) + ":*")
    for i in __co:
        self.rd_instance_co.delete(i)

    for i in __col_list:

        # Delete collaborator commits
        self.rd_instance_usco.delete("users:" + str(i) + ":projects:" + str(pr_id) + ":commits:")

        # Regenerate metadata of collaborator
        __co_list = self.rd_instance_usco.keys("users:" + str(i) + ":*")
        __us_info = self.rd_instance_us.hgetall("users:" + str(i) + ":")
        if "first_commit_at" in __us_info:
            __us_info["first_commit_at"] = 0
        if "last_commit_at" in __us_info:
            __us_info["last_commit_at"] = 0
        for j in __co_list:
            __start = self.rd_instance_usco.zrange(j, 0, 0, withscores=True)[1]
            __end = self.rd_instance_usco.zrange(j, -1, -1, withscores=True)[1]
            if __start < __us_info.get("first_commit_at"):
                __us_info["first_commit_at"] = __start
            if __end > __us_info.get("last_commit_at"):
                __us_info["last_commit_at"] = __end
        self.rd_instance_us.hmset("users:" + str(i) + ":", __us_info)

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Remove project %d " % int(pr_id))
