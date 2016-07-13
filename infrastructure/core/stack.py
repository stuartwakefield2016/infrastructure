import boto3
import botocore.exceptions
from troposphere import Template


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

    def build(self):
        return StackBuilder.build(self)


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

        try:
            StackBuilder.create(stack)
        except botocore.exceptions.ClientError as err:
            if err.response['Error']['Code'] == 'AlreadyExistsException':
                StackBuilder.update(stack)
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
