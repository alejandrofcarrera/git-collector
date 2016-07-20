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

import threading

import settings as config
import utils_db
import utils_git
from gitcollector import utils_amqp


__author__ = 'Alejandro F. Carrera'


def print_running():
    config.print_message(' * [Worker] Started')


def print_finishing():
    config.print_message(' * [Worker] Finished')


def print_finish_task(repository_id):
    config.print_message(' * [Worker] %s : Reviewed' % repository_id)

#########################################################


class CollectorTask(object):

    def __init__(self, redis_instance, event_manager):
        self.thread = None
        self.data = None
        self.rd = redis_instance
        self.list = None
        self.event_manager = event_manager

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
            if st >= 0:
                if st == 0:
                    event = utils_amqp.RepositoryCreatedEvent([rep_info['id']])
                    self.event_manager.add_event(event)
                br = self.get_branches_from_repository(rep_info)
                self.del_commits_from_branches(rep_info, br.get('delete'))
                self.upd_commits_from_branches(rep_info, br.get('update'))
            print_finish_task(rep_info.get('id'))
        print_finishing()

    #########################################################

    def get_branches_from_repository(self, rep_info):

        # Get Branches saved at redis
        br_rd_list = utils_db.get_branches_from_repository(
            self.rd, rep_info.get('id')
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

    def get_commits_from_branch(self, rep_info, branch_name):

        # Get Commits saved at redis
        co_rd_dict = utils_db.get_commits_from_branch(
            self.rd, rep_info.get('id'), branch_name
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

    def del_commits_from_branches(self, rep_info, branches):
        commits_to_del = set()

        # Get commits and delete links from branches
        for i in branches:

            # Notification for deleted branches
            event = utils_amqp.RepositoryUpdatedEvent(rep_info['id'],
                                                      'deletedBranches',
                                                      i)
            self.event_manager.add_event(event)
            com_br_del = utils_db.del_branches_from_id(
                self.rd, rep_info.get('id'), i
            )
            commits_to_del = commits_to_del.union(com_br_del)

        # Remove all unique commits
        if len(commits_to_del) > 0:

            # Notification for deleted commits
            event = utils_amqp.RepositoryUpdatedEvent(rep_info['id'],
                                                      'deletedCommits',
                                                      commits_to_del)
            self.event_manager.add_event(event)
            utils_db.del_commits_from_repository(
                self.rd, rep_info.get('id'), commits_to_del
            )

    def upd_commits_from_branches(self, rep_info, branches):

        for i in branches:

            # Generate branch id
            br_id = utils_db.create_branch_id_from_repository(rep_info, i)

            # Get old information
            if not self.rd.get('b').exists(br_id):

                # Notification for new branches:
                event = utils_amqp.RepositoryUpdatedEvent(rep_info['id'],
                                                          'newBranches',
                                                          [br_id.split(':')[1]])
                self.event_manager.add_event(event)
                br_info_col = set()
            else:
                br_info_col = set(eval(
                    self.rd.get('b').hgetall(br_id).get('contributors')
                ))

            # Get commits from branch
            # ids (sha) and old data structure
            com_br_upd = self.get_commits_from_branch(rep_info, i)
            com_br = {}
            com_br_new = {}
            new_ids = com_br_upd.get('add')
            new_info = com_br_upd.get('add_info')
            old_info = com_br_upd.get('info')
            mod_info = com_br_upd.get('update')
            del_info = com_br_upd.get('delete')

            # Get old commits to create structure
            if len(old_info.keys()):
                [com_br.update({j: long(old_info[j])}) for j in mod_info]

            # Delete old structure of commits
            if len(new_ids) > 0 or len(del_info) > 0:
                self.rd.get('cb').delete(br_id)

            # Update or add commits to redis
            for j in new_ids:

                # Generate commit id
                co_id = utils_db.create_commit_id_from_repo(rep_info, j)

                # Get email from commit and add as contributor
                co_info = utils_git.get_commit_information(rep_info.get('id'),
                                                           j)
                co_info['sha'] = j
                co_info['title'] = new_info.get(j)
                co_em = co_info.get('email').lower()
                user_key = utils_db.create_user_id_from_email(co_em)
                co_info['author'] = user_key
                br_info_col.add(user_key)

                # Insert commit information
                if not self.rd.get('c').exists(co_id):
                    self.rd.get('c').hmset(co_id, co_info)

                # Set values at Redis Structure - Branch (id + timestamp)
                com_br.update({co_id: co_info.get('time')})

                if user_key not in com_br_new:
                    com_br_new[user_key] = {}
                com_br_new[user_key].update(
                    {br_id + ':' + j: co_info.get('time')})

            if len(com_br_new):
                contributors = set(com_br_new.keys())
                new_commiters = contributors.difference(
                    utils_db.get_contributors(self.rd))
                # Notification for new commiters
                event = utils_amqp.CommitterCreatedEvent(new_commiters)
                self.event_manager.add_event(event)

                # Notification for contributors
                event = utils_amqp.RepositoryUpdatedEvent(rep_info['id'],
                                                          'contributors',
                                                          contributors)
                self.event_manager.add_event(event)

            # Set values at Redis Structure - Users
            if len(new_ids):

                # Notification for new Commits
                event = utils_amqp.RepositoryUpdatedEvent(rep_info['id'],
                                                          'newCommits', new_ids)
                self.event_manager.add_event(event)

                for j in com_br_new:
                    utils_db.inject_user_commits(self.rd, j, com_br_new[j])

            # Delete commits from redis
            for j in del_info:

                # Generate commit id
                co_id = utils_db.create_commit_id_from_repo(rep_info, j)

                # Get commit identifier (sha) + info
                co_info = self.rd.get('c').hgetall(co_id)

                # Get email from commit and add as contributor
                co_em = co_info.get('email').lower()
                user_key = utils_db.create_user_id_from_email(co_em)
                self.rd.get('cc').zrem(user_key, br_id + ':' + j)

            # Check if contributors keep being same
            if len(del_info):
                col_tmp = br_info_col.copy()
                for j in br_info_col:
                    br_us_co = self.rd.get('cc').zrange(j, 0, -1)
                    br_com = filter(lambda x: str(x).startswith(br_id),
                                    br_us_co)
                    if not len(br_com):
                        col_tmp.remove(j)
                br_info_col = col_tmp

            # Inject commits to branch from data structure filled
            if len(new_ids) or len(del_info):
                utils_db.inject_branch_commits(self.rd, br_id, com_br)

            # Insert information to branch
                self.rd.get('b').hmset(br_id, {
                    'name': i,
                    'contributors': list(br_info_col)
                })
