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
import st_diff

__author__ = 'Alejandro F. Carrera'


# Add user (user registered at gitlab) to redis
# us_id = user identifier at gitlab
# us_info = information cleaned from gitlab
def save(self, us_id, us_info):

    # Generate pseudo-key-id
    __u_id = "u_" + str(us_id)

    # Check if user exists at non gitlab users
    if len(self.rd_instance_us.keys(__u_id)) == 0:

        # Save user and mark to active
        us_info["state"] = "active"
        self.rd_instance_us.hmset("u_" + str(us_id), us_info)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Added User: %d" % int(us_id))

    # User exists at redis
    else:

        # Get info at redis
        us_rd = self.rd_instance_us.hgetall("u_" + str(us_id))

        # Detect different information from two users
        __new_user = st_diff.users(us_info, us_rd)

        if __new_user is not None:

            __new_user = us_info
            if "first_commit_at" in us_rd:
                __new_user["first_commit_at"] = us_rd.get("first_commit_at")
            if "last_commit_at" in us_rd:
                __new_user["last_commit_at"] = us_rd.get("last_commit_at")

            # Generate information about committer
            __em_gl = eval(us_info.get('emails'))
            __em_rd = eval(us_rd.get('emails'))

            # Emails added
            __em_added = set(__em_gl).difference(set(__em_rd))
            if len(__em_added) > 0:
                save_user_info_mod_emails(self, us_id, __new_user, __em_added, "new")

            # Emails deleted
            __em_deleted = set(__em_rd).difference(set(__em_gl))
            if len(__em_deleted) > 0:
                save_user_info_mod_emails(self, us_id, __new_user, __em_deleted, "delete")

            # Generate new user
            if len(__em_added) == 0 and len(__em_deleted) == 0:
                self.rd_instance_us.hmset(__u_id, __new_user)

            # Print alert
            if config.DEBUGGER:
                config.print_message("- Updated User: %d" % int(us_id))


# Delete user (user registered at gitlab) at redis
# us_id = user identifier at gitlab
def delete(self, us_id):

    # Generate pseudo-key-id
    __u_id = "u_" + str(us_id)

    # Generate temp information and remove from db
    rd_info = self.rd_instance_us.hgetall(__u_id)
    self.rd_instance_us.delete(__u_id)

    # Iterate over deleted emails
    # Get list of emails to update info about user
    __emails = eval(rd_info.get("emails"))
    for i in __emails:
        __co_em = "nu_" + base64.b16encode(i.lower())
        if len(self.rd_instance_us.keys(__co_em)) > 0:

            # Pass information from old user (Projects)
            pass_contributors_between_users(
                self.rd_instance_pr, self.rd_instance_us_pr, __u_id, __co_em, True
            )

            # Pass information from old user (Branches)
            pass_contributors_between_users(
                self.rd_instance_br, self.rd_instance_us_br, __u_id, __co_em, True
            )

            # Pass information from old user (Commits)
            pass_commits_between_users(
                self.rd_instance_co, self.rd_instance_us_co, __u_id, __co_em
            )

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Removed User %d" % int(us_id))


# Add user (committer) to redis
# em_user = committer email
def save_committer(self, em_user):

    # Generate pseudo-hash-id
    __em_b16 = "nu_" + base64.b16encode(em_user)

    # Check if user email exists at non gitlab users
    if len(self.rd_instance_us.keys(__em_b16)) == 0:

        # Save committer
        self.rd_instance_us.hset(__em_b16, "primary_email", em_user)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Detected and added Committer: %s" % em_user)


# Update contributors, commits and metadata of user at redis
# us_id = user identifier at gitlab
# us_info = information cleaned from gitlab
# emails_list = user's emails list
# func = boolean for detect new or delete information
def save_user_info_mod_emails(self, us_id, us_info, emails_list, func):

    __u_id = "u_" + str(us_id)

    # Iterate over added emails
    for i in emails_list:
        __co_em = "nu_" + base64.b16encode(i.lower())
        if len(self.rd_instance_us.keys(__co_em)) > 0:

            user_one = __co_em if func == "new" else __u_id
            user_two = __u_id if func == "new" else __co_em
            flag = func != "new"

            if func == "new":

                # Update metadata about first and last commit
                __us_info_old = self.rd_instance_us.hgetall(__co_em)
                if "first_commit_at" not in us_info or \
                        (long(__us_info_old.get("first_commit_at")) <
                             long(us_info.get("first_commit_at"))):
                    us_info["first_commit_at"] = __us_info_old.get("first_commit_at")
                if "last_commit_at" not in us_info or \
                        (long(__us_info_old.get("last_commit_at")) >
                             long(us_info.get("last_commit_at"))):
                    us_info["last_commit_at"] = __us_info_old.get("last_commit_at")

            # Pass information from old user (Projects)
            pass_contributors_between_users(
                self.rd_instance_pr, self.rd_instance_us_pr, user_one, user_two, flag
            )

            # Pass information from old user (Branches)
            pass_contributors_between_users(
                self.rd_instance_br, self.rd_instance_us_br, user_one, user_two, flag
            )

            # Pass information from old user (Commits)
            pass_commits_between_users(
                self.rd_instance_co, self.rd_instance_us_co, user_one, user_two
            )

    if func == "delete":

        # Remove information
        if "first_commit_at" in us_info:
            del us_info["first_commit_at"]
        if "last_commit_at" in us_info:
            del us_info["last_commit_at"]

        # Get list of emails to update info about user
        __emails = eval(us_info.get("emails"))
        for i in __emails:
            __co_em = "nu_" + base64.b16encode(i.lower())
            if len(self.rd_instance_us.keys(__co_em)) > 0:

                # Update metadata about first and last commit
                __us_info_old = self.rd_instance_us.hgetall(__co_em)
                if "first_commit_at" not in us_info or \
                        (long(__us_info_old.get("first_commit_at")) <
                             long(us_info.get("first_commit_at"))):
                    us_info["first_commit_at"] = __us_info_old.get("first_commit_at")
                if "last_commit_at" not in us_info or \
                        (long(__us_info_old.get("last_commit_at")) >
                             long(us_info.get("last_commit_at"))):
                    us_info["last_commit_at"] = __us_info_old.get("last_commit_at")

    # Save new metadata user
    self.rd_instance_us.hmset(__u_id, us_info)


# Pass contributors list from user (user/committer) to other (user/committer)
# if preference is False it will be from committer to user
# else it will be from user to committer
# rd = redis database with original info (i.e rd_instance_pr)
# rd_d = redis database with keys and relations (i.e rd_instance_pr_us)
# user_one | user_two = key user at redis
# preference = boolean to choose from and to
def pass_contributors_between_users(rd, rd_d, user_one, user_two, preference):
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


# Pass commits list from user to other user (update author)
# rd = redis database with original info (i.e rd_instance_co)
# rd_d = redis database with keys and relations (i.e rd_instance_us_co)
# user_one | user_two = key user at redis
def pass_commits_between_users(rd, rd_d, user_one, user_two):
    __pr = rd_d.keys(user_one + ":*")
    for i in __pr:
        [rd.hset(x, "author", user_two) for x in rd_d.zrange(i, 0, -1)]
