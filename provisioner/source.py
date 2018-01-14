import logging
import opennms
import pyVim
import pyVim.connect
import pyVmomi

class Source(object):

    def __init__(self, name, parameters):
        self._name = name
        self._parameters = parameters
        self._logger = logging.getLogger("app")

    def get_parameter(self, name, default=None):
        output = default
        if name in self._parameters:
            output = self._parameters[name]
        return output

    def get_nodes(self):
        raise Exception("not implemented")
        pass


class SourceException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class DummySource(Source):

    def __init__(self, name, parameters):
        Source.__init__(self, name, parameters)

    def get_nodes(self):
        # create nodelist
        nodelist = []

        # get parameters from config
        cat1 = self.get_parameter("cat1", None)
        cat2 = self.get_parameter("cat2", None)

        # create testnode 1
        node_1 = opennms.Node("testnode1", "1")
        node_1.add_interface("127.0.0.1")
        node_1.add_service("127.0.0.1", "ICMP")
        node_1.add_service("127.0.0.1", "SNMP")
        node_1.add_asset("city", "Fulda")
        node_1.add_asset("zip", "36041")
        node_1.add_category("Test")
        if cat1:
            node_1.add_category(cat1)
        if cat2:
            node_1.add_category(cat2)

        # create testnode2
        node_2 = opennms.Node("testnode2", "2")
        node_2.add_interface("127.0.0.1")
        node_2.add_asset("city", "Fulda")
        node_2.add_asset("zip", "36041")
        node_2.add_category("Test")
        if cat1:
            node_2.add_category(cat1)
        if cat2:
            node_2.add_category(cat2)

        # add nodes to list and return nodelist
        nodelist.append(node_1)
        nodelist.append(node_2)
        return nodelist


class VmwareSource(Source):

    def __init__(self, name, parameters):
        Source.__init__(self, name, parameters)

    def get_nodes(self):
        # create nodelist
        nodelist = []

        # get parameters from config
        vmware_host = self.get_parameter("vmware_host", "localhost")
        vmware_port = self.get_parameter("vmware_port", "443")
        vmware_user = self.get_parameter("vmware_user", "admin")
        vmware_password = self.get_parameter("vmware_password", "admin")

        # connect to Vmware server
        try:
            vmware_serviceinstance = pyVim.connect.SmartConnectNoSSL(host=vmware_host,
                                                                     user=vmware_user, 
                                                                     pwd=vmware_password,
                                                                     port=int(vmware_port))
        except pyVmomi.vim.fault.InvalidLogin:
            raise SourceException("Vmware API: invalid login")
        except TimeoutError:
            raise SourceException("Vmware API: timeout connecting to API")

        # get rootFolder
        vmware_content = vmware_serviceinstance.RetrieveContent()
        vmware_folder = vmware_content.rootFolder

        # walk through entries in rootFolder
        vmware_view_type = [pyVmomi.vim.VirtualMachine]
        vmware_view_recursive = True
        vmware_view = vmware_content.viewManager.CreateContainerView(vmware_folder, vmware_view_type,
                                                                     vmware_view_recursive)

        # create node for every vm
        for vm in vmware_view.view:
            vm_hostname = vm.summary.config.name
            vm_ip = vm.summary.guest.ipAddress
            if vm_ip is not None:
                node = opennms.Node(vm_hostname, vm_hostname)
                node.add_interface(vm_ip)
                nodelist.append(node)
            else:
                self._logger.warn("VmwareSource: could not import VM {} with IP 'None'".format(vm_hostname))

        # close connection
        pyVim.connect.Disconnect(vmware_serviceinstance)

        # return nodelist
        return nodelist
