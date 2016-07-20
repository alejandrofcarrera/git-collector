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

from flask import make_response
import settings as config
import validators
import json

__author__ = 'Alejandro F. Carrera'


def json_response(json_object, state=200):
    obj = json_object
    if isinstance(obj, set):
        obj = list(obj)
    r = make_response(json.dumps(obj), state)
    r.headers['Content-Type'] = 'application/json'
    return r


def generate_pwd_error():
    return json_response({
        "Error": "Password is not valid."
    }, 401)


def generate_ctype_error():
    return json_response({
        "Error": "The server does not support the media type transmitted in"
                 "the request."
    }, 415)


def generate_json_error():
    return json_response({
        "Error": "JSON at request body is bad format."
    }, 422)


def generate_repo_error(msg, status):
    return json_response({
        "Error": msg
    }, status)


#########################################################


def check_url(url):
    try:
        return validators.url(url)
    except validators.ValidationFailure:
        return False


def check_password(req, pwd):

    # Check Password is available at Headers
    if config.GC_USE_PASSWORD and 'X-GC-PWD' not in req.headers:
        raise StandardError('Password is not valid')

    # Check Password is valid
    if config.GC_USE_PASSWORD and 'X-GC-PWD' in req.headers:
        if pwd != req.headers.get('X-GC-PWD'):
            raise StandardError('Password is not valid')
