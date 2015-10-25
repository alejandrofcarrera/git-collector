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
import settings as config
import parser

__author__ = 'Alejandro F. Carrera'


# Update Functions

def projects_from_gitlab(self, pr_id, pr_info):

    # Get info from redis
    __p_id = "p_" + str(pr_id)
    pr_rd = self.rd_instance_pr.hgetall(__p_id)

    # Get extra infro from gitlab
    if pr_info.get("owner") is None:
        pr_info["owner"] = "g_" + str(pr_info.get("namespace").get("id"))
    else:
        pr_info["owner"] = "u_" + str(pr_info.get("owner").get("id"))
    pr_info['tags'] = map(
        lambda x: x.get("name").encode("ascii", "ignore"),
        self.gl_instance.get_projects_repository_tags_byId(id=pr_id)
    )
    pr_info['state'] = 'archived' if pr_info['archived'] == 'true' else 'active'
    del pr_info['archived']

    # Detect different information from two projects
    __new_project = parser.join_projects(pr_info, pr_rd)

    # Detect when last_activity_at has been modified
    __flag = True if "last_activity_at" in __new_project else False

    if __new_project is not None:

        # Generate new project
        __new_project = pr_info
        __new_project["contributors"] = pr_rd.get("contributors")
        __new_project["first_commit_at"] = pr_rd.get("first_commit_at")
        __new_project["last_commit_at"] = pr_rd.get("last_commit_at")
        self.rd_instance_pr.hmset(__p_id, pr_info)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Updated Project %d" % int(pr_id))

    return __flag


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


def user_to_redis_and_update(self, us_id, us_info):

    # Get list of emails to add info about user
    __emails = eval(us_info.get("emails"))
    user_to_redis_and_update_email(self, us_id, us_info, __emails)

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Added User %d" % int(us_id))


def user_to_redis_and_update_email(self, us_id, us_info, emails_list):

    __u_id = "u_" + str(us_id)

    # Iterate over added emails
    for i in emails_list:
        __co_em = "nu_" + base64.b16encode(i.lower())
        if len(self.rd_instance_us.keys(__co_em)) > 0:
            __us_info_old = self.rd_instance_us.hgetall(__co_em)

            # Copy old values to new user
            if "first_commit_at" not in us_info or \
                    (long(__us_info_old.get("first_commit_at")) <
                         long(us_info.get("first_commit_at"))):
                us_info["first_commit_at"] = __us_info_old.get("first_commit_at")
            if "last_commit_at" not in us_info or \
                    (long(__us_info_old.get("last_commit_at")) >
                         long(us_info.get("last_commit_at"))):
                us_info["last_commit_at"] = __us_info_old.get("last_commit_at")

            # Pass information from old user (Projects)
            contributors_from_user_to_user(
                self.rd_instance_pr, self.rd_instance_us_pr, __co_em, __u_id, False
            )

            # Pass information from old user (Branches)
            contributors_from_user_to_user(
                self.rd_instance_br, self.rd_instance_us_br, __co_em, __u_id, False
            )

            # Pass information from old user (Commits)
            commits_from_user_to_user(
                self.rd_instance_co, self.rd_instance_us_co, __co_em, __u_id
            )

    # Generate new user
    self.rd_instance_us.hmset(__u_id, us_info)


def user_to_redis_and_delete_email(self, us_id, us_info, emails_list):

    __u_id = "u_" + str(us_id)

    # Iterate over deleted emails
    for i in emails_list:
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

    # Remove information
    del us_info["first_commit_at"]
    del us_info["last_commit_at"]

    # Get list of emails to update info about user
    __emails = eval(us_info.get("emails"))
    for i in __emails:
        __co_em = "nu_" + base64.b16encode(i.lower())
        if len(self.rd_instance_us.keys(__co_em)) > 0:
            __us_info_old = self.rd_instance_us.hgetall(__co_em)

            # Copy old values to new user
            if "first_commit_at" not in us_info or \
                    (long(__us_info_old.get("first_commit_at")) <
                         long(us_info.get("first_commit_at"))):
                us_info["first_commit_at"] = __us_info_old.get("first_commit_at")
            if "last_commit_at" not in us_info or \
                    (long(__us_info_old.get("last_commit_at")) >
                         long(us_info.get("last_commit_at"))):
                us_info["last_commit_at"] = __us_info_old.get("last_commit_at")

    # Generate new user
    self.rd_instance_us.hmset(__u_id, us_info)


def user_from_gitlab(self, us_id, us_info):

    # Get info at redis
    us_rd = self.rd_instance_us.hgetall("u_" + str(us_id))

    # Detect different information from two users
    __new_user = parser.join_users(us_info, us_rd)

    if __new_user is not None:

        __new_user = us_info
        __new_user["first_commit_at"] = us_rd.get("first_commit_at")
        __new_user["last_commit_at"] = us_rd.get("last_commit_at")

        # Generate information about committer
        __em_gl = eval(us_info.get('emails'))
        __em_rd = eval(us_rd.get('emails'))

        # Emails added
        __em_added = set(__em_gl).difference(set(__em_rd))
        if len(__em_added) > 0:
            user_to_redis_and_update_email(self, us_id, __new_user, __em_added)

        # Emails deleted
        __em_deleted = set(__em_rd).difference(set(__em_gl))
        if len(__em_deleted) > 0:
            user_to_redis_and_delete_email(self, us_id, __new_user, __em_deleted)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Updated User %d" % int(us_id))


def group_from_gitlab(self, gr_id, gr_info):

    # Get info at redis
    __g_id = "g_" + str(gr_id)
    gr_rd = self.rd_instance_us.hgetall(__g_id)

    # Detect different information from two groups
    __new_group = parser.join_groups(gr_info, gr_rd)

    if __new_group is not None:

        # Generate new group
        self.rd_instance_us.hmset(__g_id, gr_info)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Updated Group %d" % int(gr_id))