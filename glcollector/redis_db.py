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
import settings as config
import parser, inject, sniff

__author__ = 'Alejandro F. Carrera'


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
    __us = sniff.get_values_from_redis(self, "users")
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
                j_info = parser.get_info_commit(pr_name, j.get("id"))
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
        inject.inject_branch_commits(self.rd_instance_br, pr_id, base64.b16encode(i), __co_br)

    # Inject commits to Project
    __info['commits'] = __info['commits'].values()
    __info['commits'].sort(key=lambda j: j.get('created_at'), reverse=False)
    __co_pr = []
    for i in __info["commits"]:
        __co_pr.append("projects:" + str(pr_id) + ":commits:" + i.get("id") + ":")
        __co_pr.append(i.get("created_at"))
    inject.inject_project_commits(self.rd_instance_co, pr_id, __co_pr)

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
        inject.inject_user_commits(self.rd_instance_us, pr_id, w, comm_un_project_user)

    # Print alert
    if config.DEBUGGER:
        config.print_message("* Added to Redis - %d Commits (%d)" % (len(__co), int(pr_id)))