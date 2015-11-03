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

import settings as config
import st_diff

__author__ = 'Alejandro F. Carrera'


# Add group (group registered at gitlab) to redis
# gr_id = group identifier at gitlab
# gr_info = information cleaned from gitlab
def save(self, gr_id, gr_info):

    # Generate pseudo-key-id
    __g_id = "g_" + str(gr_id)

    # Check if group exists at db
    if len(self.rd_instance_us.keys(__g_id)) == 0:

        # Save group and mark to active
        gr_info["state"] = "active"
        self.rd_instance_us.hmset("g_" + str(gr_id), gr_info)

        # Print alert
        if config.DEBUGGER:
            config.print_message("- Added Group: %d" % int(gr_id))

    # Group exists at redis
    else:

        # Get info at redis
        gr_rd = self.rd_instance_us.hgetall(__g_id)

        # Detect different information from two groups
        __new_group = st_diff.groups(gr_info, gr_rd)

        if __new_group is not None:

            # Generate new group
            self.rd_instance_us.hmset(__g_id, gr_info)

            # Print alert
            if config.DEBUGGER:
                config.print_message("- Updated Group: %d" % int(gr_id))


# Delete group (group registered at gitlab) at redis
# gr_id = group identifier at gitlab
def delete(self, gr_id):

    # Generate pseudo-key-id
    __g_id = "g_" + str(gr_id)

    # Set flag to deleted
    self.rd_instance_us.hset(__g_id, "state", "deleted")

    # Print alert
    if config.DEBUGGER:
        config.print_message("- Removed Group: %d" % int(gr_id))
