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

import pytest
import gitcollector.settings as se
import gitcollector.utils_db as db

__author__ = 'Alejandro F. Carrera'


#########################################################


red = None
rep = 'https://github.com/dear-github/dear-github.git'


#########################################################


def clear_database():
    [red[i].flushdb() for i in red]


#########################################################


# Must be passed unless all tests will fail
def test_config_good():
    global red
    red_dbs = [
        se.GC_DB_REPOSITORIES,
        se.GC_DB_REPOSITORIES_URL,
        se.GC_DB_BRANCHES,
        se.GC_DB_COMMITS,
        se.GC_DB_BRANCH_COMMIT,
        se.GC_DB_COMMITTER_COMMIT
    ]
    red_dbs = set(red_dbs)

    # Test if each database has different
    # database number to create connection
    assert len(red_dbs) == 6

    # Test redis connection
    # and clean all databases
    try:
        red = db.rd_connect()
        clear_database()
    except EnvironmentError as e:
        red = None
    assert isinstance(red, dict)

    # Test if each database connection has
    # been created successfully
    red_k = ['r', 'u', 'b', 'c', 'cb', 'cc']
    red_k = set(red_k)
    red_keys = set(red.keys())
    assert not len(red_keys.difference(red_k))


def test_no_repositories():

    # Test redis is connected
    assert isinstance(red, dict)

    # Test there are not repositories
    rep_list = db.get_repositories(red)
    assert not len(rep_list)


def test_no_active_repositories():

    # Test redis is connected
    assert isinstance(red, dict)

    # Test there are not active repositories
    rep_list = db.get_repositories_active(red)
    assert not len(rep_list)


def test_get_bad_repository_id():

    # Test redis is connected
    assert isinstance(red, dict)

    # Test raise Exception at get repository
    # using identifier not valid
    with pytest.raises(db.CollectorException):
        db.get_repository(red, 'a')


def test_set_bad_repository_id():

    # Test redis is connected
    assert isinstance(red, dict)

    # Test raise Exception at set repository
    # parameter using identifier not valid
    with pytest.raises(db.CollectorException):
        db.set_repository(red, 'a', None)


def test_active_bad_repository_id():

    # Test redis is connected
    assert isinstance(red, dict)

    # Test raise Exception at activate repository
    with pytest.raises(db.CollectorException):
        db.act_repository(red, 'a', None)


def test_create_active_repository():

    # Test redis is connected
    assert isinstance(red, dict)

    rep_id, rep_st = db.set_repositories(red, {
        'url': rep
    })
    rep_info_waited = {
        'url': rep, 'state': 'active', 'id': rep_id
    }

    # Test identifier has been created and
    # it is a string and not empty
    assert isinstance(rep_id, str)
    assert rep_id != ''

    # Test repository state is active
    assert rep_st == 'active'

    # Test repository info is the same at redis side
    rep_info = db.get_repository(red, rep_id)
    assert cmp(rep_info, rep_info_waited) == 0
    rep_info = db.get_repository(red, rep_id, True)
    assert cmp(rep_info, rep_info_waited) == 0

    # Test this repository is the one alive
    rep_info = db.get_repositories(red)
    assert len(rep_info) == 1
    rep_info = rep_info[0]
    assert cmp(rep_info, rep_info_waited) == 0

    # Test this repository is the one active
    rep_info = db.get_repositories_active(red)
    assert len(rep_info) == 1
    rep_info = rep_info.pop()
    assert rep_info == rep_id


def test_set_exist_url_repository():

    # Test redis is connected
    assert isinstance(red, dict)

    rep_info = db.get_repositories(red)
    assert len(rep_info) == 1
    rep_info = rep_info[0]

    # Test raise Exception at save an url
    # has been already saved at redis
    with pytest.raises(db.CollectorException):
        db.set_repository(red, rep_info.get('id'), {
            'url': rep_info.get('url')
        })


def test_set_parameters_repository():

    # Test redis is connected
    assert isinstance(red, dict)

    rep_id = db.get_repositories_active(red)
    assert len(rep_id) == 1
    rep_id = rep_id.pop()
    db.set_repository(red, rep_id, {
        'user': 'usertest',
        'password': 'passwordtest',
        'key_not_valid': 'garbage',
        'state': 'nonactive'
    })
    rep_info = db.get_repository(red, rep_id)

    # Test key_not_valid is not at redis
    assert 'key_not_valid' not in rep_info

    # Test password has not been returned by method
    assert 'password' not in rep_info

    # Test repository state is active
    assert rep_info.get('state') == 'active'

    # Test user has been saved successfully
    assert rep_info.get('user') == 'usertest'

    # Test password has been returned by method
    rep_info = db.get_repository(red, rep_id, True)
    assert rep_info.get('password') == 'passwordtest'


def test_deactivate_repository():

    # Test redis is connected
    assert isinstance(red, dict)
    rep_id = db.get_repositories_active(red)
    assert len(rep_id) == 1
    rep_id = rep_id.pop()
    db.act_repository(red, rep_id, 'nonactive')

    # Test there are no active repositories
    rep_id = db.get_repositories_active(red)
    assert len(rep_id) == 0
    clear_database()


def test_create_nonactive_repository():

    # Test redis is connected
    assert isinstance(red, dict)
    rep_id, rep_st = db.set_repositories(red, {
        'url': rep,
        'state': 'nonactive'
    })
    rep_info_waited = {
        'url': rep, 'state': 'nonactive', 'id': rep_id
    }

    # Test identifier has been created and
    # it is a string and not empty
    assert isinstance(rep_id, str)
    assert rep_id != ''

    # Test repository state is active
    assert rep_st == 'nonactive'

    # Test repository info is the same at redis side
    rep_info = db.get_repository(red, rep_id)
    assert cmp(rep_info, rep_info_waited) == 0
    rep_info = db.get_repository(red, rep_id, True)
    assert cmp(rep_info, rep_info_waited) == 0

    # Test this repository is the one alive
    rep_info = db.get_repositories(red)
    assert len(rep_info) == 1
    rep_info = rep_info[0]
    assert cmp(rep_info, rep_info_waited) == 0

    # Test there are no active repositories
    rep_info = db.get_repositories_active(red)
    assert len(rep_info) == 0
    clear_database()
