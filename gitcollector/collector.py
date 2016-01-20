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

from flask import request, make_response, Flask
from flask_negotiate import produces, consumes
import settings as config
import utils_http
import utils_db
import json

__author__ = 'Alejandro F. Carrera'


class Collector(object):

    # Collector constructor
    def __init__(self, ip, port, pwd):
        self.ip = ip
        self.port = port
        self.password = pwd
        self.app = Flask(__name__)
        try:
            self.rd = utils_db.rd_connect()
        except EnvironmentError as e:
            raise e

        # Root path (same as /api)
        @self.app.route('/', methods=['GET'])
        @produces('application/json')
        def root():
            return api()

        # Get information about Collector
        @self.app.route('/api', methods=['GET'])
        @produces('application/json')
        def api():
            return make_response(json.dumps({
                "Name": config.GC_LONGNAME,
                "Version": config.GC_VERSION,
                "Password": config.GC_USE_PASSWORD
            }), 200)

        # Get and update information about repositories
        @self.app.route('/api/repositories', methods=['GET', 'POST'])
        @produces('application/json')
        @consumes('application/json')
        def repositories():

            # Check Password is mandatory and valid
            try:
                utils_http.check_password(request, self.password)
            except Exception as c1:
                return utils_http.generate_pwd_error()

            if request.method == 'GET':
                return make_response(json.dumps(
                    utils_db.get_repositories(self.rd)
                ), 200)
            else:

                # Check if JSON is available
                try:
                    param = request.json
                except Exception as c2:
                    return utils_http.generate_json_error()
                if 'url' not in param:
                    return utils_http.generate_json_error()

                # Check if URL is valid
                if not utils_http.check_url(param.get('url')):
                    return utils_http.generate_json_error()

                # Check if Username is available and valid
                if 'user' in param:
                    if not utils_db.check_git_username(param.get('user')):
                        return utils_http.generate_json_error()

                # Check if state is available and valid
                if 'state' in param:
                    if param.get('state') != 'active' and param.get('state') != 'nonactive':
                        return utils_http.generate_json_error()

                # Save repository at redis
                try:
                    r_id = utils_db.set_repositories(self.rd, param)
                    return make_response(json.dumps({
                        "URL": param.get('url'),
                        "ID": r_id,
                        "Status": "Added"
                    }), 201)
                except utils_db.CollectorException as c3:
                    return utils_http.generate_repo_error(
                        c3.args[0].get('msg'), c3.args[0].get('code')
                    )

        # Get and Update Repository
        @self.app.route('/api/repositories/<string:r_id>', methods=['GET', 'PUT'])
        @produces('application/json')
        @consumes('application/json')
        def repository(r_id):

            # Check Password is mandatory and valid
            try:
                utils_http.check_password(request, self.password)
            except Exception as c4:
                return utils_http.generate_pwd_error()

            if request.method == 'GET':
                try:
                    return make_response(json.dumps(
                        utils_db.get_repository(self.rd, r_id)
                    ), 200)
                except Exception as c5:
                    return utils_http.generate_repo_error(
                        c5.args[0].get('msg'), c5.args[0].get('code')
                    )

            else:

                if request.method == 'PUT':

                    # Check if JSON is available
                    try:
                        param = request.json
                    except Exception as c6:
                        return utils_http.generate_json_error()

                    # Check if URL is valid
                    if 'url' in param:
                        if not utils_http.check_url(param.get('url')):
                            return utils_http.generate_json_error()

                    # Check if Username is available and valid
                    if 'user' in param:
                        if not utils_db.check_git_username(param.get('user')):
                            return utils_http.generate_json_error()

                    try:
                        utils_db.set_repository(self.rd, r_id, param)
                        return make_response(json.dumps({
                            "ID": r_id,
                            "Status": "Updated"
                        }))

                    # Catch exception
                    except Exception as c7:
                        return utils_http.generate_repo_error(
                            c7.args[0].get('msg'), c7.args[0].get('code')
                        )

        # De/activate Repository
        @self.app.route('/api/repositories/<string:r_id>/state', methods=['POST'])
        @produces('application/json')
        @consumes('application/json')
        def repository_activation(r_id):

            # Check Password is mandatory and valid
            try:
                utils_http.check_password(request, self.password)
            except Exception as c8:
                return utils_http.generate_pwd_error()

            try:
                param = request.json
            except Exception as c9:
                return utils_http.generate_json_error()

            # Check if state is valid
            if 'state' not in param:
                return utils_http.generate_json_error()
            st = param.get('state')
            if st != 'active' and st != 'nonactive':
                return utils_http.generate_json_error()

            try:
                utils_db.act_repository(self.rd, r_id, st)
                return make_response(json.dumps({
                    "ID": r_id,
                    "Status": "Activated" if st == 'active' else 'Deactivated'
                }))

            # Catch exception
            except Exception as c10:
                return utils_http.generate_repo_error(
                    c10.args[0].get('msg'), c10.args[0].get('code')
                )