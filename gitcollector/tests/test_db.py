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
import gitcollector.utils_db as db

__author__ = 'Alejandro F. Carrera'

red = None


# Must be passed unless all tests will fail
def test_config_good():
    global red
    red_k = ['r', 'u', 'b', 'c', 'cb', 'cc']
    red_k = set(red_k)
    try:
        red = db.rd_connect()
        [red[i].flushdb() for i in red]
    except EnvironmentError as e:
        red = None
    assert isinstance(red, dict)
    red_keys = set(red.keys())
    assert not len(red_keys.difference(red_k))


def test_no_repositories():
    global red
    rep = db.get_repositories(red)
    assert not len(rep)


def test_no_active_repositories():
    global red
    rep = db.get_repositories_active(red)
    assert not len(rep)


def test_get_bad_repository_id():
    global red
    with pytest.raises(db.CollectorException):
        db.get_repository(red, 'a')


def test_set_bad_repository_id():
    global red
    with pytest.raises(db.CollectorException):
        db.set_repository(red, 'a', None)


def test_active_bad_repository_id():
    global red
    with pytest.raises(db.CollectorException):
        db.act_repository(red, 'a', None)



