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
import threading
import time
from pika.exceptions import ChannelClosed, ConnectionClosed
from pika.spec import BasicProperties
import settings as config
import pika
import json

__author__ = 'Ignacio Molina Cuquerella & Alejandro F. Carrera'


def print_sent(e):
    config.print_message(' * [Worker] [AMQP] Sent ' + e + ' Notification')


def print_error_amqp():
    config.print_error(' * [Worker] AMQP configuration is not valid or it is'
                       'not online')


class Event(object):

    def __init__(self):
        self.fields = dict()

    def update(self, event):

        """
        Should mix values from the two events
        :param event: Event which values will be added
        """

        pass

    def event_data(self):

        values = dict()
        values.update({k: list(v) if k is not 'repository' else v
                       for k, v in self.fields.iteritems()})
        values['timestamp'] = long(time.time() * 1000)

        return values


class BasicEvent(Event):

    def __init__(self, name, elements):
        super(BasicEvent, self).__init__()
        self.name = name
        self.fields[self.name] = set(elements)

    def update(self, event):

        if not isinstance(event, BasicEvent) or self.name is not event.name:
            raise StandardError('Error: Not compatible event type.',
                                type(event))

        self.fields[self.name].update(event.fields[event.name])


class RepositoryCreatedEvent(BasicEvent):

    def __init__(self, elements):
        name = 'newRepositories'
        super(RepositoryCreatedEvent, self).__init__(name, elements)


class RepositoryDeletedEvent(BasicEvent):

    def __init__(self, elements):
        name = 'deleteRepositories'
        super(RepositoryDeletedEvent, self).__init__(name, elements)


class CommitterCreatedEvent(BasicEvent):

    def __init__(self, elements):
        name = 'newCommitters'
        super(CommitterCreatedEvent, self).__init__(name, elements)


class CommitterDeletedEvent(BasicEvent):

    def __init__(self, elements):
        name = 'deleteCommitters'
        super(CommitterDeletedEvent, self).__init__(name, elements)


class RepositoryUpdatedEvent(Event):

    def __init__(self, repository, name, elements):
        super(RepositoryUpdatedEvent, self).__init__()
        self.fields['repository'] = repository
        self.fields[name] = set(elements)

    def update(self, event):

        if not isinstance(event, RepositoryUpdatedEvent):
            raise StandardError('Error: Not compatible event type.',
                                type(event))

        if self.fields['repository'] is not event.fields['repository']:
            raise StandardError('Error: Not compatible repositories.',
                                type(event))

        self.fields.update({k: self.fields.get(k, v).union(v)
                            for k, v in event.fields.iteritems()
                            if k is not 'repository'})


class EventManager(object):

    def __init__(self, instance, host, port, virtual_host='/', t_window=1):

        """
        Class that manage events, sending them in intervals of t_window
        seconds

        Args:
            host: host address
            port: host listening port
            virtual_host:
            t_window: time between sendings in seconds
        """

        self.broker_host = host
        self.broker_port = port
        self.virtual_host = virtual_host
        self.t_window = float(t_window)
        self.instance = instance
        self.events = dict()
        self._lock = threading.RLock()

    def start(self):

        self._lock.acquire(True)
        for event in self.events:
            data = self.events[event].event_data()
            data['instance'] = self.instance
            self._send(json.dumps(data), event.__class__.__name__)

        self.events.clear()
        self._lock.release()

        time.sleep(self.t_window)
        self.start()

    def add_event(self, event):

        """
        Method that adds an event to the list of events to send
        :param event: Event to be sent
        """

        self._lock.acquire(True)
        if not isinstance(event, RepositoryUpdatedEvent):
            e = self.events.get(event.name, event)
            e.update(event)
            self.events[event.__class__.__name__] = e

        else:  # then is a repository update
            identifier = 'update:%s' % event.fields['repository']
            e = self.events.get(identifier, event)
            e.update(event)
            self.events[identifier] = e
        self._lock.release()

    def _send(self, message, event_name):

        try:
            connection_params = pika.ConnectionParameters(
                host=self.broker_host,
                port=self.broker_port,
                virtual_host=self.virtual_host
            )
            connection = pika.BlockingConnection(connection_params)
        except ConnectionClosed:
            print_error_amqp()
            return

        try:
            channel = connection.channel()
            routing_key = 'gitcollector.notification.' + event_name
            channel.confirm_delivery()
            sent = channel.basic_publish(
                exchange=config.GC_AMQP_EXCNAME,
                routing_key=routing_key,
                body=json.dumps(message, ensure_ascii=False),
                properties=BasicProperties(
                    content_type='application/psr.sdh.gitcollector+json',
                    content_encoding='utf-8',
                    delivery_mode=2
                ),
                mandatory=True
            )
            if not sent:
                print_error_amqp()
            else:
                print_sent(event_name)
        except ChannelClosed:
            print_error_amqp()
        finally:
            connection.close()
