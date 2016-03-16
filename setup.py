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

import os

from setuptools import setup, find_packages
from gitcollector import settings as config

__author__ = 'Alejandro F. Carrera'


def read(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()

setup(
    name=config.GC_NAME,
    version=config.GC_VERSION,
    author="Alejandro F. Carrera",
    author_email="alej4fc@gmail.com",
    description="Project to get data through the git protocol",
    license="Apache 2",
    keywords="inner-source collector git git-collector",
    url="https://github.com/alejandrofcarrera/git-collector",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    install_requires=['redis', 'flask', 'flask_negotiate', 'validators', 'pytest', 'pika'],
    scripts=['mgitcollector'],
    classifiers=[]
)
