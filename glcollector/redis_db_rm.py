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


# Delete Functions

def user_from_redis(self, us_id):

    # Delete user from redis
    self.rd_instance_us.delete("users:" + str(us_id) + ":")

    # Get all projects and commits linked to this user
    __pr_us = self.rd_instance_usco.keys("users:" + str(us_id) + ":*:")
    if __pr_us is not None:
        __pr_us_id = map(lambda x: x.split(":")[3], __pr_us)

        # Remove information about author in all commits
        for i in __pr_us:
            __pr_co = self.rd_instance_usco.zrange(i, 0, -1)
            for j in __pr_co:
                self.rd_instance_co.hdel(j, "author")
            self.rd_instance_usco.delete(i)

        for i in __pr_us_id:

            # Remove contributor at project
            __col_pr = json.loads(self.rd_instance_pr.hgetall(
                "projects:" + str(i) + ":"
            ).get("contributors"))
            __col_pr.remove(us_id)
            self.rd_instance_pr.hset(
                "projects:" + str(i) + ":", "contributors", __col_pr
            )

            # Remove contributor at branches
            __col_br = self.rd_instance_br.keys("projects:" + str(i) + ":*:commits:")
            __col_br = map(lambda x: x.split(":")[3], __col_br)
            for j in __col_br:
                __col_br_sp = json.loads(
                    self.rd_instance_br.hgetall(
                        "projects:" + str(i) + ":branches:" + str(j) + ":"
                    ).get("contributors")
                )
                __col_br_sp.remove(us_id)
                self.rd_instance_br.hset(
                    "projects:" + str(i) + ":branches:" + str(j) + ":",
                    "contributors", __col_br_sp
                )

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


def project_from_filesystem(pr_info):
    if os.path.exists(config.COLLECTOR_GIT_FOLDER):
        cur_dir = os.getcwd()
        if os.path.exists(config.COLLECTOR_GIT_FOLDER + pr_info.get("name")):

            # Delete folder from filesystem
            os.chdir(config.COLLECTOR_GIT_FOLDER)
            shutil.rmtree(pr_info.get("name"), True)
            os.chdir(cur_dir)

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Removed files of Project " + pr_info.get("name"))


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
