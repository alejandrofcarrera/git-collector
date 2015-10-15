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
import json
import settings as config
import inject

__author__ = 'Alejandro F. Carrera'


# Update Functions

def contributors_from_user_to_user(rd, rd_d, user_one, user_two):
    __pr = rd_d.smembers(user_one)
    for i in __pr:
        __cont = eval(rd.hgetall(i).get("contributors"))
        __cont.remove(user_one)
        if user_two not in __cont:
            __cont.append(user_two)
        rd.hset(i, "contributors", __cont)
    if len(rd_d.keys(user_two)) > 0:
        __pr_new = __pr.union(rd_d.smembers(user_two))
        rd_d.delete(user_one)
        rd_d.sadd(user_two, *__pr_new)
    else:
        rd_d.rename(user_one, user_two)


def commits_from_user_to_user(rd, rd_d, user_one, user_two):
    __pr = rd_d.keys(user_one + ":*")
    for i in __pr:
        __new_key = i.replace(user_one, user_two)
        __pr_id = __new_key.replace(user_two + ":p_", "")
        __co_us = rd_d.zrange(i, 0, -1, withscores=True)
        for j in __co_us:
            rd.hset(j[0], "author", user_two)
        if len(rd_d.keys(__new_key)) > 0:
            __co_old = rd_d.zrange(__new_key, 0, -1, withscores=True)
            __c_new = []
            for j in __co_us:
                __c_new += j
            for j in __co_old:
                __c_new +=j
            inject.inject_user_commits(
                rd_d, __pr_id, user_two, __c_new
            )
            rd_d.delete(i)
        else:
            rd_d.rename(i, __new_key)


def user_to_redis_and_update(self, us_id, us_info):

    __u_id = "u_" + str(us_id)
    __emails = json.loads(us_info.get("emails"))

    # Check if any user email exists at non gitlab users
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

            # Delete old user
            self.rd_instance_us.delete(__co_em)

            # Pass information from old user (Projects)
            contributors_from_user_to_user(
                self.rd_instance_pr, self.rd_instance_us_pr, __co_em, __u_id
            )

            # Pass information from old user (Branches)
            contributors_from_user_to_user(
                self.rd_instance_br, self.rd_instance_us_br, __co_em, __u_id
            )

            # Pass information from old user (Commits)
            commits_from_user_to_user(
                self.rd_instance_co, self.rd_instance_us_co, __co_em, __u_id
            )

    # Generate new user
    self.rd_instance_us.hmset(__u_id, us_info)

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Added User %d with old information" % int(us_id))
