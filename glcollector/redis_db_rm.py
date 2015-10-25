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


# Update Functions

def contributors_from_user_to_user(rd, rd_d, user_one, user_two, preference):
    if preference is False:
        __pr = rd_d.smembers(user_one)
    else:
        __pr = rd_d.smembers(user_two)
    for i in __pr:
        __cont = eval(rd.hgetall(i).get("contributors"))
        __flag = False
        if user_one in __cont:
            __cont.remove(user_one)
            __flag = True
        if user_two not in __cont:
            __cont.append(user_two)
            __flag = True
        if __flag:
            rd.hset(i, "contributors", __cont)


def commits_from_user_to_user(rd, rd_d, user_one, user_two):
    __pr = rd_d.keys(user_one + ":*")
    for i in __pr:
        [rd.hset(x, "author", user_two) for x in rd_d.zrange(i, 0, -1)]


# Delete Functions

def user_from_redis(self, us_id):

    # Delete user
    __u_id = "u_" + str(us_id)
    self.rd_instance_us.hset(__u_id, "state", "deleted")
    rd_info = self.rd_instance_us.hgetall(__u_id)

    # Iterate over deleted emails
    # Get list of emails to update info about user
    __emails = eval(rd_info.get("emails"))
    for i in __emails:
        __co_em = "nu_" + base64.b16encode(i.lower())
        if len(self.rd_instance_us.keys(__co_em)) > 0:

            # Pass information from old user (Projects)
            contributors_from_user_to_user(
                self.rd_instance_pr, self.rd_instance_us_pr, __u_id, __co_em, True
            )

            # Pass information from old user (Branches)
            contributors_from_user_to_user(
                self.rd_instance_br, self.rd_instance_us_br, __u_id, __co_em, True
            )

            # Pass information from old user (Commits)
            commits_from_user_to_user(
                self.rd_instance_co, self.rd_instance_us_co, __u_id, __co_em
            )

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
