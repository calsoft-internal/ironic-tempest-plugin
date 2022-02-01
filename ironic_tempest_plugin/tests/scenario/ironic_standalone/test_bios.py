#
# Copyright 2018 Red Hat Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators

from ironic_tempest_plugin.tests.scenario import \
    baremetal_standalone_manager as bsm

LOG = logging.getLogger(__name__)
CONF = config.CONF


class BaremetalFakeBios(
        bsm.BaremetalStandaloneScenarioTest):

    driver = 'fake-hardware'
    bios_interface = 'fake'
    deploy_interface = 'iscsi'
    image_ref = CONF.baremetal.whole_disk_image_ref
    wholedisk_image = True
    delete_node = False
    api_microversion = '1.40'

    @decorators.idempotent_id('ef55c44a-cc10-4cf6-8fda-85f0c0793150')
    def test_bios_apply_and_reset_configuration(self):
        settings = [
            {
                "name": "setting1_name",
                "value": "setting1_value"
            },
            {
                "name": "setting2_name",
                "value": "setting2_value"
            }
        ]

        self.check_bios_apply_and_reset_configuration(self.node, settings)


class BaremetalIdracBiosCleaning(
        bsm.BaremetalStandaloneScenarioTest):

    mandatory_attr = ['driver', 'bios_interface']
    driver = 'idrac'
    deploy_interface = 'direct'
    delete_node = False
    api_microversion = '1.40'

    @decorators.idempotent_id('6ded82ab-b444-436b-bb78-06fa5957d6c3')
    def test_bios_apply_and_reset_configuration(self):

        new_settings = [
            {
                "name": "ProcVirtualization",
                "value": "Enabled"
            },
            {
                "name": "BootMode",
                "value": "Uefi"
            }
        ]

        clean_steps = [
            {
                "interface": "bios",
                "step": "apply_configuration",
                "args": {"settings": new_settings}
            }
        ]

        _, bios_settings = self.baremetal_client.\
            list_node_bios_settings(self.node['uuid'])

        prev_settings = [
            dict({i['name']:i['value']}) for setting in new_settings
            for i in bios_settings['bios'] if setting['name'] == i['name']]
        self.manual_cleaning(self.node, clean_steps=clean_steps)

        _, bios_settings = self.baremetal_client.\
            list_node_bios_settings(self.node['uuid'])

        for setting in new_settings:
            self.assertIn(setting['name'],
                          [i['name'] for i in bios_settings['bios']])
            self.assertIn(setting['value'],
                          [i['value'] for i in bios_settings['bios']])

        clean_steps_restore = [
            {
                "interface": "bios",
                "step": "apply_configuration",
                "args": {"settings": prev_settings}
            }
        ]

        self.manual_cleaning(self.node, clean_steps=clean_steps_restore)

        _, bios_settings = self.baremetal_client.\
            list_node_bios_settings(self.node['uuid'])

        for setting in prev_settings:
            self.assertIn(setting['name'],
                          [i['name'] for i in bios_settings['bios']])
            self.assertIn(setting['value'],
                          [i['value'] for i in bios_settings['bios']])


class BaremetalIdracWSManBios(
        BaremetalIdracBiosCleaning):

    bios_interface = 'idrac-wsman'


class BaremetalIdracRedfishBios(
        BaremetalIdracBiosCleaning):

    bios_interface = 'idrac-redfish'
