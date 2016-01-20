"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  This file is part of the Smart Developer Hub Project:
    http://www.smartdeveloperhub.org
  Center for Open Middleware
        http://www.centeropenmiddleware.com/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2016 Center for Open Middleware.
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

import re
import uuid
import hmac
import redis
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
        raise EnvironmentError(" * Redis configuration is not valid or it is not online")


def rd_connect():
    c = {}
    try:
        c["r"] = redis_create_pool(config.GC_DB_REPOSITORIES)
        c["b"] = redis_create_pool(config.GC_DB_BRANCHES)
        c["c"] = redis_create_pool(config.GC_DB_COMMITS)
        c["cb"] = redis_create_pool(config.GC_DB_BRANCH_COMMIT)
        c["cc"] = redis_create_pool(config.GC_DB_COMMITTER_COMMIT)
        return c
    except EnvironmentError as e:
        raise e


#########################################################


class CollectorException(Exception):
    pass


EXCEP_REPOSITORY_NOT_FOUND = {
    'msg': "Repository does not exist.",
    'code': 404
}

EXCEP_REPOSITORY_EXISTS = {
    'msg': "Repository exists. Please update or remove it.",
    'code': 422
}

#########################################################


def check_git_username(username):
    return re.match('^\w[\w-]+$', username)


def check_url_exists(redis_instance, url):
    r = redis_instance.get('r').keys("*")
    if 'active' in r:
        r.remove('active')
    for i in r:
        return redis_instance.get('r').hgetall(i).get('url') == url
    return False

#########################################################


def get_repositories(redis_instance):
    r = redis_instance.get('r').keys("*")
    if 'active' in r:
        r.remove('active')
    result = []
    [result.append(get_repository(redis_instance, i)) for i in r]
    return result


def set_repositories(redis_instance, parameters):
    r_id = create_repository_id()
    if check_url_exists(redis_instance, parameters.get('url')):
        raise CollectorException(EXCEP_REPOSITORY_EXISTS)
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
    redis_instance.get('r').sadd('active', r_id)
    return r_id


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
        r_data['url'] = parameters.get('url')

    if 'user' in parameters:
        r_data['user'] = parameters.get('user')

    if 'password' in parameters:
        r_data['password'] = parameters.get('password')

    redis_instance.get('r').hmset(repository_id, r_data)


def act_repository(redis_instance, repository_id, state):
    if not redis_instance.get('r').exists(repository_id):
        raise CollectorException(EXCEP_REPOSITORY_NOT_FOUND)

    if state == 'nonactive':
        redis_instance.get('r').srem('active', repository_id)
    else:
        redis_instance.get('r').sadd('active', repository_id)
    redis_instance.get('r').hset(repository_id, 'state', state)
