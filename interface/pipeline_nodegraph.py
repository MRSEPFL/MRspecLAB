import wx

from gs.registry import NODE_REGISTRY
from .node_add import AddNodeMenu
from utils.colours import(XISLAND1)

ID_ADDNODEMENU = wx.NewIdRef()
import ctypes
try: ctypes.windll.shcore.SetProcessDpiAwareness(True)
except Exception: pass

#Added for MRS software to fix a bug in the UI (disable connection from input to output)
from gsnodegraph import (NodeBase, NodeGraphBase, EVT_GSNODEGRAPH_NODESELECT, EVT_GSNODEGRAPH_ADDNODEBTN)
from gsnodegraph.constants import SOCKET_INPUT
        
import builtins
builtins.__dict__['_'] = wx.GetTranslation

class Output(object):
    def __init__(self, idname, datatype, label, visible=True):
        self.idname = idname
        self.datatype = datatype
        self.label = label 
        self.visible = visible

class InputNode(NodeBase):
    """ Example node showing an input node. """
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)

        self.label = "Input"
        self.category = "INPUT"
        self.is_input = True

        self.outputs = {
            "Output": Output(idname="transients", datatype="TRANSIENTS", label="Output")
        }

class NodeGraph(NodeGraphBase): # modified for MRS software
    def __init__(self, parent, registry, config, *args, **kwargs):
        NodeGraphBase.__init__(self, parent, registry, config, *args, **kwargs)

    def OnLeftUp(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)

        # Clear selection bbox and set nodes as selected
        if self.bbox_rect != None:
            self.sel_nodes = self.BoxSelectHitTest(self.bbox_rect)
            for node in self.sel_nodes:
                if node.IsSelected() != True and node.IsActive() != True:
                    node.SetSelected(True)

        # Attempt to make a connection
        if self.src_node != None:
            dst_node = self.HitTest(winpnt)
            
            if dst_node is not None:
                dst_socket = dst_node.HitTest(winpnt)

                # Make sure not to allow different datatypes or
                # the same 'socket type' to be connected!
                if dst_socket is not None:
                    if (self.src_socket.direction != dst_socket.direction
                        and self.src_socket.datatype == dst_socket.datatype
                        and self.src_node != dst_node):

                        # Only allow a single wire to be connected to any one input.
                        if self.SocketHasWire(dst_socket) is not True:
                            #Added for MRS software to fix a bug in the UI (disable connection from input to output)

                            if dst_socket.direction is SOCKET_INPUT:
                                self.ConnectNodes(self.src_socket, dst_socket)

                        # If there is already a connection,
                        # but a wire is "dropped" into the socket
                        # disconnect the last connection and
                        # connect the current wire.
                        else:
                            for wire in self.wires:
                                if wire.dstsocket == dst_socket:
                                    dst = wire.dstsocket
                                    src = wire.srcsocket
                                    self.DisconnectNodes(src, dst)

                            self.ConnectNodes(self.src_socket, dst_socket)

            # Send event to update the properties panel
            if self.last_active_node is None:
                self.SendNodeSelectEvent()
            if self.last_active_node is not self.src_node:
                self.SendNodeSelectEvent()
            self.last_active_node = self.src_node


        # Reset all values
        self.src_node = None
        self.src_socket = None
        self.tmp_wire = None
        self.bbox_start = None
        self.bbox_rect = None

        # Update add node button and send button event if it was clicked
        pnt = event.GetPosition()
        if self.MouseInAddNodeBtn(pnt) is True:
            self.addnode_btn.SetClicked(False)
            self.SendAddNodeBtnEvent()

        # Refresh the nodegraph
        self.UpdateNodeGraph()

    def OnDeleteNode(self, event):
        if (self.active_node != None and
            self.active_node.IsOutputNode() != True and not isinstance(self.active_node, InputNode)): ##Changed for MRS
            self.DeleteNode(self.active_node)
            self.active_node = None

        # Update the properties panel so that the deleted
        # nodes' properties are not still shown!
        self.SendNodeSelectEvent()

        self.UpdateNodeGraph()

    def DeleteNodes(self):
        """ Delete the currently selected nodes. This will refuse
        to delete the Output Composite node though, for obvious reasons.
        """
        for node in self.sel_nodes:
            if (node.IsOutputNode() != True and not isinstance(node, InputNode)):##Changed for MRS
                self.DeleteNode(node)
            else:
                # In the case that this is an output node, we
                # want to deselect it, not delete it. :)
                node.SetSelected(False)
        self.sel_nodes = []

        if (self.active_node != None and
            self.active_node.IsOutputNode() != True and not isinstance(node, InputNode)):##Changed for MRS
            self.DeleteNode(self.active_node)
            self.active_node = None

        # Update the properties panel so that the deleted
        # nodes' properties are not still shown!
        self.SendNodeSelectEvent()

        self.UpdateNodeGraph()

    def DuplicateNode(self, node):
        """ Duplicates the given ``Node`` object with its properties.
        :param node: the ``Node`` object to duplicate
        :returns: the duplicate ``Node`` object
        """
        if (node.IsOutputNode() is not True and not isinstance(node, InputNode)): #changed for MRS softfare
            duplicate_node = self.AddNode(node.GetIdname(), location="CURSOR")

            # TODO: Assign the same properties to the duplicate node object

            self.UpdateNodeGraph()
            return duplicate_node
    
    def GetInputNode(self): ##added for MRS Software
        """ Return the input node object. """
        for node_id in self.nodes:
            node = self.nodes[node_id]
            # if node.IsInputNode():
            if isinstance(node, InputNode):
                return node
    
    def DisconnectNodes(self, src_socket, dst_socket):
        for wire in self.wires:
            if wire.srcsocket is src_socket and wire.dstsocket is dst_socket:
                self.wires.remove(wire)
                src_socket.wires.remove(wire)        #Added for MRS software, because when there is a  disconnection the list of the socket does not suppress the wire
                dst_socket.wires.remove(wire)        #Added for MRS software, because when there is a  disconnection the list of the socket does not suppress the wire
                wire.dstsocket.node.EditConnection(wire.dstsocket.idname, None, None)

        self.SendNodeDisconnectEvent()

class NodeGraphPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.NO_BORDER | wx.TAB_TRAVERSAL)
        self.parent = parent
        self.SetBackgroundColour(XISLAND1)
        self.BuildUI()

    def BuildUI(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        topbar = wx.Panel(self)
        topbar.SetBackgroundColour(XISLAND1)
        topbar_sizer = wx.GridBagSizer(vgap=1, hgap=1)
        topbar_sizer.Add((10, 10), (0, 5), flag=wx.ALL, border=3)
        topbar_sizer.AddGrowableCol(2)
        topbar.SetSizer(topbar_sizer)
        self.available_registery_nodes = NODE_REGISTRY
        # print(self.available_registery_nodes)
        self.available_registery_nodes = dict(sorted(self.available_registery_nodes.items()))
        self.registry =self.available_registery_nodes.copy()
        self.registry["input_nodeid"] = InputNode
        config = {
            "image_datatype": "IMAGE",
            "node_datatypes": {
                "IMAGE": "#C6C62D",  # Yellow
                "INTEGER": "#A0A0A0",  # Grey
                "FLOAT": "#A0A0A0",  # Grey
                "VECTOR":"#A0A0A0",
                "VALUE": "#A0A0A0",
                "TRANSIENTS": "#FFA07A", 
            },
            "input_nodes_categories": ["INPUT"],
            "node_categories": {
                "INPUT": "#329D32",
                "COIL_COMBINATION": "#B06000",
                "PROCESSING": "#D08000",
                "QUALITY_CONTROL": "#028cae",
                "OUTPUT": "#B33641"
            }
        }

        self.nodegraph = NodeGraph(self, registry=self.registry, config=config, size=(-1, self.Size[0]-20))

        # For testing during development
        # Add nodes to the node graph
        node1 = self.nodegraph.AddNode("input_nodeid", nodeid= 'input0', pos=wx.Point(0, 100))
        node11 = self.nodegraph.AddNode("CoilCombinationAdaptive", nodeid= 'coil_combination_svd', pos=wx.Point(200, 100))
        node2 = self.nodegraph.AddNode("ZeroPadding",nodeid='zeropadding_node0', pos=wx.Point(400, 120))
        node3 = self.nodegraph.AddNode("LineBroadening", nodeid='linebroadening0',pos=wx.Point(600, 100))
        node4 = self.nodegraph.AddNode("FreqPhaseAlignment",nodeid='freqphasealignement0', pos=wx.Point(800, 120))
        node5 = self.nodegraph.AddNode("EddyCurrentCorrection",nodeid='eddyccurentcorrection0', pos=wx.Point(1000, 100))
        node6 = self.nodegraph.AddNode("RemoveBadAverages",nodeid='removebadaverages0', pos=wx.Point(1200, 120))
        node7 = self.nodegraph.AddNode("Average", nodeid='average0', pos=wx.Point(1400, 100))
        # Connect the nodes by default
        # self.nodegraph.ConnectNodes(self.nodegraph.nodes['input0'].GetSockets()[0],self.nodegraph.nodes['zeropadding_node0'].GetSockets()[1])
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['input0'].GetSockets()[0],self.nodegraph.nodes['coil_combination_svd'].GetSockets()[1])
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['coil_combination_svd'].GetSockets()[0],self.nodegraph.nodes['zeropadding_node0'].GetSockets()[1])
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['zeropadding_node0'].GetSockets()[0],self.nodegraph.nodes['linebroadening0'].GetSockets()[1])
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['linebroadening0'].GetSockets()[0],self.nodegraph.nodes['freqphasealignement0'].GetSockets()[1])
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['freqphasealignement0'].GetSockets()[0],self.nodegraph.nodes['eddyccurentcorrection0'].GetSockets()[1])
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['eddyccurentcorrection0'].GetSockets()[0],self.nodegraph.nodes['removebadaverages0'].GetSockets()[1])
        self.nodegraph.ConnectNodes(self.nodegraph.nodes['removebadaverages0'].GetSockets()[0],self.nodegraph.nodes['average0'].GetSockets()[1])

        main_sizer.Add(topbar, flag=wx.EXPAND | wx.LEFT | wx.RIGHT)
        main_sizer.Add(self.nodegraph, 1, flag=wx.EXPAND | wx.BOTH)
        self.SetSizer(main_sizer)
        self.nodegraph.Bind(EVT_GSNODEGRAPH_NODESELECT, self.UpdateNodePropertiesPnl)
        self.nodegraph.Bind(EVT_GSNODEGRAPH_ADDNODEBTN, self.OnAddNodeMenuButton) 

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

    def PopupAddNodeMenu(self, pos):
        self.addnodemenu = AddNodeMenu(self, self.available_registery_nodes, size=wx.Size(250, self.Size[1] - 50))
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
        # current_node= self.nodegraph.GetInputNode()
        # pipeline =[]
        # while current_node is not None:
        #     for socket in current_node.GetSockets():
        #         if socket.direction == 1:
        #             if len(socket.GetWires())==0:
        #                 current_node = None
        #             elif len(socket.GetWires())>1:
        #                 print("Error: Only allow serial pipeline for now (each node must be connected to only one another)")
        #                 current_node = None
        #             else:
        #                 for wire in socket.GetWires():
        #                     current_node = wire.dstsocket.node
        #                     pipeline.append(get_node_type(wire.dstsocket.node))
