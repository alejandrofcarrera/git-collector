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

from pika.exceptions import ChannelClosed, ConnectionClosed
from pika.spec import BasicProperties
import settings as config
import pika
import json

__author__ = 'Alejandro F. Carrera'


def print_sent(e):
    config.print_message(' * [Worker] [AMQP] Sent ' + e + ' Notification')


def print_error_amqp():
    config.print_error(' * [Worker] AMQP configuration is not valid or it is not online')


def send(message, event):
    try:
        connection_params = pika.ConnectionParameters(
            host=config.GC_AMQP_BROKER_HOST,
            port=config.GC_AMQP_BROKER_PORT
        )
        connection = pika.BlockingConnection(connection_params)
    except ConnectionClosed as e:
        print_error_amqp()
        return

    try:
        channel = connection.channel()
        routing_key = 'gitcollector.notification.' + event
        channel.confirm_delivery()
        sent = channel.basic_publish(
            exchange=config.GC_AMQP_EXCNAME,
            routing_key=routing_key,
            body=str(json.dumps(message)),
            properties=BasicProperties({}),
            mandatory=True
        )
        if not sent:
            print_error_amqp()
        else:
            print_sent(event)
    except ChannelClosed:
        print_error_amqp()
    finally:
        connection.close()
