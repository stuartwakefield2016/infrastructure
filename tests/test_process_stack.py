import sys
import json
import unittest
import unittest.mock as mock
from botocore.exceptions import ClientError
from infrastructure.core.stack import processstack, InvalidStackError, NoChangeToStackError, UnknownStackError
from infrastructure.core.stack import RawStack as Stack

name = "TestStack"
invalid_name = "TestStack!!"
existing_name = "ExistingName"
body = """
AWSTemplateFormatVersion: "2010-09-09"

Description: This is a description.

Resources:

  Vpc:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 0.0.0.0/0
"""
body_data = {
    'AWSTemplateFormatVersion': '2010-09-09',
    'Description': 'This is a description.',
    'Resources': {
        'Vpc': {
            'Type': 'AWS::EC2::VPC',
            'Properties': {
                'CidrBlock': '0.0.0.0/0'
            }
        }
    }
}
invalid_body = """
I am not a template!
"""
existing_body = """
AWSTemplateFormatVersion: "2010-09-09"

Description: I already exist.

Resources:

  Vpc:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 0.0.0.0/0
"""


class ProcessStackTestCase(unittest.TestCase):

    @mock.patch("infrastructure.core.stack.boto3")
    def test_creates_stack(self, mock_boto3):

        mock_cloudstack_client = mock.Mock()
        mock_boto3.client.configure_mock(return_value=mock_cloudstack_client)
        mock_cloudstack_client.create_stack.configure_mock(return_value={
            'StackId': 'arn:aws:cloudformation:region:account:stack/abc123'
        })

        processstack(name, body)

        mock_boto3.client.assert_called_with('cloudformation')
        mock_cloudstack_client.create_stack.assert_called_with(StackName=name, TemplateBody=mock.ANY)
        (_, named) = mock_cloudstack_client.create_stack.call_args
        assert json.loads(named['TemplateBody']) == body_data

    @mock.patch("infrastructure.core.stack.boto3")
    def test_raise_invalid_stack(self, mock_boto3):

        mock_cloudstack_client = mock.Mock()
        mock_boto3.client.configure_mock(return_value=mock_cloudstack_client)
        mock_cloudstack_client.create_stack.configure_mock(side_effect=ClientError({
            'Error': {
                'Code': 'ValidationError',
                'Message': 'Template format error: JSON not well-formed.'
            }
        }, 'CreateStack'))

        with self.assertRaises(InvalidStackError):
            processstack(name, invalid_body)

    @mock.patch("infrastructure.core.stack.boto3")
    def test_raise_invalid_name(self, mock_boto3):

        mock_cloudstack_client = mock.Mock()
        mock_boto3.client.configure_mock(return_value=mock_cloudstack_client)
        mock_cloudstack_client.create_stack.configure_mock(side_effect=ClientError({
            'Error': {
                'Code': 'ValidationError',
                'Message': 'Validation error detected at \'stackName\' failed to satisfy constraint.'
            }
        }, 'CreateStack'))

        with self.assertRaises(InvalidStackError):
            processstack(invalid_name, body)

    @mock.patch("infrastructure.core.stack.boto3")
    def test_updates_stack(self, mock_boto3):

        mock_cloudstack_client = mock.Mock()
        mock_boto3.client.configure_mock(return_value=mock_cloudstack_client)
        mock_cloudstack_client.create_stack.configure_mock(side_effect=ClientError({
            'Error': {
                'Code': 'AlreadyExistsException',
                'Message': 'Stack already exists.'
            }
        }, 'CreateStack'))
        mock_cloudstack_client.update_stack.configure_mock(return_value={
            'StackId': 'arn:aws:cloudformation:region:account:stack/abc123'
        })

        processstack(existing_name, body)

        mock_boto3.client.assert_called_with('cloudformation')

        mock_cloudstack_client.create_stack.assert_called_with(StackName=existing_name, TemplateBody=mock.ANY)
        (_, named) = mock_cloudstack_client.create_stack.call_args
        assert json.loads(named['TemplateBody']) == body_data

        mock_cloudstack_client.update_stack.assert_called_with(StackName=existing_name, TemplateBody=mock.ANY)
        (_, named) = mock_cloudstack_client.update_stack.call_args
        assert json.loads(named['TemplateBody']) == body_data

    @mock.patch("infrastructure.core.stack.boto3")
    def test_raise_no_change(self, mock_boto3):

        mock_cloudstack_client = mock.Mock()
        mock_boto3.client.configure_mock(return_value=mock_cloudstack_client)
        mock_cloudstack_client.create_stack.configure_mock(side_effect=ClientError({
            'Error': {
                'Code': 'AlreadyExistsException',
                'Message': 'Stack already exists.'
            }
        }, 'CreateStack'))
        mock_cloudstack_client.update_stack.configure_mock(side_effect=ClientError({
            'Error': {
                'Code': 'ValidationError',
                'Message': 'No updates are to be performed.'
            }
        }, 'UpdateStack'))

        with self.assertRaises(NoChangeToStackError):
            processstack(existing_name, existing_body)

    @mock.patch("infrastructure.core.stack.boto3")
    def test_unhandled_error_on_create(self, mock_boto3):

        mock_cloudstack_client = mock.Mock()
        mock_boto3.client.configure_mock(return_value=mock_cloudstack_client)
        mock_cloudstack_client.create_stack.configure_mock(side_effect=ClientError({
            'Error': {
                'Code': 'UnknownError',
                'Message': 'Unknown error.'
            }
        }, 'CreateStack'))

        with self.assertRaises(UnknownStackError):
            processstack(name, body)

    @mock.patch("infrastructure.core.stack.boto3")
    def test_unhandled_error_on_update(self, mock_boto3):

        mock_cloudstack_client = mock.Mock()
        mock_boto3.client.configure_mock(return_value=mock_cloudstack_client)
        mock_cloudstack_client.create_stack.configure_mock(side_effect=ClientError({
            'Error': {
                'Code': 'AlreadyExistsException',
                'Message': 'Stack already exists.'
            }
        }, 'CreateStack'))
        mock_cloudstack_client.update_stack.configure_mock(side_effect=ClientError({
            'Error': {
                'Code': 'UnknownError',
                'Message': 'Unknown error.'
            }
        }, 'CreateStack'))

        with self.assertRaises(UnknownStackError):
            processstack(name, body)


class StackProcessTestCase(unittest.TestCase):

    @mock.patch("infrastructure.core.stack.boto3")
    def test_calls_process_stack(self, mock_boto3):

        mock_cloudstack_client = mock.Mock()
        mock_boto3.client.configure_mock(return_value=mock_cloudstack_client)
        mock_cloudstack_client.create_stack.configure_mock(return_value={
            'StackId': 'arn:aws:cloudformation:region:account:stack/abc123'
        })

        stack = Stack(name, body)
        stack.process()

        mock_boto3.client.assert_called_with('cloudformation')
        mock_cloudstack_client.create_stack.assert_called_with(StackName=name, TemplateBody=mock.ANY)
        (_, named) = mock_cloudstack_client.create_stack.call_args
        assert json.loads(named['TemplateBody']) == body_data