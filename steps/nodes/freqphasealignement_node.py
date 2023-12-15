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
from ..FreqPhaseAlignment import FreqPhaseAlignment


class FrequencyPhaseAlignementNode(api.Node):
    def __init__(self, nodegraph, id):
        api.Node.__init__(self, nodegraph, id)
        self.label = "Frequency and Phase Alignement"
        self.processing_step=FreqPhaseAlignment()


    @property
    def NodeMeta(self):
        meta_info = {
            "label": "Frequency and Phase Alignement",
            "author": "MRSoftware",
            "version": (0, 0, 0),
            "category": "QUALITY CONTROL",
            "description": "Perform both the Frequency and Phase Alignement on the received transients",
        }
        return meta_info

    def NodeInitProps(self):
        transients = api.TransientsProp(
            idname="in_transients",
        )
        alignFreq = api.ChoiceProp(
            idname="alignFreq",
            default="True",
            choices=["True", "False"],
            exposed=False,
            fpb_label="Align Frequency"
        )
        alignPhase = api.ChoiceProp(
            idname="alignPhase",
            default="True",
            choices=["True", "False"],
            exposed=False,
            fpb_label="Align Phase"
        )
        freqRange=api.VectorProp(
            idname="freqRange", 
            default=(3, 3.2, 0), 
            labels=("Lower Bound", "Higher Bound"),
            min_vals=(0, 0, 0), 
            max_vals=(6, 6, 0),
            exposed=False,
            show_p=False, 
            fpb_label="Frequency Range Peak Alignement"
        )
        median = api.ChoiceProp(
            idname="median",
            default="True",
            choices=["True", "False"],
            exposed=False,
            fpb_label="Median"
        )
        target = api.IntegerProp(
            idname="target",
            default=0,
            min_val=0,
            max_val=1000,
            show_p=True,
            exposed=False,
            fpb_label="Align to transient #"
        )
        

        self.NodeAddProp(transients)
        self.NodeAddProp(alignFreq)
        self.NodeAddProp(alignPhase)
        self.NodeAddProp(median)
        self.NodeAddProp(freqRange)

        self.NodeAddProp(target)


    def NodeInitOutputs(self):
        self.outputs = {
            "transients": api.Output(idname="transients", datatype="TRANSIENTS", label="Transients")
        }
        
    #Added for MRSoftware
    #Assume idname of propertie of the node is the same as name of the keys of the parameter dictionary   
    def EditParametersProcessing(self):
        for key, value in self.properties.items():
            if key == "freqRange":
               self.processing_step.parameters[key] = self.properties[key].value[:-1]
            elif key in self.processing_step.parameters:
                self.processing_step.parameters[key] = self.properties[key].value

            





api.RegisterNode(FrequencyPhaseAlignementNode, "freqphasealignement_nodeid")
