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
import hmac
import redis
import hashlib
import settings as config

__author__ = 'Alejandro F. Carrera'


def create_repository_id(prof):
    sig = ''
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
        c["r"] = redis_create_pool(config.GC_DB_RE)
        c["b"] = redis_create_pool(config.GC_DB_BR)
        c["c"] = redis_create_pool(config.GC_DB_CO)
        c["cb"] = redis_create_pool(config.GC_DB_BR_CO)
        c["cc"] = redis_create_pool(config.GC_DB_US_CO)
        return c
    except EnvironmentError as e:
        raise e


#########################################################


def check_git_username(username):
    return re.match('^\w[\w-]+$', username)


#########################################################


def get_repositories(redis_instance):
    r = redis_instance.get('r').keys("*")
    result = []
    [result.append(redis_instance.get('r').hgetall(i)) for i in r]
    return result


def set_repositories(redis_instance, parameters):
    r_id = create_repository_id({
        'URL': parameters.get('url')
    })
    if redis_instance.get('r').exists(r_id):
        raise Exception('Repository already exists')
    redis_instance.get('r').hmset(r_id, {
        'id': r_id,
        'url': parameters.get('url'),
        'user': parameters.get('user', None),
        'password': parameters.get('password', None)
    })
    return r_id


#########################################################


def get_repository(redis_instance, repository_id):
    if not redis_instance.get('r').exists(repository_id):
        raise Exception('Repository not found')

    return redis_instance.get('r').hgetall(repository_id)


def set_repository(redis_instance, repository_id, parameters):
    if not redis_instance.get('r').exists(repository_id):
        raise Exception('Repository not found')

    if 'url' in parameters:
        redis_instance.get('r').hset(
            repository_id, 'url', parameters.get('url')
        )

    if 'user' in parameters:
        redis_instance.get('r').hset(
            repository_id, 'user', parameters.get('user')
        )

    if 'password' in parameters:
        redis_instance.get('r').hset(
            repository_id, 'password', parameters.get('password')
        )


def del_repository(redis_instance, repository_id):
    if not redis_instance.get('r').exists(repository_id):
        raise Exception('Repository not found')

    redis_instance.get('r').delete(repository_id)
