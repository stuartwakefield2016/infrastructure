import json
import logging

import boto3
import botocore.exceptions
import yaml
from infrastructure.aop import around
from troposphere import Template


class YamlTemplate:

    def __init__(self, body):
        self._body = body

    def to_json(self):
        return json.dumps(yaml.load(self._body))


class RawStack:

    def __init__(self, name, template):
        self._name = name
        self._template = template

    def name(self):
        return self._name

    def template(self):
        return self._template

    def build(self, params):
        return StackBuilder.build(self, params)

    def status(self):
        return StackDescriber.describe(self._name)

    def events(self):
        return StackDescriber.events(self._name)


class Stack:
    """
    I am used to build a stack with consistent naming conventions
    using troposphere templates and boto3 to create or update the
    stack.
    """

    def __init__(self, prefix, name):
        """
        Set up the stack with the specified name and template body.

        :type prefix: basestring
        :param prefix: The prefix to apply to stack components.
            Note that this will also apply to the stack component.

        :type name: basestring
        :param name: The name to apply to the stack component.
        """
        self._naming = ComponentNaming(prefix)
        self._name = name
        self._template = Template()

    def name(self):
        return self._naming.component(self._name)

    def component(self, name):
        return self._naming.component(name)

    def template(self):
        return self._template

    def build(self, params):
        return StackBuilder.build(self, params)


class ComponentNaming:
    """
    I handle the naming of stack components. The naming convention
    is the stack prefix plus a component name.
    """

    def __init__(self, prefix):
        """
        Set up the naming with the specified prefix.

        :type prefix: basestring
        :param prefix: The prefix to apply to each component.
        """
        self._prefix = prefix

    def component(self, name):
        """
        Returns the component name for the stack naming configured.

        :type name: basestring
        :param name: The name of the component to prefix.

        :return: The full resolved name of the component.
        """
        return self._prefix + name

logger = logging.getLogger(__name__)



class StackBuilder:

    @staticmethod
    def build(stack, params):
        """
        Creates a new or updates an existing stack.

        :type stack: Stack
        :param stack: The stack to create or update
        """

        try:
            StackBuilder.create(stack, params)

        except botocore.exceptions.ClientError as err:

            if err.response['Error']['Code'] == 'AlreadyExistsException':
                logger.info('Stack "%s" already exists', stack.name())

                StackBuilder.update(stack, params)
            else:
                raise err

    @staticmethod
    @around(
        lambda stack, _: logger.info('Create stack "%s"', stack.name()),
        lambda stack, _: logger.info('Create stack "%s" complete', stack.name())
    )
    def create(stack, params):
        cloudformation = boto3.client('cloudformation')

        cloudformation.create_stack(
            StackName=stack.name(),
            TemplateBody=stack.template().to_json(),
            Parameters=StackBuilder.to_param_array(params)
        )

    @staticmethod
    @around(
        lambda stack, _: logger.info('Update stack "%s"', stack.name()),
        lambda stack, _: logger.info('Update stack "%s" complete', stack.name())
    )
    def update(stack, params):
        cloudformation = boto3.client('cloudformation')

        cloudformation.update_stack(
            StackName=stack.name(),
            TemplateBody=stack.template().to_json(),
            Parameters=StackBuilder.to_param_array(params)
        )

    @staticmethod
    def to_param_array(params):
        return [
            {
                'ParameterKey': k,
                'ParameterValue': v
            } for k, v in params.items()
        ]


class StackDescriber:

    @staticmethod
    def describe(stack_name):
        cloudformation = boto3.client('cloudformation')

        response = cloudformation.describe_stacks(
            StackName=stack_name
        )

        return response['Stacks'][0]['StackStatus']

    @staticmethod
    def events(stack_name):
        cloudformation = boto3.client('cloudformation')

        response = cloudformation.describe_stack_events(
            StackName=stack_name
        )

        return response['StackEvents']


class StackEventLog:

    def __init__(self, stack):
        self._events = []
        self._encountered_event_ids = set()
        self._stack = stack

    def next_events(self):

        new_events = []
        incoming_events = sorted(
            self._stack.events(),
            key=lambda event: event['Timestamp']
        )

        for event in incoming_events:
            if event['EventId'] not in self._encountered_event_ids:
                new_events.append(event)
                self._events.append(event)
            self._encountered_event_ids.add(event['EventId'])

        return new_events
