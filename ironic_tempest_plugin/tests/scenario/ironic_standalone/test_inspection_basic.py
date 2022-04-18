#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest.config import CONF
from tempest.lib import decorators


from ironic_tempest_plugin.tests.scenario import \
    baremetal_standalone_manager as bsm


class InspectBasicTest(bsm.BaremetalStandaloneScenarioTest):

    driver = 'idrac'
    mandatory_attr = ['driver', 'inspect_interface']
    image_ref = CONF.baremetal.whole_disk_image_ref

    def verify_node_inspection_data(self, node):
        self.assertEqual(node['properties']['cpu_arch'],
                         'x86_64')
        self.assertGreaterEqual(int(node['properties']['memory_mb']), 0)
        self.assertGreaterEqual(int(node['properties']['cpus']), 0)
        self.assertGreater(int(node['properties']['local_gb']), 0)

    @decorators.idempotent_id('47ea4487-4720-43e8-a024-53ae82f8c264')
    def test_baremetal_inspect(self):
        """This test case follows this set of operations:

            * Sets nodes to manageable state
            * Inspects nodes
            * Verifies all properties are inspected
            * Verifies inspection data
            * Sets node to available state

        """
        self.baremetal_client.set_node_provision_state(self.node['uuid'],
                                                       'manage')
        self.baremetal_client.set_node_provision_state(self.node['uuid'],
                                                       'inspect')

        self.wait_provisioning_state(self.node['uuid'],
                                     'manageable')

        node = self.baremetal_client.show_node(self.node['uuid'])
        for node_attr in node:
            if 'properties' in node_attr:
                node_properties = node_attr
        self.verify_node_inspection_data(node_properties)

        self.baremetal_client.set_node_provision_state(self.node['uuid'],
                                                       'provide')
        self.wait_provisioning_state(self.node['uuid'],
                                     'available')
        self.update_node(self.node['uuid'], [{'op': 'replace',
                                            'path': '/instance_uuid',
                                            'value': None}])

class BaremetalIdracRedfishInspect(
        InspectBasicTest):
    inspect_interface = 'idrac-redfish'


class BaremetalIdracWSManInspect(
        InspectBasicTest):
    inspect_interface = 'idrac-wsman'
