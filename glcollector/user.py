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

import base64
import settings as config
import st_diff

__author__ = 'Alejandro F. Carrera'


# Add user (user registered at gitlab) to redis
# us_id = user identifier at gitlab
# us_info = information cleaned from gitlab
def save(self, us_id, us_info):

    # Generate pseudo-key-id
    __u_id = "u_" + str(us_id)

    # Check if user exists at non gitlab users
    if len(self.rd_instance_us.keys(__u_id)) == 0:

        # Save user and mark to active
        us_info["state"] = "active"
        self.rd_instance_us.hmset("u_" + str(us_id), us_info)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Added User: %d" % int(us_id))

    # User exists at redis
    else:

        # Get info at redis
        us_rd = self.rd_instance_us.hgetall(__u_id)

        # Detect different information from two users
        __new_user = st_diff.users(us_info, us_rd)

        if __new_user is not None:

            __new_user = us_info

            # Generate new user
            self.rd_instance_us.hmset(__u_id, __new_user)

            # Print alert
            if config.DEBUGGER:
                config.print_message("- Updated User: %d" % int(us_id))


# Delete user (user registered at gitlab) at redis
# us_id = user identifier at gitlab
def delete(self, us_id):

    # Generate pseudo-key-id
    __u_id = "u_" + str(us_id)

    # Check user exists
    if len(self.rd_instance_us.keys(__u_id)) > 0:

        # Remove from db
        self.rd_instance_us.delete(__u_id)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Removed User %d" % int(us_id))
