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
    if not os.path.exists(__pr_id):

        # Clone (mirror like bare repository)
        res = commands.getstatusoutput('git clone ' + __pr_url + ' ' + __pr_id)
        if res[0] == 0:
            config.print_message(' * [Worker] Success : Cloned - %s' % __pr_id)
        else:
            if 'Repository not found.' in res[1]:
                config.print_message(' * [Worker] Error : URL - %s' % __pr_id)
            else:
                config.print_message(' * [Worker] Error : Credentials - %s' % __pr_id)

    # Repository exists
    else:

        # Change current directory to repository
        os.chdir(config.GC_FOLDER + '/' + __pr_id)

        # Clone (mirror like bare repository)
        res = commands.getstatusoutput('git pull ' + __pr_url)
        if res[0] == 0:
            config.print_message(' * [Worker] Success : Pulled - %s' % __pr_id)
        else:
            if 'Repository not found.' in res[1]:
                config.print_message(' * [Worker] Error : URL - %s' % __pr_id)
            else:
                config.print_message(' * [Worker] Error : Credentials - %s' % __pr_id)

    # Revert current directory
    os.chdir(cur_dir)