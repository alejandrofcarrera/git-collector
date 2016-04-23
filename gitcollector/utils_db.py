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

import re
import uuid
import hmac
import redis
import base64
import hashlib
import settings as config

__author__ = 'Alejandro F. Carrera'


def create_repository_id():
    sig = ''
    prof = {
        'id': uuid.uuid1()
    }
    for key in sorted(prof.keys()):
        sig += '|%s=%s' % (key, prof[key])
    sig = hmac.new('collector|repository', sig.encode(), hashlib.sha1)
    return str(sig.hexdigest()).lower()


def create_branch_id_from_repository(repo_info, branch_name):
    if type(repo_info) is dict:
        return repo_info.get('id') + ':' + base64.b16encode(branch_name)
    else:
        return repo_info + ':' + base64.b16encode(branch_name)


def create_user_id_from_email(email):
    return base64.b16encode(email)


def create_commit_id_from_repo(repo_info, sha):
    return repo_info.get('id') + ':' + sha


#########################################################


def redis_create_pool(db):
    __redis_db = redis.ConnectionPool(
        host=config.GC_DB_IP,
        port=config.GC_DB_PORT,
        db=db,
        password=config.GC_DB_PASS
    )
    __redis_db = redis.Redis(connection_pool=__redis_db)
    try:
        __redis_db.client_list()
        return __redis_db
    except Exception as e:
        raise EnvironmentError(' * Redis configuration is not valid or it is not online')


def rd_connect():
    c = {}
    try:
        c['r'] = redis_create_pool(config.GC_DB_REPOSITORIES)
        c['u'] = redis_create_pool(config.GC_DB_REPOSITORIES_URL)
        c['b'] = redis_create_pool(config.GC_DB_BRANCHES)
        c['c'] = redis_create_pool(config.GC_DB_COMMITS)
        c['cb'] = redis_create_pool(config.GC_DB_BRANCH_COMMIT)
        c['cc'] = redis_create_pool(config.GC_DB_COMMITTER_COMMIT)
        return c
    except EnvironmentError as e:
        raise e


#########################################################


class CollectorException(Exception):
    pass


EXCEP_REPOSITORY_NOT_FOUND = {
    'msg': 'Repository does not exist.',
    'code': 404
}

EXCEP_COMMIT_NOT_FOUND = {
    'msg': 'Commit does not exist.',
    'code': 404
}

EXCEP_CONTRIBUTOR_NOT_FOUND = {
    'msg': 'Contributor does not exist.',
    'code': 404
}

EXCEP_BRANCH_NOT_FOUND = {
    'msg': 'Branch does not exist.',
    'code': 404
}

EXCEP_REPOSITORY_EXISTS = {
    'msg': 'Repository exists. Please update or remove it.',
    'code': 422
}

#########################################################


def check_git_username(username):
    return re.match('^\w[\w-]+$', username)


def check_url_exists(redis_instance, url):
    return redis_instance.get('u').exists(url)


#########################################################


def get_repositories(redis_instance):
    r = redis_instance.get('r').keys('*')
    if 'active' in r:
        r.remove('active')
    result = []
    [result.append(get_repository(redis_instance, i)) for i in r]
    return result


def get_repositories_active(redis_instance):
    if redis_instance.get('r').exists('active'):
        return redis_instance.get('r').smembers('active')
    return []


def set_repositories(redis_instance, parameters):
    if check_url_exists(redis_instance, parameters.get('url')):
            raise CollectorException(EXCEP_REPOSITORY_EXISTS)
    r_id = create_repository_id()
    r = {
        'id': r_id,
        'url': parameters.get('url'),
        'state': 'active' if 'state' not in parameters else parameters.get('state')
    }
    if 'user' in parameters:
        r['user'] = parameters.get('user')
    if 'password' in parameters:
        r['password'] = parameters.get('password')
    redis_instance.get('r').hmset(r_id, r)
    if r['state'] == 'active':
        redis_instance.get('r').sadd('active', r_id)
    redis_instance.get('u').set(r.get('url'), r_id)
    return r_id, r['state']


#########################################################


def get_repository(redis_instance, repository_id, with_password=False):
    if not redis_instance.get('r').exists(repository_id):
        raise CollectorException(EXCEP_REPOSITORY_NOT_FOUND)
    r = redis_instance.get('r').hgetall(repository_id)
    if not with_password and 'password' in r:
        del r['password']
    return r


def set_repository(redis_instance, repository_id, parameters):
    if not redis_instance.get('r').exists(repository_id):
        raise CollectorException(EXCEP_REPOSITORY_NOT_FOUND)

    r_data = redis_instance.get('r').hgetall(repository_id)

    if 'url' in parameters:
        if check_url_exists(redis_instance, parameters.get('url')):
            raise CollectorException(EXCEP_REPOSITORY_EXISTS)
        redis_instance.get('u').delete(r_data.get('url'))
        r_data['url'] = parameters.get('url')

    if 'user' in parameters:
        r_data['user'] = parameters.get('user')

    if 'password' in parameters:
        r_data['password'] = parameters.get('password')

    redis_instance.get('r').hmset(repository_id, r_data)
    redis_instance.get('u').set(r_data.get('url'), r_data.get('id'))


def act_repository(redis_instance, repository_id, state):
    if not redis_instance.get('r').exists(repository_id):
        raise CollectorException(EXCEP_REPOSITORY_NOT_FOUND)

    if state == 'nonactive':
        redis_instance.get('r').srem('active', repository_id)
    else:
        redis_instance.get('r').sadd('active', repository_id)
    redis_instance.get('r').hset(repository_id, 'state', state)


#########################################################

def get_commits_from_repository(redis_instance, repository_id):
    if not redis_instance.get('r').exists(repository_id):
        raise CollectorException(EXCEP_REPOSITORY_NOT_FOUND)

    res = set()
    commits = redis_instance.get('c').keys(repository_id + ':*')
    [res.add(x.split(':')[1]) for x in commits]
    return res


def get_commits_from_branch_id(redis_instance, repository_id, branch_id):
    if not redis_instance.get('r').exists(repository_id):
        raise CollectorException(EXCEP_REPOSITORY_NOT_FOUND)

    br_id = repository_id + ':' + branch_id
    if not redis_instance.get('b').exists(br_id):
        raise CollectorException(EXCEP_BRANCH_NOT_FOUND)

    res = set()
    commits = redis_instance.get('cb').zrange(br_id, 0, -1)
    [res.add(x.split(':')[1]) for x in commits]
    return res


def get_commit_from_repository(redis_instance, repository_id, commit_id):
    if not redis_instance.get('r').exists(repository_id):
        raise CollectorException(EXCEP_REPOSITORY_NOT_FOUND)

    co_id = repository_id + ':' + commit_id

    if not redis_instance.get('c').exists(co_id):
        raise CollectorException(EXCEP_COMMIT_NOT_FOUND)

    return redis_instance.get('c').hgetall(co_id)


def get_branches_from_repository(redis_instance, repository_id):
    if not redis_instance.get('r').exists(repository_id):
        raise CollectorException(EXCEP_REPOSITORY_NOT_FOUND)
    res = set()
    branches = redis_instance.get('b').keys(repository_id + ':*')
    [res.add(base64.b16decode(x.split(':')[1])) for x in branches]
    return res


def get_branch_from_repository(redis_instance, repository_id, branch_id):
    if not redis_instance.get('r').exists(repository_id):
        raise CollectorException(EXCEP_REPOSITORY_NOT_FOUND)

    br_id = repository_id + ':' + branch_id

    if not redis_instance.get('b').exists(br_id):
        raise CollectorException(EXCEP_BRANCH_NOT_FOUND)

    br = redis_instance.get('b').hgetall(br_id)
    br['contributors'] = eval(br.get('contributors'))
    return br


def get_branches_id_from_repository(redis_instance, repository_id):
    if not redis_instance.get('r').exists(repository_id):
        raise CollectorException(EXCEP_REPOSITORY_NOT_FOUND)

    res = set()
    branches = redis_instance.get('b').keys(repository_id + ':*')
    [res.add(x.split(':')[1]) for x in branches]
    return res


#########################################################


def get_repository_contributors(redis_instance, repository_id):
    if not redis_instance.get('r').exists(repository_id):
        raise CollectorException(EXCEP_REPOSITORY_NOT_FOUND)

    ret = []
    br_ids = [x.split(':')[1] for x in redis_instance.get('cb').keys(repository_id + ':*')]
    [ret.extend(get_contributors_from_branch_id(redis_instance, repository_id, x)) for x in br_ids]
    return set(ret)


def get_contributors_from_branch_id(redis_instance, repository_id, branch_id):
    if not redis_instance.get('r').exists(repository_id):
        raise CollectorException(EXCEP_REPOSITORY_NOT_FOUND)

    br_id = repository_id + ':' + branch_id

    if not redis_instance.get('b').exists(br_id):
        raise CollectorException(EXCEP_BRANCH_NOT_FOUND)

    return eval(redis_instance.get('b').hget(br_id, 'contributors'))


def get_contributors(redis_instance):
    return redis_instance.get('cc').keys('*')


def get_contributor(redis_instance, contributor_id):
    if not redis_instance.get('cc').exists(contributor_id):
        raise CollectorException(EXCEP_CONTRIBUTOR_NOT_FOUND)

    us = {
        'email': base64.b16decode(contributor_id)
    }
    com = redis_instance.get('cc').zrange(
        contributor_id, 0, -1, withscores=True
    )
    us['commits'] = len(com)
    if len(com):
        us['first_commit_at'] = str(long(com[0][1]))
        us['last_commit_at'] = str(long(com[-1][1]))

    return us


#########################################################


def inject_branch_commits(redis_instance, branch_id, commits):
    if redis_instance.get('cb').exists(branch_id):
        redis_instance.get('cb').delete(branch_id)

    commits_push = []
    com_tmp = []
    [com_tmp.extend([k, v]) for k, v in commits.items()]

    c = 0
    for i in com_tmp:
        if c == 10000:
            redis_instance.get('cb').zadd(branch_id, *commits_push)
            commits_push = [i]
            c = 1
        else:
            commits_push.append(i)
            c += 1
    redis_instance.get('cb').zadd(branch_id, *commits_push)


def inject_user_commits(redis_instance, user_id, commits):

    commits_push = []
    com_tmp = []
    [com_tmp.extend([k, v]) for k, v in commits.items()]

    c = 0
    for i in com_tmp:
        if c == 10000:
            redis_instance.get('cc').zadd(user_id, *commits_push)
            commits_push = [i]
            c = 1
        else:
            commits_push.append(i)
            c += 1
    redis_instance.get('cc').zadd(user_id, *commits_push)


def del_branches_from_id(redis_instance, repository_id, branch_name):

    # Generate ID with Base64
    br_id = create_branch_id_from_repository(repository_id, branch_name)

    # Temporal save
    br_con = eval(redis_instance.get('b').hget(br_id, 'contributors'))

    # Delete containers at redis
    redis_instance.get('b').delete(br_id)
    redis_instance.get('cb').delete(br_id)

    commits_to_del = set()

    # Remove links with contributors
    for i in br_con:
        us_com = redis_instance.get('cc').smembers(i)
        br_com = filter(lambda x: str(x).startswith(br_id), us_com)
        [commits_to_del.add(
            str(x).split(':')[0] + ':' + str(x).split(':')[2]
        ) for x in br_com]
        redis_instance.get('cc').srem(i, *commits_to_del)

    return commits_to_del


def get_commits_from_branch(redis_instance, repository_id, branch_name):
    br_id = create_branch_id_from_repository(repository_id, branch_name)
    result = {}
    if redis_instance.get('cb').exists(br_id):
        result_tmp = dict(redis_instance.get('cb').zrange(
            br_id, 0, -1, withscores=True)
        )
        result = {}
        [result.update({
            x.replace(repository_id + ':', ''): result_tmp[x]
        }) for x in result_tmp.keys()]
    return result


def del_commits_from_repository(redis_instance, repository_id, comm_list):
    branch_co = set()
    branches = redis_instance.get('b').keys(repository_id + ':*')
    for i in branches:
        branch_co = branch_co.union(
            set(redis_instance.get('cb').zrange(i, 0, -1))
        )
    com = list(filter(lambda x: x not in branch_co, comm_list))
    redis_instance.get('c').delete(*com)
