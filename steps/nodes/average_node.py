# ----------------------------------------------------------------------------
# Gimel Studio Copyright 2019-2023 by the Gimel Studio project contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------


###the template of the nodes comes from GimelStudio

import api
# from gsnodegraph.gsnodegraph.node import NodeBase
# from gsnodegraph.nodes.nodes import Output, TransientsProp
# class AverageNode(NodeBase):
#     """ Example node showing an input node. """
#     def __init__(self, nodegraph, _id):
#         NodeBase.__init__(self, nodegraph, _id)

#         self.label = "Average"
#         self.category = "QUALITY CONTROL"

#         self.outputs = {
#             "transients": Output(idname="transients", datatype="TRANSIENTS", label="Transients")
#         }
#         self.properties = {
#             "transients_socketid": TransientsProp("transients_socketid", label="Transients")
#         }
from ..Average import Average
class AverageNode(api.Node):
    def __init__(self, nodegraph, id):
        api.Node.__init__(self, nodegraph, id)
        self.label = "Average"
        self.processing_step=Average()

    @property
    def NodeMeta(self):
        meta_info = {
            "label": "Average",
            "author": "MRSoftware",
            "version": (0, 0, 0),
            "category": "QUALITY CONTROL",
            "description": "Perform the average of the signals received",
        }
        return meta_info

    def NodeInitProps(self):
        transients = api.TransientsProp(
            idname="in_transients",
        )


        self.NodeAddProp(transients)
 

    def NodeInitOutputs(self):
        self.outputs = {
            "transients": api.Output(idname="transients", datatype="TRANSIENTS", label="Transients")
        }
        
    #Added for MRSoftware
    #Assume idname of propertie of the node is the same as name of the keys of the parameter dictionary   
    def EditParametersProcessing(self):
        for key, value in self.properties.items():
            if key in self.processing_step.parameters:
                self.processing_step.parameters[key] = self.properties[key].value




api.RegisterNode(AverageNode, "average_nodeid")
