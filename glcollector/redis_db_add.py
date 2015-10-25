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
import os
import settings as config
import parser, inject, sniff

__author__ = 'Alejandro F. Carrera'


# Add Functions

def user_to_redis(self, us_id, us_info):

    # Save user
    us_info["state"] = "active"
    self.rd_instance_us.hmset("u_" + str(us_id), us_info)

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Added User %d" % int(us_id))


def non_user_to_redis(self, em_user):

    # Check if user email exists at non gitlab users
    __em_b16 = base64.b16encode(em_user)
    if len(self.rd_instance_us.keys("nu_" + __em_b16)) == 0:

        # Save user
        self.rd_instance_us.hset("nu_" + __em_b16, "primary_email", em_user)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Detected and added Committer %s" % em_user)


def group_to_redis(self, gr_id, gr_info):

    # Set flag to active
    gr_info["state"] = "active"
    self.rd_instance_us.hmset("g_" + str(gr_id), gr_info)

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Added Group %d" % int(gr_id))


def project_to_filesystem(pr_info):
    if not os.path.exists(config.COLLECTOR_GIT_FOLDER):
        os.makedirs(config.COLLECTOR_GIT_FOLDER)
    cur_dir = os.getcwd()
    if not os.path.exists(config.COLLECTOR_GIT_FOLDER + pr_info.get("name")):
        os.chdir(config.COLLECTOR_GIT_FOLDER)
        commands.getstatusoutput("git clone --mirror " +
                                 pr_info.get("http_url_to_repo") + " " +
                                 str(pr_info.get("id")) + "_" + pr_info.get("name"))
        os.chdir(cur_dir)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Cloned Project " + pr_info.get("name"))


def project_to_redis(self, pr_id, pr_info):
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
    self.rd_instance_pr.hmset("p_" + str(pr_id), pr_info)


def branches_to_redis(self, pr_id):
    __branches = self.gl_instance.get_projects_repository_branches_byId(id=pr_id)
    for i in __branches:
        parser.clean_info_branch(i)
        self.rd_instance_br.hmset("p_" + str(pr_id) + ":" + i.get("id"), i)

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Added %d Branches from project (%d)" % (len(__branches), int(pr_id)))

    return __branches


def commits_to_redis(self, pr_id, pr_name):

    # Get Branches about project
    __br = self.rd_instance_br.keys("p_" + str(pr_id) + ":*")
    __br = map(lambda x: base64.b16decode(x.split(":")[1]), __br)

    # Get Users emails
    __us_emails = {}
    __us = sniff.get_values_from_redis(self, "users")
    for i in __us:
        __em = eval(__us[i].get('emails'))
        for j in __em:
            __us_emails.update({str(j).lower(): i})

    # Object for project information
    __info = {
        "commits": {},
        "authors": {},
        "authors_project": {}
    }

    # For through Branches
    for i in __br:

        # Data structure for branch's collaborators
        __br_info_collaborators = {}
        __br_info_collaborators_all = {}

        # Create Redis Data structure (id + score, in this case timestamp)
        __co_br = []

        # Get all commits from specific branch
        __co = self.gl_instance.get_projects_repository_commits_byId(id=pr_id, ref_name=i)

        # For through these commits
        for j in __co:
            parser.clean_info_commit(j)
            __co_id = j.get("id")
            __co_info = j

            # Set values at Redis Structure (id + timestamp)
            __co_br.append(__co_id)
            __co_br.append(__co_info.get("created_at"))

            # Get email from commit
            __co_em = __co_info.get('author_email').lower()

            # Detect if committer is not registered user
            collaborator_id = None
            if __co_em in __us_emails:
                collaborator_id = str(__us_emails[__co_em])
            non_user_to_redis(self, __co_em)
            __user_key = "nu_" + base64.b16encode(__co_em)

            # Detect unique repository commits (sha)
            # Also get extra info from git log and save commit
            if __co_id not in __info["commits"]:

                parser.get_info_commit(pr_id, pr_name, __co_info)

                if collaborator_id is None:
                    __co_info["author"] = __user_key
                else:
                    __co_info["author"] = collaborator_id
                __info['commits'][__co_id] = __co_info

                # Insert commit information
                self.rd_instance_co.hmset(
                    __co_id, __co_info
                )

            # Save metadata for later (users info)
            if __user_key not in __info["authors"]:
                __info["authors"][__user_key] = {}
            if __co_id not in __info["authors"][__user_key]:
                __info["authors"][__user_key][__co_id] = __co_info
            __br_info_collaborators_all[__user_key] = '1'
            if collaborator_id is not None:
                if collaborator_id not in __info["authors"]:
                    __info["authors"][collaborator_id] = {}
                if __co_id not in __info["authors"][collaborator_id]:
                    __info["authors"][collaborator_id][__co_id] = __co_info
                __info["authors_project"][collaborator_id] = '1'
                __br_info_collaborators[collaborator_id] = '1'
            else:
                __info["authors_project"][__user_key] = '1'
                __br_info_collaborators[__user_key] = '1'

        # Inject commits to branch from data structure filled
        inject.inject_branch_commits(self.rd_instance_br_co, pr_id, base64.b16encode(i), __co_br)

        # Insert information to branch
        self.rd_instance_br.hset(
            "p_" + str(pr_id) + ":" + base64.b16encode(i), 'contributors',
            __br_info_collaborators.keys()
        )

        # Insert relation between user and branch
        for j in __br_info_collaborators_all.keys():
            if not self.rd_instance_us_br.sismember(
                j, "p_" + str(pr_id) + ":" + base64.b16encode(i)
            ):
                self.rd_instance_us_br.sadd(
                    j, "p_" + str(pr_id) + ":" + base64.b16encode(i)
                )

        # Sort Branch's commits by timestamp
        __co.sort(key=lambda j: j.get('created_at'), reverse=False)
        if len(__co) > 0:
            self.rd_instance_br.hset(
                "p_" + str(pr_id) + ":" + base64.b16encode(i)
                , 'created_at', __co[0].get('created_at')
            )
            self.rd_instance_br.hset(
                "p_" + str(pr_id) + ":" + base64.b16encode(i),
                'last_commit', __co[-1].get('id')
            )

    # Inject commits to Project
    __info['commits'] = __info['commits'].values()
    __info['commits'].sort(key=lambda j: j.get('created_at'), reverse=False)

    # Create and inject Redis Data structure (same case like Branch)
    __co_pr = []
    for i in __info["commits"]:
        __co_pr.append(i.get("id"))
        __co_pr.append(i.get("created_at"))
    inject.inject_project_commits(self.rd_instance_pr_co, pr_id, __co_pr)

    # Insert information to project
    self.rd_instance_pr.hset(
        "p_" + str(pr_id), 'contributors',
        __info['authors_project'].keys()
    )
    if len(__co_pr) > 0:
        self.rd_instance_pr.hset(
            "p_" + str(pr_id), 'first_commit_at',
            __co_pr[1]
        )
        self.rd_instance_pr.hset(
            "p_" + str(pr_id), 'last_commit_at',
            __co_pr[-1]
        )

    # For through project's authors
    for w in __info["authors"]:

        # Sort authors's commits by timestamp
        __info["authors"][w] = __info["authors"][w].values()
        __info["authors"][w].sort(key=lambda x: x.get('created_at'), reverse=False)

        if not w.startswith("u_"):

            # Insert relation between user and project
            if not self.rd_instance_us_pr.sismember(w, "p_" + str(pr_id)):
                self.rd_instance_us_pr.sadd(w, "p_" + str(pr_id))

        # Create and inject Redis Data structure (same case like Project or Branch)
        comm_un_project_user = []
        for j in __info["authors"][w]:
            comm_un_project_user.append(j.get("id"))
            comm_un_project_user.append(j.get('created_at'))
        if not w.startswith("u_"):
            inject.inject_user_commits(self.rd_instance_us_co, pr_id, w, comm_un_project_user)

        # Insert information to user
        if len(comm_un_project_user) > 0:
            __first = comm_un_project_user[1]
            __last = comm_un_project_user[-1]
            __first_us = self.rd_instance_us.hget(str(w), "first_commit_at")
            __last_us = self.rd_instance_us.hget(str(w), "last_commit_at")
            if __first_us is None or __first_us > __first:
                self.rd_instance_us.hset(str(w), "first_commit_at", __first)
            if __last_us is None or __last_us < __last:
                self.rd_instance_us.hset(str(w), "last_commit_at", __last)

    # Print alert
    if config.DEBUGGER:
        config.print_message("* Added to Redis - %d Commits (%d)" % (len(__co), int(pr_id)))
