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
import utils_git
import threading
import utils_db


__author__ = 'Alejandro F. Carrera'


def print_running():
    config.print_message(' * [Worker] Started')


def print_finishing():
    config.print_message(' * [Worker] Finished')


def print_finish_task(repository_id):
    config.print_message(' * [Worker] %s : Reviewed' % repository_id)


#########################################################


def get_branches_from_repository(redis_instance, rep_info):

    # Get Branches saved at redis
    br_rd_list = utils_db.get_branches_from_repository(
        redis_instance, rep_info.get('id')
    )

    # Get Branches from Git Commands
    br_git_list = utils_git.get_branches_from_repository(rep_info)

    # Get Branches to Update or Delete
    mt_diff = br_git_list.difference(br_rd_list)
    mt_int = br_git_list.intersection(br_rd_list)
    mt_mod = list(mt_diff.union(mt_int))
    mt_del = list(br_rd_list.difference(br_git_list))
    mt_cont = len(mt_del) + len(mt_mod)

    config.print_message(' * [Worker] ' + ' %3d B: %3d - | %3d +' % (
        mt_cont, len(mt_del), len(mt_mod)
    ))
    return {'delete': mt_del, 'update': mt_mod}


def get_commits_from_branch(redis_instance, rep_info, branch_name):

    # Get Commits saved at redis
    co_rd_dict = utils_db.get_commits_from_branch(
        redis_instance, rep_info.get('id'), branch_name
    )

    # Get Commits from git commands
    co_git_dict = utils_git.get_commits_from_branch(
        rep_info, branch_name
    )

    # Get commits to update, delete or add
    co_git_ids = set(co_git_dict.keys())
    co_rd_ids = set(co_rd_dict.keys())
    mt_new = co_git_ids.difference(co_rd_ids)
    mt_del = co_rd_ids.difference(co_git_ids)
    mt_mod = co_git_ids.intersection(co_rd_ids)
    mt_cont = len(mt_new) + len(mt_mod) + len(mt_del)

    config.print_message(' * [Worker] ' + ' %3d C: %3d - | %3d +' % (
        mt_cont, len(mt_del), (len(mt_new) + len(mt_mod))
    ))
    return {
        'add': mt_new, 'delete': mt_del, 'add_info': co_git_dict,
        'update': mt_mod, 'info': co_rd_dict
    }


#########################################################


def del_commits_from_branches(redis_instance, rep_info, branches):
    commits_to_del = set()

    # Get commits and delete links from branches
    for i in branches:
        com_br_del = utils_db.del_branches_from_id(
            redis_instance, rep_info.get('id'), i
        )
        commits_to_del = commits_to_del.union(com_br_del)

    # Remove all unique commits
    if len(commits_to_del) > 0:
        utils_db.del_commits_from_repository(
            redis_instance, rep_info.get('id'), commits_to_del
        )


def upd_commits_from_branches(redis_instance, rep_info, branches):

    for i in branches:

        # Generate branch id
        br_id = utils_db.create_branch_id_from_repository(rep_info, i)

        # Get commits from branch
        # ids (sha) and old data structure
        com_br_upd = get_commits_from_branch(
            redis_instance, rep_info, i
        )
        com_br = {}
        com_br_new = {}
        br_info_col = set()
        new_ids = com_br_upd.get('add')
        new_info = com_br_upd.get('add_info')
        old_info = com_br_upd.get('info')
        mod_info = com_br_upd.get('update')
        del_info = com_br_upd.get('delete')

        # Get old commits to create structure
        if len(old_info.keys()):
            [com_br.update({i: long(old_info[i])}) for i in mod_info]

        # Delete old structure of commits
        if len(new_ids) > 0 or len(del_info) > 0:
            redis_instance.get('cb').delete(br_id)

        # Update or add commits to redis
        for j in new_ids:

            # Generate commit id
            co_id = utils_db.create_commit_id_from_repo(rep_info, j)

            # Get email from commit and add as contributor
            co_info = utils_git.get_commit_information(rep_info.get('id'), j)
            co_info['sha'] = j
            co_info['title'] = new_info.get(j)
            co_em = co_info.get('email').lower()
            user_key = utils_db.create_user_id_from_email(co_em)
            co_info['author'] = user_key
            br_info_col.add(user_key)

            # Insert commit information
            if not redis_instance.get('c').exists(co_id):
                redis_instance.get('c').hmset(co_id, co_info)

            # Set values at Redis Structure - Branch (id + timestamp)
            com_br.update({co_id: co_info.get('time')})

            if user_key not in com_br_new:
                com_br_new[user_key] = {}
            com_br_new[user_key].update({br_id + ':' + j: co_info.get('time')})

        if len(new_ids):

            # Set values at Redis Structure - Users
            for i in com_br_new:
                utils_db.inject_user_commits(redis_instance, i, com_br_new[i])

        # Delete commits from redis
        for j in del_info:

            # Get commit identifier (sha) + info
            co_info = redis_instance.get('c').hgetall(j)

            # Get email from commit and add as contributor
            co_em = co_info.get('email').lower()
            user_key = utils_db.create_user_id_from_email(co_em)
            redis_instance.get('cc').zrem(user_key, br_id + ':' + j)

        # Check if contributors keep being same
        if len(del_info):
            col_tmp = br_info_col.copy()
            for j in br_info_col:
                br_us_co = redis_instance.get('cc').zrange(j, 0, -1)
                br_com = filter(lambda x: str(x).startswith(br_id), br_us_co)
                if not len(br_com):
                    col_tmp.remove(i)
            br_info_col = col_tmp

        # Inject commits to branch from data structure filled
        if len(new_ids) or len(del_info):
            utils_db.inject_branch_commits(redis_instance, br_id, com_br)

        # Insert information to branch
        redis_instance.get('b').hmset(br_id, {
            'name': i,
            'contributors': br_info_col
        })


#########################################################


class CollectorTask(object):

    def __init__(self, redis_instance):
        self.thread = None
        self.data = None
        self.rd = redis_instance
        self.list = None

    def start(self):
        if self.thread is not None:
            if self.thread.isAlive():
                print_running()
        self.thread = threading.Thread(target=self.start_worker)
        self.thread.start()
        print_running()

    def status(self):
        if self.thread is None:
            return 'not_started'
        else:
            if self.thread.isAlive():
                return 'running'
            else:
                return 'finished'

    def start_worker(self):
        if self.list is not None:
            rep_active = self.list
        else:
            rep_active = utils_db.get_repositories_active(self.rd)
        for i in rep_active:
            rep_info = utils_db.get_repository(self.rd, i, True)
            st = utils_git.repository_clone(rep_info)
            if st == 0:
                br = get_branches_from_repository(self.rd, rep_info)
                del_commits_from_branches(self.rd, rep_info, br.get('delete'))
                upd_commits_from_branches(self.rd, rep_info, br.get('update'))
            print_finish_task(rep_info.get('id'))
        print_finishing()
