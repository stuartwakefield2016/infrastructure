import logging
import yaml
import json
import boto3
from botocore.exceptions import ClientError
from troposphere import Template


class BaseStack:

    def stack_name(self):
        raise NotImplemented

    def template_body(self):
        raise NotImplemented

    def process(self):
        return processstack(self.stack_name(), self.template_body())


class RawStack(BaseStack):

    def __init__(self, name, body):
        self._name = name
        self._body = body

    def stack_name(self):
        return self._name

    def template_body(self):
        return self._body


class Stack(BaseStack):
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

    def build(self):
        return StackBuilder.build(self)

    def stack_name(self):
        return self.name()

    def template_body(self):
        return self._template.to_json()


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


class StackBuilder:

    @staticmethod
    def build(stack):
        """
        Creates a new or updates an existing stack.

        :type stack: Stack
        :param stack: The stack to create or update
        """

        logger = logging.getLogger(__name__)

        try:
            logger.info('Create stack "{0}"'.format(stack.name()))
            StackBuilder.create(stack)
            logger.info('Create stack "{0}" complete'.format(stack.name()))
        except ClientError as err:
            if err.response['Error']['Code'] == 'AlreadyExistsException':
                logger.info('Stack "{0}" already exists'.format(stack.name()))
                logger.info('Update stack "{0}"'.format(stack.name()))
                StackBuilder.update(stack)
                logger.info('Update stack "{0}" complete'.format(stack.name()))
            else:
                raise err

    @staticmethod
    def create(stack):
        cloudformation = boto3.client("cloudformation")

        cloudformation.create_stack(
            StackName=stack.name(),
            TemplateBody=stack.template().to_json()
        )

    @staticmethod
    def update(stack):
        cloudformation = boto3.client("cloudformation")

        cloudformation.update_stack(
            StackName=stack.name(),
            TemplateBody=stack.template().to_json()
        )


def processstack(name, body):
    cloudformation = boto3.client("cloudformation")

    try:
        cloudformation.create_stack(
            StackName=name,
            TemplateBody=json.dumps(yaml.load(body))
        )

    except ClientError as err:

        if err.response['Error']['Code'] == 'AlreadyExistsException':

            try:
                cloudformation.update_stack(
                    StackName=name,
                    TemplateBody=json.dumps(yaml.load(body))
                )

            except ClientError as err:
                if err.response['Error']['Code'] == 'ValidationError':
                    raise NoChangeToStackError
                else:
                    raise UnknownStackError

        elif err.response['Error']['Code'] == 'ValidationError':
            raise InvalidStackError
        else:
            raise UnknownStackError


class InvalidStackError(Exception):
    pass


class NoChangeToStackError(Exception):
    pass


class UnknownStackError(Exception):
    pass
