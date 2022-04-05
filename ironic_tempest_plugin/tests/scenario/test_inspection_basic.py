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

from tempest.common import utils
from tempest.config import CONF
from tempest.lib import decorators

from ironic_tempest_plugin.tests.scenario import baremetal_manager
from ironic_tempest_plugin.tests.scenario import introspection_manager


class InspectBasicTest(introspection_manager.InspectorScenarioTest):

    def verify_node_inspection_data(self, node):
        self.assertEqual(node['cpu_arch'],
                         self.flavor['properties']['cpu_arch'])
        self.assertGreaterEqual(int(data['properties']['memory_mb']), 0)
        self.assertGreaterEqual(int(data['properties']['cpus']), 0)

    def verify_node_flavor(self, node):
        expected_cpu_arch = self.flavor['properties']['cpu_arch']

        self.assertGreater(int(node['properties']['cpus']), 0)
        self.assertGreater(int(node['properties']['memory_mb']), 0)
        self.assertGreater(int(node['properties']['local_gb']), 0)
        self.assertEqual(expected_cpu_arch,
                         node['properties']['cpu_arch'])


    @decorators.idempotent_id('03bf7990-bee0-4dd7-bf74-b97ad7b52a4b')
    @utils.services('network')
    def test_baremetal_inspect(self):
        """This test case follows this set of operations:

            * Sets nodes to manageable state
            * Inspects nodes
            * Verifies all properties are inspected
            * Verifies inspection data
            * Sets node to available state

        """
        # prepare introspection rule
        #rule_path = self.get_rule_path("basic_ops_rule.json")
        #self.rule_import(rule_path)
        #self.addCleanup(self.rule_purge)

        for node_id in self.node_ids:
            self.introspect_node(node_id)

        # settle down introspection
        #self.wait_for_introspection_finished(self.node_ids)
        for node_id in self.node_ids:
            self.wait_provisioning_state(
                node_id, 'manageable',
                timeout=CONF.baremetal_introspection.ironic_sync_timeout,
                interval=self.wait_provisioning_state_interval)

        for node_id in self.node_ids:
            node = self.node_show(node_id)
            self.assertGreater(int(node['properties']['memory_mb']), 0)
            self.assertGreater(int(node['properties']['cpus']), 0)
            self.assertGreater(int(node['properties']['local_gb']), 0)

            #self.assertEqual('yes', node['extra']['rule_success'])
            #data_store = CONF.baremetal_introspection.data_store
            #if data_store is None:
                # Backward compatibility, the option is not set.
            #    data_store = ('swift' if CONF.service_available.swift
            #                  else 'none')
            #if data_store != 'none':
                #if not CONF.baremetal_introspection.skip_verification:
            #    self.verify_node_introspection_data(node)
            #self.verify_node_flavor(node)

        for node_id in self.node_ids:
            self.baremetal_client.set_node_provision_state(node_id, 'provide')

        for node_id in self.node_ids:
            self.wait_provisioning_state(
                node_id, baremetal_manager.BaremetalProvisionStates.AVAILABLE,
                timeout=CONF.baremetal.active_timeout,
                interval=self.wait_provisioning_state_interval)

        #self.wait_for_nova_aware_of_bvms()
        #self.add_keypair()
        #ins, _node = self.boot_instance()
        #self.terminate_instance(ins)

