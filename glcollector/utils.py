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

import commands
import base64
import json
import os

import redis
from glapi import GlAPI

import settings as config
import parser

__author__ = 'Alejandro F. Carrera'


# Redis Help Functions
def redis_create_pool(db):
    __redis_db = redis.ConnectionPool(
        host=config.REDIS_IP,
        port=config.REDIS_PORT,
        db=db,
        password=config.REDIS_PASS
    )
    __redis_db = redis.Redis(connection_pool=__redis_db)
    try:
        __redis_db.client_list()
        return __redis_db
    except Exception as e:
        raise EnvironmentError("- Configuration is not valid or Redis is not online")


class Collector(object):

    """GitLab Collector Class

    Attributes:
        gl_instance (GitLab): GitLab object
        rd_instance (Redis): Redis object
    """

    def __init__(self):
        self.gl_instance = None
        self.rd_instance_pr = None
        self.rd_instance_us = None
        self.rd_instance_br = None
        self.rd_instance_co = None
        self.rd_instance_usco = None
        try:
            self.gl_connect()
            self.rd_connect()
        except EnvironmentError as e:
            raise e

    # Connection Functions

    def gl_connect(self):
        __host = "%s://%s:%d" % (config.GITLAB_PROT, config.GITLAB_IP, config.GITLAB_PORT)
        __gl = GlAPI(__host, ssl=config.GITLAB_VER_SSL)
        try:
            __gl.login(login=config.GITLAB_USER, password=config.GITLAB_PASS)
            self.gl_instance = __gl
        except Exception as e:
            raise EnvironmentError("- Configuration is not valid or Gitlab is not online")

    def rd_connect(self):
        try:
            self.rd_instance_pr = redis_create_pool(config.REDIS_DB_PR)
            self.rd_instance_us = redis_create_pool(config.REDIS_DB_US)
            self.rd_instance_br = redis_create_pool(config.REDIS_DB_BR)
            self.rd_instance_co = redis_create_pool(config.REDIS_DB_CO)
            self.rd_instance_usco = redis_create_pool(config.REDIS_DB_USCO)
        except EnvironmentError as e:
            raise e

    # Get Functions

    def get_keys_and_values_from_redis(self, key_str):
        if key_str == "projects":
            __mt = self.rd_instance_pr.keys(key_str + ":*:commits:")
        elif key_str == "users" or key_str == "groups":
            __mt = self.rd_instance_us.keys(key_str + ":*:")
        __mt_id = map(lambda x: int(x.split(":")[1]), __mt)
        if key_str == "projects":
            __mt = map(lambda x: self.rd_instance_pr.hgetall(
                x.replace("commits:", "")
            ), __mt)
        elif key_str == "users" or key_str == "groups":
            __mt = map(lambda x: self.rd_instance_us.hgetall(x), __mt)
        return dict(zip(__mt_id, __mt))

    def get_keys_and_values_from_gitlab(self, key_str):
        if key_str == "projects":
            __mt = self.gl_instance.get_projects()
        elif key_str == "users":
            __mt = self.gl_instance.get_users()
            for i in __mt:
                i['emails'] = [i.get('email')]
                del i['email']
                __em_lst = self.gl_instance.get_users_emails_byUid(uid=i.get('id'))
                for j in __em_lst:
                    i['emails'].append(j.get('email'))
                i['emails'] = json.dumps(i['emails'])

        elif key_str == "groups":
            __mt = self.gl_instance.get_groups()
        __mt_id = map(lambda x: int(x.get('id')), __mt)
        return dict(zip(__mt_id, __mt))

    # Inject Functions

    def inject_branch_commits(self, pr_id, br_name, commits):
        commits_push = []
        c = 0
        for i in commits:
            if c == 10000:
                self.rd_instance_br.zadd("projects:" + str(pr_id) + ":branches:" +
                                         br_name + ":commits:", *commits_push)
                commits_push = [i]
                c = 1
            else:
                commits_push.append(i)
                c += 1
        self.rd_instance_br.zadd("projects:" + str(pr_id) + ":branches:" +
                                 br_name + ":commits:", *commits_push)

    def inject_project_commits(self, pr_id, commits):
        commits_push = []
        c = 0
        for i in commits:
            if c == 10000:
                self.rd_instance_pr.zadd("projects:" + str(pr_id) + ":commits:", *commits_push)
                commits_push = [i]
                c = 1
            else:
                commits_push.append(i)
                c += 1
        self.rd_instance_pr.zadd("projects:" + str(pr_id) + ":commits:", *commits_push)

    def inject_user_commits(self, pr_id, user_id, commits):
        c = 0
        commits_push = []
        for i in commits:
            if c == 10000:
                self.rd_instance_usco.zadd(
                    "users:" + str(user_id) + ":projects:" +
                    str(pr_id) + ":commits:", *commits_push
                )
                commits_push = [i]
                c = 1
            else:
                commits_push.append(i)
                c += 1
        self.rd_instance_usco.zadd(
            "users:" + str(user_id) + ":projects:" +
            str(pr_id) + ":commits:", *commits_push
        )

    # Add Functions

    def add_user_to_redis(self, us_id, us_info):
        parser.clean_info_user(us_info)
        self.rd_instance_us.hmset("users:" + str(us_id) + ":", us_info)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Added User %d" % int(us_id))

    def add_group_to_redis(self, gr_id, gr_info):
        parser.clean_info_group(gr_info)
        gr_info["members"] = []
        [gr_info["members"].append(x.get("id")) for x in self.gl_instance.get_groups_members_byId(id=gr_id)]
        self.rd_instance_us.hmset("groups:" + str(gr_id) + ":", gr_info)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Added Group %d" % int(gr_id))

    def add_project_to_filesystem(self, pr_info):
        if not os.path.exists(config.COLLECTOR_GIT_FOLDER):
            os.makedirs(config.COLLECTOR_GIT_FOLDER)
        cur_dir = os.getcwd()
        if not os.path.exists(config.COLLECTOR_GIT_FOLDER + pr_info.get("name")):
            os.chdir(config.COLLECTOR_GIT_FOLDER)
            commands.getstatusoutput("git clone --mirror " +
                                     pr_info.get("http_url_to_repo") + " " + pr_info.get("name"))
            os.chdir(cur_dir)

            # Print alert
            if config.DEBUGGER:
                config.print_message("- Cloned Project " + pr_info.get("name"))

    def add_project_to_redis(self, pr_id, pr_info):
        if pr_info.get("owner") is None:
            pr_info["owner"] = "groups:" + str(pr_info.get("namespace").get("id"))
        else:
            pr_info["owner"] = "users:" + str(pr_info.get("owner").get("id"))
        pr_info['tags'] = map(
            lambda x: x.get("name").encode("ascii", "ignore"),
            self.gl_instance.get_projects_repository_tags_byId(id=pr_id)
        )
        parser.clean_info_project(pr_info)
        self.rd_instance_pr.hmset("projects:" + str(pr_id) + ":", pr_info)

    def add_branches_to_redis(self, pr_id):
        __branches = self.gl_instance.get_projects_repository_branches_byId(id=pr_id)
        for i in __branches:
            parser.clean_info_branch(i)
            self.rd_instance_br.hmset("projects:" + str(pr_id) + ":branches:" + i.get("id") + ":", i)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Added %d Branches from project (%d)" % (len(__branches), int(pr_id)))

        return __branches

    def add_commits_to_redis(self, pr_id, pr_name):

        # Get Branches about project
        __br = self.rd_instance_br.keys("projects:" + str(pr_id) + ":branches:*:")
        __br = map(lambda x: base64.b16decode(x.split(":")[3]), __br)

        # Get Users emails
        __us_emails = {}
        __us = self.get_keys_and_values_from_redis("users")
        for i in __us:
            __em = json.loads(__us[i].get('emails'))
            for j in __em:
                __us_emails.update({j: i})

        # Object for project information
        __info = {
            "collaborators": {},
            "commits": {},
            "authors": {}
        }

        for i in __br:
            __br_info_collaborators = {}
            __co_br = []
            __co = self.gl_instance.get_projects_repository_commits_byId(id=pr_id, ref_name=i)
            for j in __co:
                parser.clean_info_commit(j)
                if j.get('id') not in __info["commits"]:
                    __info['commits'][j.get('id')] = j
                    j_info = parser.get_info_commit(pr_name, j.get("id"), j.get("message"))
                    __info['commits'][j.get('id')]["files_changed"] = j_info["files_changed"]
                    __info['commits'][j.get('id')]["lines_added"] = j_info["lines_added"]
                    __info['commits'][j.get('id')]["lines_removed"] = j_info["lines_removed"]
                    self.rd_instance_co.hmset(
                        "projects:" + str(pr_id) + ":commits:" +
                        __info['commits'][j.get('id')].get("id") + ":",
                        __info['commits'][j.get('id')]
                    )
                __co_br.append("projects:" + str(pr_id) + ":commits:" + j.get("id") + ":")
                __co_br.append(__info['commits'][j.get('id')].get("created_at"))
                j['author_email'] = __info['commits'][j.get('id')].get('author_email').lower()
                if __info['commits'][j.get('id')].get('author_email') in __us_emails:
                    collaborator_id = __us_emails[j.get('author_email')]
                    if collaborator_id not in __info["authors"]:
                        __info["authors"][collaborator_id] = []
                    __info["authors"][collaborator_id].append(j)
                    __br_info_collaborators[collaborator_id] = '1'
                    __info['collaborators'][collaborator_id] = '1'

            # Inject information to branch
            __co.sort(key=lambda j: j.get('created_at'), reverse=False)
            self.rd_instance_br.hset(
                "projects:" + str(pr_id) + ":branches:" +
                base64.b16encode(i) + ":", 'created_at',
                __co[0].get('created_at')
            )
            self.rd_instance_br.hset(
                "projects:" + str(pr_id) + ":branches:" +
                base64.b16encode(i) + ":", 'last_commit',
                __co[-1].get('id')
            )
            self.rd_instance_br.hset(
                "projects:" + str(pr_id) + ":branches:" +
                base64.b16encode(i) + ":", 'contributors',
                __br_info_collaborators.keys()
            )

            # Inject commits to branch
            self.inject_branch_commits(pr_id, base64.b16encode(i), __co_br)

        # Inject commits to Project
        __info['commits'] = __info['commits'].values()
        __info['commits'].sort(key=lambda j: j.get('created_at'), reverse=False)
        __co_pr = []
        for i in __info["commits"]:
            __co_pr.append("projects:" + str(pr_id) + ":commits:" + i.get("id") + ":")
            __co_pr.append(i.get("created_at"))
        self.inject_project_commits(pr_id, __co_pr)

        # Inject Info Project
        self.rd_instance_pr.hset(
            "projects:" + str(pr_id) + ":", 'contributors',
            __info['collaborators'].keys()
        )
        self.rd_instance_pr.hset(
            "projects:" + str(pr_id) + ":", 'first_commit_at',
            __co_pr[1]
        )
        self.rd_instance_pr.hset(
            "projects:" + str(pr_id) + ":", 'last_commit_at',
            __co_pr[-1]
        )

        # Inject Info User
        for w in __info["authors"]:
            __info["authors"][w].sort(key=lambda j: j.get('created_at'), reverse=False)
            comm_un_project_user = []
            for j in __info["authors"][w]:
                comm_un_project_user.append("projects:" + str(i) + ":commits:" + j.get('id'))
                comm_un_project_user.append(j.get('created_at'))
            self.rd_instance_us.hset(
                "users:" + str(w) + ":",
                'first_commit_at', __info["authors"][w][0].get('created_at')
            )
            self.rd_instance_us.hset(
                "users:" + str(w) + ":",
                'last_commit_at', __info["authors"][w][-1].get('created_at')
            )
            self.inject_user_commits(pr_id, w, comm_un_project_user)

        # Print alert
        if config.DEBUGGER:
            config.print_message("* Added to Redis - %d Commits (%d)" % (len(__co), int(pr_id)))

    def update_information(self, update):

        config.print_message("* Updating %s ..." % update)

        __mt_gl = self.get_keys_and_values_from_gitlab(update)
        __mt_rd = self.get_keys_and_values_from_redis(update)
        __mt_gl_id = __mt_gl.keys()
        __mt_rd_id = __mt_rd.keys()

        # Generate difference and intersection metadata
        __mt_new = list(set(__mt_gl_id).difference(set(__mt_rd_id)))
        __mt_mod = list(set(__mt_gl_id).intersection(set(__mt_rd_id)))
        __mt_del = list(set(__mt_rd_id).difference(set(__mt_gl_id)))

        # Print alert
        if config.DEBUGGER:
            config.print_message("- %d new | %d deleted | %d possible updates" %
                                 (len(__mt_new), len(__mt_del), len(__mt_mod)))

        # Insert New Detected Metadata
        for i in __mt_new:
            if update == "users":
                self.add_user_to_redis(i, __mt_gl[i])
            elif update == "groups":
                self.add_group_to_redis(i, __mt_gl[i])
            elif update == "projects":
                self.add_project_to_filesystem(__mt_gl[i])
                self.add_project_to_redis(i, __mt_gl[i])
                self.add_branches_to_redis(i)
                self.add_commits_to_redis(i, __mt_gl[i].get("name"))

        # Delete Projects

        # Update Projects
