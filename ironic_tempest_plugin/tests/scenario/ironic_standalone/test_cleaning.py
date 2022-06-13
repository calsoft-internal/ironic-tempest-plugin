#
# Copyright 2017 Mirantis Inc.
#
# Copyright (c) 2022 Dell Inc. or its subsidiaries.
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

import json
import os

import jsonschema
from jsonschema import exceptions as json_schema_exc
from oslo_log import log as logging
from tempest.common import utils
from tempest import config
from tempest.lib import decorators

from ironic_tempest_plugin.tests.scenario import \
    baremetal_standalone_manager as bsm

LOG = logging.getLogger(__name__)
CONF = config.CONF


class BaremetalCleaningAgentIpmitoolWholedisk(
        bsm.BaremetalStandaloneScenarioTest):

    driver = 'agent_ipmitool'
    image_ref = CONF.baremetal.whole_disk_image_ref
    wholedisk_image = True
    delete_node = False
    api_microversion = '1.28'

    @decorators.idempotent_id('0d82cedd-9697-4cf7-8e4a-80d510f53615')
    @utils.services('image', 'network')
    def test_manual_cleaning(self):
        self.check_manual_partition_cleaning(self.node)


class BaremetalCleaningPxeIpmitoolWholedisk(
        bsm.BaremetalStandaloneScenarioTest):

    driver = 'pxe_ipmitool'
    image_ref = CONF.baremetal.whole_disk_image_ref
    wholedisk_image = True
    delete_node = False
    api_microversion = '1.28'

    @decorators.idempotent_id('fb03abfa-cdfc-41ec-aaa8-c70402786a85')
    @utils.services('image', 'network')
    def test_manual_cleaning(self):
        self.check_manual_partition_cleaning(self.node)


class BaremetalCleaningIpmiWholedisk(
        bsm.BaremetalStandaloneScenarioTest):

    driver = 'ipmi'
    image_ref = CONF.baremetal.whole_disk_image_ref
    wholedisk_image = True
    delete_node = False
    deploy_interface = 'iscsi'
    api_microversion = '1.31'

    @classmethod
    def skip_checks(cls):
        super(BaremetalCleaningIpmiWholedisk, cls).skip_checks()
        if CONF.baremetal_feature_enabled.software_raid:
            raise cls.skipException("Cleaning is covered in the RAID test")

    @decorators.idempotent_id('065238db-1b6d-4d75-a9da-c240f8cbd956')
    @utils.services('image', 'network')
    def test_manual_cleaning(self):
        self.check_manual_partition_cleaning(self.node)


class SoftwareRaidIscsi(bsm.BaremetalStandaloneScenarioTest):

    if 'redfish' in CONF.baremetal.enabled_hardware_types:
        driver = 'redfish'
    else:
        driver = 'ipmi'
    image_ref = CONF.baremetal.whole_disk_image_ref
    wholedisk_image = True
    deploy_interface = 'iscsi'
    raid_interface = 'agent'
    api_microversion = '1.55'
    # Software RAID is always local boot
    boot_option = 'local'
    delete_node = False

    raid_config = {
        "logical_disks": [
            {
                "size_gb": "MAX",
                "raid_level": "1",
                "controller": "software"
            },
        ]
    }

    @classmethod
    def skip_checks(cls):
        super(SoftwareRaidIscsi, cls).skip_checks()
        if cls.driver == 'ipmi':
            raise cls.skipException("Testing with redfish driver")
        if not CONF.baremetal_feature_enabled.software_raid:
            raise cls.skipException("Software RAID feature is not enabled")

    @decorators.idempotent_id('7ecba4f7-98b8-4ea1-b95e-3ec399f46798')
    @utils.services('image', 'network')
    def test_software_raid(self):
        self.build_raid_and_verify_node(
            deploy_time=CONF.baremetal_feature_enabled.deploy_time_raid)
        # NOTE(TheJulia): tearing down/terminating the instance does not
        # remove the root device hint, so it is best for us to go ahead
        # and remove it before exiting the test.
        self.remove_root_device_hint()
        self.terminate_node(self.node['uuid'], force_delete=True)


class SoftwareRaidDirect(bsm.BaremetalStandaloneScenarioTest):

    if 'redfish' in CONF.baremetal.enabled_hardware_types:
        driver = 'redfish'
    else:
        driver = 'ipmi'
    image_ref = CONF.baremetal.whole_disk_image_ref
    wholedisk_image = True
    deploy_interface = 'direct'
    raid_interface = 'agent'
    api_microversion = '1.55'
    # Software RAID is always local boot
    boot_option = 'local'
    delete_node = False

    # TODO(dtantsur): more complex layout in this job
    raid_config = {
        "logical_disks": [
            {
                "size_gb": "MAX",
                "raid_level": "1",
                "controller": "software"
            },
        ]
    }

    @classmethod
    def skip_checks(cls):
        super(SoftwareRaidDirect, cls).skip_checks()
        if cls.driver == 'redfish':
            raise cls.skipException("Testing with ipmi driver")
        if not CONF.baremetal_feature_enabled.software_raid:
            raise cls.skipException("Software RAID feature is not enabled")

    @decorators.idempotent_id('125361ac-0eb3-4d79-8be2-a91936aa3f46')
    @utils.services('image', 'network')
    def test_software_raid(self):
        self.build_raid_and_verify_node(
            deploy_time=CONF.baremetal_feature_enabled.deploy_time_raid)
        # NOTE(TheJulia): tearing down/terminating the instance does not
        # remove the root device hint, so it is best for us to go ahead
        # and remove it before exiting the test.
        self.remove_root_device_hint()
        self.terminate_node(self.node['uuid'], force_delete=True)


class BaremetalIdracManagementCleaning(
        bsm.BaremetalStandaloneScenarioTest):

    mandatory_attr = ['driver', 'management_interface',
                      'power_interface']

    driver = 'idrac'
    delete_node = False
    # Minimum version for manual cleaning is 1.15 (# v1.15: Add ability to
    # do manual cleaning of nodes). The test cases clean up at the end by
    # detaching the VIF. Support for VIFs was introduced by version 1.28
    # (# v1.28: Add vifs subcontroller to node).
    api_microversion = '1.28'

    @decorators.idempotent_id('d085ff72-abef-4931-a5b0-06efd5f9a037')
    def test_reset_idrac(self):
        clean_steps = [
            {
                "interface": "management",
                "step": "reset_idrac"
            }
        ]
        self.manual_cleaning(self.node, clean_steps=clean_steps)

    @decorators.idempotent_id('9252ec6f-6b5b-447e-a323-c52775b88b4e')
    def test_clear_job_queue(self):
        clean_steps = [
            {
                "interface": "management",
                "step": "clear_job_queue"
            }
        ]
        self.manual_cleaning(self.node, clean_steps=clean_steps)

    @decorators.idempotent_id('7baeff52-7d6e-4dea-a48f-a85a6bfc9f62')
    def test_known_good_state(self):
        clean_steps = [
            {
                "interface": "management",
                "step": "known_good_state"
            }
        ]
        self.manual_cleaning(self.node, clean_steps=clean_steps)


class BaremetalIdracRedfishManagementCleaning(
        BaremetalIdracManagementCleaning):

    management_interface = 'idrac-redfish'
    power_interface = 'idrac-redfish'


class BaremetalIdracWSManManagementCleaning(
        BaremetalIdracManagementCleaning):

    management_interface = 'idrac-wsman'
    power_interface = 'idrac-wsman'


class BaremetalIdracRaidCleaning(bsm.BaremetalStandaloneScenarioTest):

    mandatory_attr = ['driver', 'raid_interface']

    image_ref = CONF.baremetal.whole_disk_image_ref
    wholedisk_image = True
    storage_inventory = CONF.baremetal.storage_inventory
    driver = 'idrac'
    api_microversion = '1.32'
    delete_node = False

    @classmethod
    def skip_checks(cls):
        super(BaremetalIdracRaidCleaning, cls).skip_checks()
        if not CONF.baremetal.storage_inventory:
            raise cls.skipException('Storage inventory file path missing.'
                                    'Skipping Test case')

    def storage_inventory_validation(self):
        """Validates the storage information passed in file using JSON schema.

        This method validates a storage inventory information against
        a storage inventory schema.

        :raises: skipException if validation of the storage inventory
        fails and it skips Test case execution.

        """
        try:
            with open(self.storage_inventory, 'r') as storage_invent_fobj:
                storage_inventory_info = json.load(storage_invent_fobj)
        except IOError:
            raise self.skipException('Storage inventory file is not found,'
                                     'Skipping Test Case')
        STORAGE_INVENTORY_SCHEMA = os.path.join(os.path.dirname(
            __file__), 'storage_inventory_schema.json')
        with open(STORAGE_INVENTORY_SCHEMA, 'r') as storage_schema_fobj:
            storage_inventory_schema = json.load(storage_schema_fobj)
        try:
            jsonschema.validate(storage_inventory_info,
                                storage_inventory_schema)
        except json_schema_exc.ValidationError as e:
            msg = _("Storage Inventory validation error: %s") % e.message
            raise self.skipException(msg)
        return storage_inventory_info

    @decorators.idempotent_id('8a908a3c-f2af-48fb-8553-9163715aa403')
    @utils.services('image', 'network')
    def test_hardware_raid(self):
        storage_inventory_info = self.storage_inventory_validation()
        controller_id = storage_inventory_info[
            'storage_inventory'][0]['controllers'][0]['id']
        number_of_physical_disks = storage_inventory_info[
            'storage_inventory'][0]['controllers'][0][
                'number_of_physical_disks']
        if number_of_physical_disks < 2:
            raise self.skipException('Atleast 2 drives are required'
                                     'in controller for this test.'
                                     'Skipping Test case')
        raid_config = {
            "logical_disks": [
                {
                    "size_gb": 100,
                    "raid_level": "1",
                    "controller": controller_id
                }
            ]
        }
        self.build_raid_and_verify_node(
            config=raid_config,
            deploy_time=CONF.baremetal_feature_enabled.deploy_time_raid,
            raid_ctrl_present=True)
        self.remove_root_device_hint()
        self.terminate_node(self.node['uuid'], force_delete=True)

    @utils.services('image', 'network')
    @decorators.idempotent_id('92fe534d-77f1-422d-84e4-e30fe9e3d928')
    def test_raid_cleaning_max_size_raid_10(self):
        storage_inventory_info = self.storage_inventory_validation()
        print(storage_inventory_info)
        controller_id = storage_inventory_info[
            'storage_inventory'][0]['controllers'][0]['id']
        number_of_physical_disks = storage_inventory_info[
            'storage_inventory'][0]['controllers'][0][
                'number_of_physical_disks']
        if number_of_physical_disks < 4:
            raise self.skipException('Atleast 4 drives are required'
                                     'in controller for this test,'
                                     'Skipping Test Case.')
        physical_disks = [pdisk['id'] for pdisk in (storage_inventory_info[
            'storage_inventory'][0]['controllers'][0]['physical_disks'])]
        raid_config = {
            "logical_disks": [
                {
                    "size_gb": "MAX",
                    "raid_level": "1+0",
                    "controller": controller_id,
                    "number_of_physical_disks": number_of_physical_disks,
                    "physical_disks": physical_disks
                }
            ]
        }
        self.build_raid_and_verify_node(
            config=raid_config,
            deploy_time=CONF.baremetal_feature_enabled.deploy_time_raid,
            raid_ctrl_present=True)
        self.remove_root_device_hint()
        self.terminate_node(self.node['uuid'], force_delete=True)


class BaremetalIdracRedfishRaidCleaning(
        BaremetalIdracRaidCleaning):
    raid_interface = 'idrac-redfish'


class BaremetalIdracWSManRaidCleaning(
        BaremetalIdracRaidCleaning):
    raid_interface = 'idrac-wsman'
