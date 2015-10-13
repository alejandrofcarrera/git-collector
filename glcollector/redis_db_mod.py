"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  This file is part of the Smart Developer Hub Project:
    http://www.smartdeveloperhub.org
  Center for Open Middleware
        http://www.centeropenmiddleware.com/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2015 Center for Open Middleware.
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
import commands
import base64
import json
import os
import settings as config
import parser, inject, sniff

__author__ = 'Alejandro F. Carrera'


# Update Functions

def user_from_gitlab(self, us_id, us_info):

    # Clean information about user
    parser.clean_info_user(us_info)

    # Get information from redis database
    us_info_rd = self.rd_instance_us.hgetall("users:" + str(us_id) + ":")

    # Generate new user with join
    new_user = parser.join_users(us_info, us_info_rd)

    if new_user is not None:
        self.rd_instance_us.hmset("users:" + str(us_id) + ":", us_info)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Updated User %d" % int(us_id))
