"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  This file is part of the Smart Developer Hub Project:
    http://www.smartdeveloperhub.org
  Center for Open Middleware
        http://www.centeropenmiddleware.com/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2016 Center for Open Middleware.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Licensed under the Apache License, Version 2.0 (the 'License');
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
            http://www.apache.org/licenses/LICENSE-2.0
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an 'AS IS' BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
"""

import settings as config
import commands
import os
import re

__author__ = 'Alejandro F. Carrera'


def repository_clone(info):

    # Save (temp) current directory
    cur_dir = os.getcwd()

    # Generate pseudo-name-id and get url
    __pr_id = info.get('id')
    __pr_url = info.get('url')

    # Insert credentials HTTP/S
    if 'user' in info and 'password' in info:
        __replace = 'http://'
        if str(__pr_url).startswith('https://'):
            __replace = 'https://'
        __pr_url = str(__pr_url).replace(
            __replace, __replace + info.get('user') + 
            ':' + info.get('password') + '@'
        )

    # Change current directory to folder
    os.chdir(config.GC_FOLDER)

    # Check repository does not exist
    res_st = 0
    if not os.path.exists(__pr_id):

        # Clone (mirror like bare repository)
        res = commands.getstatusoutput('git clone ' + __pr_url + ' ' + __pr_id)
        if res[0] == 0:
            config.print_message(' * [Worker] %s : Cloned' % __pr_id)
        else:
            res_st = 1
            if 'Repository not found.' in res[1]:
                config.print_message(' * [Worker] %s : ERROR - URL' % __pr_id)
            else:
                config.print_message(' * [Worker] %s : ERROR - Credentials' %
                                     __pr_id)

    # Repository exists
    else:

        # Change current directory to repository
        os.chdir(config.GC_FOLDER + '/' + __pr_id)

        # Clone (mirror like bare repository)
        res = commands.getstatusoutput('git pull ' + __pr_url)
        if res[0] == 0:
            config.print_message(' * [Worker] %s : Pulled' % __pr_id)
        else:
            res_st = 1
            if 'Repository not found.' in res[1]:
                config.print_message(' * [Worker] %s : ERROR - URL' % __pr_id)
            else:
                config.print_message(' * [Worker] %s : ERROR - Credentials' %
                                     __pr_id)

    # Revert current directory
    os.chdir(cur_dir)
    return res_st


def get_branches_from_repository(info):

    # Save (temp) current directory
    cur_dir = os.getcwd()

    # Generate pseudo-name-id
    __pr_id = info.get('id')

    # Change current directory to repository
    os.chdir(config.GC_FOLDER + '/' + __pr_id)

    # Get List of Remote Branches (HEAD must be deleted)
    res = commands.getstatusoutput('git branch -r')
    result = set()
    if res[0] == 0:
        br_list = res[1].split('\n')
        br_list.remove(br_list[0])
        [result.add("".join(i.split()).replace('origin/', '')) for i in br_list]

    # Revert current directory
    os.chdir(cur_dir)
    return result


def get_commit_information(pr_id, sha):

    # Save (temp) current directory
    cur_dir = os.getcwd()

    # Change current directory to repository
    os.chdir(config.GC_FOLDER + '/' + pr_id)

    # Get information from specific commit
    res_opt = 'git log --pretty=format:"%aE\n%at" --shortstat -1 ' + sha
    info_std = commands.getoutput(res_opt)
    commit = {}

    # Get author and timestamp
    if type(info_std) is str:
        info_std = info_std.split("\n")
        commit['email'] = info_std[0]
        commit['time'] = info_std[1]
        if len(info_std) > 2:
            info_std = info_std[2]
        else:
            info_std = ''
    else:
        info_std = ''

    # Create regular expression to search "number file pattern"
    __p = re.compile(r"\d+ file")
    __last = None

    # Find last occurrence
    for m in __p.finditer(info_std):
        __last = m

    # Check if it is not exist
    if __last is None:
        commit["files_changed"] = 0
        commit["lines_added"] = 0
        commit["lines_removed"] = 0

    # Files have been changed
    else:
        __p = __last.start()
        info_std = info_std[__p:]
        info_std = info_std.split(", ")
        if "files" not in info_std[0]:
            commit["files_changed"] = int(info_std[0].replace(" file changed",
                                                              ""))
        else:
            commit["files_changed"] = int(info_std[0].replace(" files changed",
                                                              ""))
        if len(info_std) > 1:
            if "insertion" in info_std[1]:
                if "insertions" not in info_std[1]:
                    commit["lines_added"] = int(info_std[1]
                                                .replace(" insertion(+)", ""))
                else:
                    commit["lines_added"] = int(info_std[1]
                                                .replace(" insertions(+)", ""))
            else:
                commit["lines_added"] = 0
                if "deletions" not in info_std[1]:
                    commit["lines_removed"] = int(info_std[1]
                                                  .replace(" deletion(-)", ""))
                else:
                    commit["lines_removed"] = int(info_std[1]
                                                  .replace(" deletions(-)", ""))
        if len(info_std) > 2:
            if "deletions" not in info_std[2]:
                commit["lines_removed"] = int(info_std[2]
                                              .replace(" deletion(-)", ""))
            else:
                commit["lines_removed"] = int(info_std[2]
                                              .replace(" deletions(-)", ""))
        else:
            commit["lines_removed"] = 0

    # Revert current directory
    os.chdir(cur_dir)

    return commit


def get_commits_from_branch(info, branch_name):

    # Save (temp) current directory
    cur_dir = os.getcwd()

    # Generate pseudo-name-id
    __pr_id = info.get('id')
    __br_id = 'origin/' + branch_name

    # Change current directory to repository
    os.chdir(config.GC_FOLDER + '/' + __pr_id)

    # Get List of Commits from specific branch
    res = commands.getstatusoutput('git log -b ' + __br_id +
                                   ' --pretty=oneline')
    commits = {}
    if res[0] == 0:

        # Parse and get information of Commits
        br_list = res[1].split('\n')
        [commits.update({i[:40]: i[41:]}) for i in br_list]

    # Revert current directory
    os.chdir(cur_dir)
    return commits
