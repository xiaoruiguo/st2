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
import mock

from st2common.constants.action import LIVEACTION_STATUS_SUCCEEDED
from st2common.models.db.liveaction import LiveActionDB
from st2common.models.system.common import ResourceReference
from st2common.services import action as action_service
from st2common.util import action_db as action_db_util
from st2tests import ExecutionDbTestCase
from st2tests.fixturesloader import FixturesLoader
from action_chain_runner import action_chain_runner as acr


class DummyActionExecution(object):
    def __init__(self, status=LIVEACTION_STATUS_SUCCEEDED, result=''):
        self.id = None
        self.status = status
        self.result = result


FIXTURES_PACK = 'generic'

TEST_MODELS = {
    'actions': ['a1.yaml', 'a2.yaml'],
    'runners': ['testrunner1.yaml']
}

MODELS = FixturesLoader().load_models(fixtures_pack=FIXTURES_PACK,
                                      fixtures_dict=TEST_MODELS)
ACTION_1 = MODELS['actions']['a1.yaml']
ACTION_2 = MODELS['actions']['a2.yaml']
RUNNER = MODELS['runners']['testrunner1.yaml']

CHAIN_1_PATH = FixturesLoader().get_fixture_file_path_abs(
    FIXTURES_PACK, 'actionchains', 'chain_with_notifications.yaml')


@mock.patch.object(
    action_db_util,
    'get_runnertype_by_name',
    mock.MagicMock(return_value=RUNNER))
@mock.patch.object(
    action_service,
    'is_action_canceled_or_canceling',
    mock.MagicMock(return_value=False))
@mock.patch.object(
    action_service,
    'is_action_paused_or_pausing',
    mock.MagicMock(return_value=False))
class TestActionChainNotifications(ExecutionDbTestCase):

    @mock.patch.object(action_db_util, 'get_action_by_ref',
                       mock.MagicMock(return_value=ACTION_1))
    @mock.patch.object(action_service, 'request', return_value=(DummyActionExecution(), None))
    def test_chain_runner_success_path(self, request):
        chain_runner = acr.get_runner()
        chain_runner.entry_point = CHAIN_1_PATH
        chain_runner.action = ACTION_1
        action_ref = ResourceReference.to_string_reference(name=ACTION_1.name, pack=ACTION_1.pack)
        chain_runner.liveaction = LiveActionDB(action=action_ref)
        chain_runner.pre_run()
        chain_runner.run({})
        self.assertNotEqual(chain_runner.chain_holder.actionchain, None)
        self.assertEqual(request.call_count, 2)
        first_call_args = request.call_args_list[0][0]
        liveaction_db = first_call_args[0]
        self.assertTrue(liveaction_db.notify, 'Notify property expected.')

        second_call_args = request.call_args_list[1][0]
        liveaction_db = second_call_args[0]
        self.assertFalse(liveaction_db.notify, 'Notify property not expected.')
