# ----------------------------------------------------------------------------
# gsnodegraph Copyright 2019-2022 by Noah Rahm and contributors
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

import sys
import wx
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
except Exception:
    pass

from gsnodegraph import EVT_GSNODEGRAPH_ADDNODEBTN
from nodes import OutputNode, MixNode, ImageNode, BlurNode, BlendNode, ValueNode, FrequencyPhaseAlignementNode,AverageNode,RemoveBadAveragesNode,LineBroadeningNode,ZeroPaddingNode,EddyCurrentCorrectionNode,InputNode
from nodegraph import NodeGraph
import nodes


# Install a custom displayhook to keep Python from setting the global
# _ (underscore) to the value of the last evaluated expression.
# If we don't do this, our mapping of _ to gettext can get overwritten.
# This is useful/needed in interactive debugging with PyShell.
def _displayHook(obj):
    """ Custom display hook to prevent Python stealing '_'. """

    if obj is not None:
        print(repr(obj))
        
def get_node_type(node):
    if isinstance(node, nodes.nodes.ZeroPaddingNode):
        return "ZeroPadding"
    elif isinstance(node, nodes.nodes.RemoveBadAveragesNode):
        return "RemoveBadAverages"
    elif isinstance(node, nodes.nodes.FrequencyPhaseAlignementNode):
        return "FreqPhaseAlignment"
    elif isinstance(node, nodes.nodes.AverageNode):
        return "Average"
    elif isinstance(node, nodes.nodes.EddyCurrentCorrectionNode):
        return "EddyCurrentCorrection"
    elif isinstance(node, nodes.nodes.LineBroadeningNode):
        return "LineBroadening"
    else:
        return "Unknown steps"


# Add translation macro to builtin similar to what gettext does.
import builtins
builtins.__dict__['_'] = wx.GetTranslation


class MainApp(wx.App):

    def OnInit(self):

        # Work around for Python stealing "_".
        sys.displayhook = _displayHook

        return True


class MyFrame(wx.Frame):
    def __init__(self, parent, id=wx.ID_ANY, title=wx.EmptyString,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE, name="frame"):
        wx.Frame.__init__(self, parent, id, title, pos, size, style, name)

        # Setup the node registry
        node_registry = {
            "image_nodeid": ImageNode,
            "mix_nodeid": MixNode,
            "blur_nodeid": BlurNode,
            "blend_nodeid": BlendNode,
            "value_nodeid": ValueNode,
            "output_nodeid": OutputNode,
            ##All the line below are added for MRS software
            "freqphasealignement_nodeid": FrequencyPhaseAlignementNode,
            "average_nodeid":AverageNode,
            "removebadaverages_nodeid":RemoveBadAveragesNode,
            "linebroadening_nodeid":LineBroadeningNode,
            "zeropadding_nodeid":ZeroPaddingNode,
            "eddyccurentcorrection_nodeid":EddyCurrentCorrectionNode,
            "input_nodeid":InputNode

        }
        # Setup the config with datatypes and node categories
        config = {
            "image_datatype": "IMAGE",
            "node_datatypes": {
                "IMAGE": "#C6C62D",  # Yellow
                "INTEGER": "#A0A0A0",  # Grey
                "FLOAT": "#A0A0A0",  # Grey
                "VALUE": "#A0A0A0",  # Depreciated!
                "TRANSIENTS": "#B33641", 
            },
            "input_nodes_categories": ["INPUT"],
            "node_categories": {
                "INPUT": "#008000",  # Burgendy
                "DRAW": "#AF4467",  # Pink
                "MASK": "#084D4D",  # Blue-green
                "CONVERT": "#564B7C",  # Purple
                "FILTER": "#558333",  # Green
                "BLEND": "#498DB8",  # Light blue
                "QUALITY CONTROL": "#B33641",  # Light blue

                "COLOR": "#C2AF3A",  # Yellow
                "TRANSFORM": "#6B8B8B", # Blue-grey
                "OUTPUT": "#B33641"  # Red
            }
        }

        # Init the nodegraph
        self.ng = NodeGraph(self, registry=node_registry, config=config)

        # Add nodes to the node graph
        node1 = self.ng.AddNode("image_nodeid", pos=wx.Point(100, 10))
        node2 = self.ng.AddNode("output_nodeid", pos=wx.Point(450, 400))
        node3 = self.ng.AddNode("input_nodeid", pos=wx.Point(400, 100))
        node4 = self.ng.AddNode("eddyccurentcorrection_nodeid",nodeid='lol', pos=wx.Point(700, 100))
        node5 = self.ng.AddNode("zeropadding_nodeid", pos=wx.Point(720, 300))
        node6 = self.ng.AddNode("linebroadening_nodeid", pos=wx.Point(620, 430))
        node7 = self.ng.AddNode("removebadaverages_nodeid", pos=wx.Point(1000, 290))
        node8 = self.ng.AddNode("average_nodeid", pos=wx.Point(1200, 290))
        node9 = self.ng.AddNode("freqphasealignement_nodeid", pos=wx.Point(1200, 100))


        # Maximize the window
        self.Maximize(True)

        # Bind events
        self.ng.Bind(EVT_GSNODEGRAPH_ADDNODEBTN, self.OnAddNodeMenuBtn)
        self.Bind(wx.EVT_CLOSE, self.OnDestroy)

    def OnAddNodeMenuBtn(self, event):
        # print(self.ng.nodes['lol'].GetSockets().GetWires())
        current_node= self.ng.GetInputNode()
        pipeline =[]
        while current_node is not None:
            for socket in current_node.GetSockets():
                if socket.direction == 1:
                    if len(socket.GetWires())==0:
                        current_node=None
                    elif len(socket.GetWires())>1:
                        print("Error: Only allow serial pipeline for now (each node must be connected to only one another)")
                        current_node=None

                    else:
                        for wire in socket.GetWires():
                            current_node = wire.dstsocket.node
                            pipeline.append(get_node_type(wire.dstsocket.node))
                        
        print (pipeline)
                        
        # print(self.ng.GetInputNode())
        # print()
        # print(self.ng.nodes['lol'].GetSockets()[0].GetWires()[0].dstsocket.node)
        #  print(len(self.ng.nodes['lol'].GetSockets()[1].GetWires()))

    def OnDestroy(self, event):
        self.Destroy()


if __name__ == "__main__":
    app = MainApp()
    frame = MyFrame(None, size=(512, 512))
    frame.SetTitle("gsnodegraph demo")
    frame.Show()
    app.MainLoop()
    
