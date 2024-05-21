import wx

from gsnodegraph.gsnodegraph import (EVT_GSNODEGRAPH_NODESELECT,
                         EVT_GSNODEGRAPH_NODECONNECT,
                         EVT_GSNODEGRAPH_NODEDISCONNECT,
                         EVT_GSNODEGRAPH_MOUSEZOOM,
                         EVT_GSNODEGRAPH_ADDNODEBTN)
from gsnodegraph import nodegraph
from gsnodegraph.gsnodegraph.constants import SOCKET_OUTPUT

import constants as const
# from gimelstudio.gimelstudio.datafiles import (ICON_NODEGRAPH_PANEL, ICON_MOUSE_LMB_MOVEMENT, 
#                                    ICON_MOUSE_LMB, ICON_KEY_CTRL, ICON_MOUSE_MMB_MOVEMENT,
#                                    ICON_MOUSE_RMB)
from GimelStudio.addnode_menu import AddNodeMenu
from constants import(XISLAND1,XISLAND2,XISLAND3,XISLAND4,XISLAND5,XISLAND6)

ID_ADDNODEMENU = wx.NewIdRef()

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
except Exception:
    pass

from gsnodegraph.gsnodegraph import EVT_GSNODEGRAPH_ADDNODEBTN
from gsnodegraph.nodes import OutputNode, MixNode, ImageNode, BlurNode, BlendNode, ValueNode, FrequencyPhaseAlignementNode,AverageNode,RemoveBadAveragesNode,LineBroadeningNode,ZeroPaddingNode,EddyCurrentCorrectionNode,InputNode
from gsnodegraph.nodes import OutputNode
from gsnodegraph.nodegraph import NodeGraph
import gsnodegraph.nodes
# from steps.nodes.average_node import AverageNode
# from steps.nodes.eddycurrentcorrection_node import EddyCurrentCorrectionNode
# from steps.nodes.freqphasealignement_node import FrequencyPhaseAlignementNode
# from steps.nodes.linebroadening_node import LineBroadeningNode
# from steps.nodes.qualitymatrix_node import QualityMatrixNode
# from steps.nodes.removebadaverages_node import RemoveBadAveragesNode
# from steps.nodes.zeropadding_node import ZeroPaddingNode
# from GimelStudio.core import  NODE_REGISTRY

def _displayHook(obj):
    """ Custom display hook to prevent Python stealing '_'. """

    if obj is not None:
        print(repr(obj))
        
# def get_node_type(node):
#     if isinstance(node, gsnodegraph.nodes.nodes.ZeroPaddingNode):
#         return "ZeroPadding"
#     elif isinstance(node, gsnodegraph.nodes.nodes.RemoveBadAveragesNode):
#         return "RemoveBadAverages"
#     elif isinstance(node, gsnodegraph.nodes.nodes.FrequencyPhaseAlignementNode):
#         return "FreqPhaseAlignment"
#     elif isinstance(node, gsnodegraph.nodes.nodes.AverageNode):
#         return "Average"
#     elif isinstance(node, gsnodegraph.nodes.nodes.EddyCurrentCorrectionNode):
#         return "EddyCurrentCorrection"
#     elif isinstance(node, gsnodegraph.nodes.nodes.LineBroadeningNode):
#         return "LineBroadening"
#     else:
#         return "Unknown steps"

# def get_node_type(node):
#     if isinstance(node, gsnodegraph.nodes.nodes.AverageNode):
#         return "Average"
#     else:
#         return "Unknown steps"


# Add translation macro to builtin similar to what gettext does.
import builtins
builtins.__dict__['_'] = wx.GetTranslation







from GimelStudio.core import NODE_REGISTRY

# from steps.import_node.node_importer import *

# class NodeGraph(NodeGraphBase):
#     def __init__(self, parent, registry, config, *args, **kwds):
#         NodeGraphBase.__init__(self, parent, registry, config, *args, **kwds)

#     @property
#     def GLSLRenderer(self):
#         return self.parent.GLSLRenderer


class NodeGraphPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                          size=wx.DefaultSize, style=wx.NO_BORDER | wx.TAB_TRAVERSAL)

        # self.registry = kwargs["registry"]
        self.parent = parent

        self.SetBackgroundColour(XISLAND1)

        self.BuildUI()

    def BuildUI(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        topbar = wx.Panel(self)
        topbar.SetBackgroundColour(XISLAND1)

        topbar_sizer = wx.GridBagSizer(vgap=1, hgap=1)





        # topbar_sizer.Add(self.zoom_field, (0, 4), flag=wx.ALL, border=3)
        topbar_sizer.Add((10, 10), (0, 5), flag=wx.ALL, border=3)
        topbar_sizer.AddGrowableCol(2)

        topbar.SetSizer(topbar_sizer)

        
        self.available_registery_nodes = NODE_REGISTRY
        
        print(self.available_registery_nodes)
        self.available_registery_nodes = dict(sorted(self.available_registery_nodes.items()))

        # self.available_registery_nodes= NODE_REGISTRY
        # print(NODE_REGISTRY)
        self.registry =self.available_registery_nodes.copy()
        self.registry["input_nodeid"] = InputNode
        # Setup the config with datatypes and node categories
        config = {
            "image_datatype": "IMAGE",
            "node_datatypes": {
                "IMAGE": "#C6C62D",  # Yellow
                "INTEGER": "#A0A0A0",  # Grey
                "FLOAT": "#A0A0A0",  # Grey
                "VECTOR":"#A0A0A0",
                "VALUE": "#A0A0A0",  # Depreciated!
                "TRANSIENTS": "#FFA07A", 
            },
            "input_nodes_categories": ["INPUT"],
            "node_categories": {
                "INPUT": "#32CD32",  # Burgendy     008000
                "DRAW": "#AF4467",  # Pink
                "MASK": "#084D4D",  # Blue-green
                "CONVERT": "#564B7C",  # Purple
                "FILTER": "#558333",  # Green
                "BLEND": "#498DB8",  # Light blue
                "QUALITY CONTROL": "#02ccfe",  # Light blue  B33641   ff00fe

                "COLOR": "#C2AF3A",  # Yellow
                "TRANSFORM": "#6B8B8B", # Blue-grey
                "OUTPUT": "#B33641"  # Red
            }
        }

        self.nodegraph = NodeGraph(self, registry=self.registry, 
                                   config=config,
                                   size=(-1, self.Size[0]-20))

        # # Add default image and output node
        # image_node = self.nodegraph.AddNode('corenode_image', pos=wx.Point(150, 150))
        # image_node.ToggleExpand()
        # output_node = self.nodegraph.AddNode('corenode_outputcomposite', pos=wx.Point(1200, 250))

        # For testing during development
        # Add nodes to the node graph
        node1 = self.nodegraph.AddNode("input_nodeid", nodeid= 'input0', pos=wx.Point(200, 100))
        node2 = self.nodegraph.AddNode("ZeroPadding",nodeid='zeropadding_node0', pos=wx.Point(400, 120))
        node3 = self.nodegraph.AddNode("LineBroadening", nodeid='linebroadening0',pos=wx.Point(600, 100))
        node4 = self.nodegraph.AddNode("FreqPhaseAlignment",nodeid='freqphasealignement0', pos=wx.Point(800, 120))
        node5 = self.nodegraph.AddNode("EddyCurrentCorrection",nodeid='eddyccurentcorrection0', pos=wx.Point(1000, 100))
        node6 = self.nodegraph.AddNode("RemoveBadAverages",nodeid='removebadaverages0', pos=wx.Point(1200, 120))
        node7 = self.nodegraph.AddNode("Average", nodeid='average0', pos=wx.Point(1400, 100))
        # Connect the nodes by default
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['input0'].GetSockets()[0],self.nodegraph.nodes['zeropadding_node0'].GetSockets()[1])
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['zeropadding_node0'].GetSockets()[0],self.nodegraph.nodes['linebroadening0'].GetSockets()[1])
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['linebroadening0'].GetSockets()[0],self.nodegraph.nodes['freqphasealignement0'].GetSockets()[1])
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['freqphasealignement0'].GetSockets()[0],self.nodegraph.nodes['eddyccurentcorrection0'].GetSockets()[1])
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['eddyccurentcorrection0'].GetSockets()[0],self.nodegraph.nodes['removebadaverages0'].GetSockets()[1])
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['removebadaverages0'].GetSockets()[0],self.nodegraph.nodes['average0'].GetSockets()[1])

        main_sizer.Add(topbar, flag=wx.EXPAND | wx.LEFT | wx.RIGHT)
        main_sizer.Add(self.nodegraph, 1, flag=wx.EXPAND | wx.BOTH)

        self.SetSizer(main_sizer)

        self.nodegraph.Bind(EVT_GSNODEGRAPH_NODESELECT, self.UpdateNodePropertiesPnl)
        # self.nodegraph.Bind(EVT_GSNODEGRAPH_NODECONNECT, self.NodeConnectEvent)
        # self.nodegraph.Bind(EVT_GSNODEGRAPH_NODEDISCONNECT, self.NodeDisconnectEvent)
        # self.nodegraph.Bind(EVT_GSNODEGRAPH_MOUSEZOOM, self.ZoomNodeGraph)
        self.nodegraph.Bind(EVT_GSNODEGRAPH_ADDNODEBTN, self.OnAddNodeMenuButton)
        # self.parent.Bind(wx.EVT_MENU, self.OnAddNodeMenu, id=ID_ADDNODEMENU)

        # Keyboard shortcut bindings
        # self.accel_tbl = wx.AcceleratorTable([(wx.ACCEL_SHIFT, ord('A'),
        #                                        ID_ADDNODEMENU)])
        # self.parent.SetAcceleratorTable(self.accel_tbl)

    @property
    def AUIManager(self):
        return self.parent._mgr

    @property
    def NodeGraph(self):
        return self.nodegraph

    @property
    def PropertiesPanel(self):
        return self.parent.Parent.prop_pnl ##changed for MRSoftware

    @property
    def GLSLRenderer(self):
        return self.parent.glsl_renderer

    @property
    def ImageViewport(self):
        return self.parent.imageviewport_pnl

    def AddNode(self, idname, nodeid, pos, location):
        return self.nodegraph.AddNode(idname, nodeid, pos, location)

    def UpdateNodegraph(self):
        self.nodegraph.UpdateNodeGraph()

    def UpdateNodePropertiesPnl(self, event):
        self.PropertiesPanel.UpdatePanelContents(event.value)

    # def NodeConnectEvent(self, event):
    #     self.parent.Render()

    # def NodeDisconnectEvent(self, event):
    #     pass

    # def ChangeZoom(self, event):
    #     level = event.value / 100.0
    #     # print(level, " <---> ", event.value)
    #     # if event.value > 60 and event.value < 310:
    #     self.nodegraph.SetZoomLevel(level)

    # def ZoomNodeGraph(self, event):
    #     self.zoom_field.SetValue(event.value)
    #     self.zoom_field.UpdateDrawing()
    #     self.zoom_field.Refresh()

    def PopupAddNodeMenu(self, pos):
        self.addnodemenu = AddNodeMenu(self, self.available_registery_nodes,
                                       size=wx.Size(250, self.Size[1] - 50))
        self.addnodemenu.Position(pos, (2, 2))
        self.addnodemenu.SetSize(250, 400)
        if self.addnodemenu.IsShown() is not True:
            self.addnodemenu.Show()

    def OnAddNodeMenu(self, event):
        pos = wx.GetMousePosition()
        pos = (pos[0]-125, pos[1]-100)
        self.PopupAddNodeMenu(pos)
        
    def OnAddNodeMenuButton(self, event):
        pos = (8, self.nodegraph.GetRect()[3]-310)
        self.PopupAddNodeMenu(pos)
        current_node= self.nodegraph.GetInputNode()
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
