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

import os

from setuptools import setup, find_packages
from glcollector import settings as config

__author__ = 'Alejandro F. Carrera'


def read(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()

setup(
    name=config.NAME,
    version=config.VERSION,
    author="Alejandro F. Carrera",
    author_email="alejandro.fernandez.carrera@centeropenmiddleware.com",
    description="A project for Gitlab Collector Service",
    license="Apache 2",
    keywords="inner-source collector gl-enhancer",
    url="https://github.com/SmartDeveloperHub/gitlab-collector",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    install_requires=['gl-api', 'redis', 'flask', 'flask_negotiate', 'python-dateutil'],
    classifiers=[],
    scripts=['collector']
)