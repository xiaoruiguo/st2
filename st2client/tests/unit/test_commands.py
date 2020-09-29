# Copyright 2020 The StackStorm Authors.
# Copyright 2019 Extreme Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
import os
import mock
import json
import logging
import argparse
import tempfile
import unittest2
from collections import namedtuple

from tests import base
from tests.base import BaseCLITestCase

from st2client.shell import Shell
from st2client import models
from st2client.utils import httpclient
from st2client.commands import resource
from st2client.commands.resource import ResourceViewCommand

__all__ = [
    'TestResourceCommand',
    'ResourceViewCommandTestCase'
]


LOG = logging.getLogger(__name__)


class TestResourceCommand(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestResourceCommand, self).__init__(*args, **kwargs)
        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers()
        self.branch = resource.ResourceBranch(
            base.FakeResource, 'Test Command', base.FakeApp(), self.subparsers)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=base.FakeResponse(json.dumps(base.RESOURCES), 200, 'OK')))
    def test_command_list(self):
        args = self.parser.parse_args(['fakeresource', 'list'])
        self.assertEqual(args.func, self.branch.commands['list'].run_and_print)
        instances = self.branch.commands['list'].run(args)
        actual = [instance.serialize() for instance in instances]
        expected = json.loads(json.dumps(base.RESOURCES))
        self.assertListEqual(actual, expected)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=base.FakeResponse('', 500, 'INTERNAL SERVER ERROR')))
    def test_command_list_failed(self):
        args = self.parser.parse_args(['fakeresource', 'list'])
        self.assertRaises(Exception, self.branch.commands['list'].run, args)

    @mock.patch.object(
        models.ResourceManager, 'get_by_name',
        mock.MagicMock(return_value=None))
    @mock.patch.object(
        models.ResourceManager, 'get_by_id',
        mock.MagicMock(return_value=base.FakeResource(**base.RESOURCES[0])))
    def test_command_get_by_id(self):
        args = self.parser.parse_args(['fakeresource', 'get', '123'])
        self.assertEqual(args.func, self.branch.commands['get'].run_and_print)
        instance = self.branch.commands['get'].run(args)
        actual = instance.serialize()
        expected = json.loads(json.dumps(base.RESOURCES[0]))
        self.assertEqual(actual, expected)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=base.FakeResponse(json.dumps(base.RESOURCES[0]), 200, 'OK')))
    def test_command_get(self):
        args = self.parser.parse_args(['fakeresource', 'get', 'abc'])
        self.assertEqual(args.func, self.branch.commands['get'].run_and_print)
        instance = self.branch.commands['get'].run(args)
        actual = instance.serialize()
        expected = json.loads(json.dumps(base.RESOURCES[0]))
        self.assertEqual(actual, expected)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=base.FakeResponse('', 404, 'NOT FOUND')))
    def test_command_get_404(self):
        args = self.parser.parse_args(['fakeresource', 'get', 'cba'])
        self.assertEqual(args.func, self.branch.commands['get'].run_and_print)
        self.assertRaises(resource.ResourceNotFoundError,
                          self.branch.commands['get'].run,
                          args)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=base.FakeResponse('', 500, 'INTERNAL SERVER ERROR')))
    def test_command_get_failed(self):
        args = self.parser.parse_args(['fakeresource', 'get', 'cba'])
        self.assertRaises(Exception, self.branch.commands['get'].run, args)

    @mock.patch.object(
        httpclient.HTTPClient, 'post',
        mock.MagicMock(return_value=base.FakeResponse(json.dumps(base.RESOURCES[0]), 200, 'OK')))
    def test_command_create(self):
        instance = base.FakeResource(name='abc')
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with open(path, 'a') as f:
                f.write(json.dumps(instance.serialize(), indent=4))
            args = self.parser.parse_args(['fakeresource', 'create', path])
            self.assertEqual(args.func,
                             self.branch.commands['create'].run_and_print)
            instance = self.branch.commands['create'].run(args)
            actual = instance.serialize()
            expected = json.loads(json.dumps(base.RESOURCES[0]))
            self.assertEqual(actual, expected)
        finally:
            os.close(fd)
            os.unlink(path)

    @mock.patch.object(
        httpclient.HTTPClient, 'post',
        mock.MagicMock(return_value=base.FakeResponse('', 500, 'INTERNAL SERVER ERROR')))
    def test_command_create_failed(self):
        instance = base.FakeResource(name='abc')
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with open(path, 'a') as f:
                f.write(json.dumps(instance.serialize(), indent=4))
            args = self.parser.parse_args(['fakeresource', 'create', path])
            self.assertRaises(Exception,
                              self.branch.commands['create'].run,
                              args)
        finally:
            os.close(fd)
            os.unlink(path)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=base.FakeResponse(json.dumps([base.RESOURCES[0]]), 200, 'OK',
                                                      {})))
    @mock.patch.object(
        httpclient.HTTPClient, 'put',
        mock.MagicMock(return_value=base.FakeResponse(json.dumps(base.RESOURCES[0]), 200, 'OK')))
    def test_command_update(self):
        instance = base.FakeResource(id='123', name='abc')
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with open(path, 'a') as f:
                f.write(json.dumps(instance.serialize(), indent=4))
            args = self.parser.parse_args(
                ['fakeresource', 'update', '123', path])
            self.assertEqual(args.func,
                             self.branch.commands['update'].run_and_print)
            instance = self.branch.commands['update'].run(args)
            actual = instance.serialize()
            expected = json.loads(json.dumps(base.RESOURCES[0]))
            self.assertEqual(actual, expected)
        finally:
            os.close(fd)
            os.unlink(path)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=base.FakeResponse(json.dumps([base.RESOURCES[0]]), 200, 'OK')))
    @mock.patch.object(
        httpclient.HTTPClient, 'put',
        mock.MagicMock(return_value=base.FakeResponse('', 500, 'INTERNAL SERVER ERROR')))
    def test_command_update_failed(self):
        instance = base.FakeResource(id='123', name='abc')
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with open(path, 'a') as f:
                f.write(json.dumps(instance.serialize(), indent=4))
            args = self.parser.parse_args(
                ['fakeresource', 'update', '123', path])
            self.assertRaises(Exception,
                              self.branch.commands['update'].run,
                              args)
        finally:
            os.close(fd)
            os.unlink(path)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=base.FakeResponse(json.dumps([base.RESOURCES[0]]), 200, 'OK')))
    def test_command_update_id_mismatch(self):
        instance = base.FakeResource(id='789', name='abc')
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with open(path, 'a') as f:
                f.write(json.dumps(instance.serialize(), indent=4))
            args = self.parser.parse_args(
                ['fakeresource', 'update', '123', path])
            self.assertRaises(Exception,
                              self.branch.commands['update'].run,
                              args)
        finally:
            os.close(fd)
            os.unlink(path)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=base.FakeResponse(json.dumps([base.RESOURCES[0]]), 200, 'OK',
                                                      {})))
    @mock.patch.object(
        httpclient.HTTPClient, 'delete',
        mock.MagicMock(return_value=base.FakeResponse('', 204, 'NO CONTENT')))
    def test_command_delete(self):
        args = self.parser.parse_args(['fakeresource', 'delete', 'abc'])
        self.assertEqual(args.func,
                         self.branch.commands['delete'].run_and_print)
        self.branch.commands['delete'].run(args)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=base.FakeResponse('', 404, 'NOT FOUND')))
    def test_command_delete_404(self):
        args = self.parser.parse_args(['fakeresource', 'delete', 'cba'])
        self.assertEqual(args.func,
                         self.branch.commands['delete'].run_and_print)
        self.assertRaises(resource.ResourceNotFoundError,
                          self.branch.commands['delete'].run,
                          args)

    @mock.patch.object(
        httpclient.HTTPClient, 'get',
        mock.MagicMock(return_value=base.FakeResponse(json.dumps([base.RESOURCES[0]]), 200, 'OK')))
    @mock.patch.object(
        httpclient.HTTPClient, 'delete',
        mock.MagicMock(return_value=base.FakeResponse('', 500, 'INTERNAL SERVER ERROR')))
    def test_command_delete_failed(self):
        args = self.parser.parse_args(['fakeresource', 'delete', 'cba'])
        self.assertRaises(Exception, self.branch.commands['delete'].run, args)


class ResourceViewCommandTestCase(unittest2.TestCase):

    def setUp(self):
        ResourceViewCommand.display_attributes = []

    def test_get_include_attributes(self):
        cls = namedtuple('Args', 'attr')

        args = cls(attr=[])
        result = ResourceViewCommand._get_include_attributes(args=args)
        self.assertEqual(result, [])

        args = cls(attr=['result'])
        result = ResourceViewCommand._get_include_attributes(args=args)
        self.assertEqual(result, ['result'])

        args = cls(attr=['result', 'trigger_instance'])
        result = ResourceViewCommand._get_include_attributes(args=args)
        self.assertEqual(result, ['result', 'trigger_instance'])

        args = cls(attr=['result.stdout'])
        result = ResourceViewCommand._get_include_attributes(args=args)
        self.assertEqual(result, ['result.stdout'])

        args = cls(attr=['result.stdout', 'result.stderr'])
        result = ResourceViewCommand._get_include_attributes(args=args)
        self.assertEqual(result, ['result.stdout', 'result.stderr'])

        args = cls(attr=['result.stdout', 'trigger_instance.id'])
        result = ResourceViewCommand._get_include_attributes(args=args)
        self.assertEqual(result, ['result.stdout', 'trigger_instance.id'])

        ResourceViewCommand.display_attributes = ['id', 'status']

        args = cls(attr=[])
        result = ResourceViewCommand._get_include_attributes(args=args)
        self.assertEqual(set(result), set(['id', 'status']))

        args = cls(attr=['trigger_instance'])
        result = ResourceViewCommand._get_include_attributes(args=args)
        self.assertEqual(set(result), set(['trigger_instance']))

        args = cls(attr=['all'])
        result = ResourceViewCommand._get_include_attributes(args=args)
        self.assertEqual(result, None)


class CommandsHelpStringTestCase(BaseCLITestCase):
    """
    Test case which verifies that all the commands support -h / --help flag.
    """

    capture_output = True

    # TODO: Automatically iterate all the available commands
    COMMANDS = [
        # action
        ['action', 'list'],
        ['action', 'get'],
        ['action', 'create'],
        ['action', 'update'],
        ['action', 'delete'],
        ['action', 'enable'],
        ['action', 'disable'],
        ['action', 'execute'],

        # execution
        ['execution', 'cancel'],
        ['execution', 'pause'],
        ['execution', 'resume'],
        ['execution', 'tail']
    ]

    def test_help_command_line_arg_works_for_supported_commands(self):
        shell = Shell()

        for command in self.COMMANDS:
            # First test longhang notation
            argv = command + ['--help']

            try:
                result = shell.run(argv)
            except SystemExit as e:
                self.assertEqual(e.code, 0)
            else:
                self.assertEqual(result, 0)

            stdout = self.stdout.getvalue()

            self.assertIn('usage:', stdout)
            self.assertIn(' '.join(command), stdout)
            # self.assertIn('positional arguments:', stdout)
            self.assertIn('optional arguments:', stdout)

            # Reset stdout and stderr after each iteration
            self._reset_output_streams()

            # Then shorthand notation
            argv = command + ['-h']

            try:
                result = shell.run(argv)
            except SystemExit as e:
                self.assertEqual(e.code, 0)
            else:
                self.assertEqual(result, 0)

            stdout = self.stdout.getvalue()

            self.assertIn('usage:', stdout)
            self.assertIn(' '.join(command), stdout)
            # self.assertIn('positional arguments:', stdout)
            self.assertIn('optional arguments:', stdout)

            # Verify that the actual help usage string was triggered and not the invalid
            # "too few arguments" which would indicate command doesn't actually correctly handle
            # --help flag
            self.assertNotIn('too few arguments', stdout)

            self._reset_output_streams()
