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
###Modified to suit MRSoftware
import api
from ..RemoveBadAverages import RemoveBadAverages


class RemoveBadAveragesNode(api.Node):
    def __init__(self, nodegraph, id):
        api.Node.__init__(self, nodegraph, id)
        self.label = "Remove Bad Averages"
        self.processing_step=RemoveBadAverages()

    @property
    def NodeMeta(self):
        meta_info = {
            "label": "Remove Bad Averages",
            "author": "MRSoftware",
            "version": (0, 0, 0),
            "category": "QUALITY CONTROL",
            "description": "Remove bad quality transients",
        }
        return meta_info

    def NodeInitProps(self):
        transients = api.TransientsProp(
            idname="in_transients",
        )
        stdDevThreshold = api.IntegerProp(
            idname="stdDevThreshold",
            default=3,
            min_val=1,
            max_val=10,
            show_p=True,
            exposed=False,
            fpb_label="STD threshold"
        )
        domain = api.ChoiceProp(
            idname="domain",
            default="time",
            choices=["time", "freq"],
            exposed=False,
            fpb_label="Domain"
        )
        tmax = api.FloatProp(
            idname="tmax",
            default=0.4,
            min_val=0.1,
            max_val=20.0,
            fpb_label="tmax",
            exposed=False
        )
        


        

        self.NodeAddProp(transients)
        self.NodeAddProp(stdDevThreshold)
        self.NodeAddProp(domain)
        self.NodeAddProp(tmax)


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




# api.RegisterNode(RemoveBadAveragesNode, "removebadaverages_nodeid")
