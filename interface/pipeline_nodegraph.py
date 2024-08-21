import wx
from interface.node_add import AddNodeMenu
from interface.colours import XISLAND1
from processing.api.registry import NODE_REGISTRY, RegisterNode
from gsnodegraph import NodeBase, NodeGraphBase, NodeWire, EVT_GSNODEGRAPH_NODESELECT, EVT_GSNODEGRAPH_ADDNODEBTN
from gsnodegraph.constants import SOCKET_INPUT, SOCKET_OUTPUT

import builtins
builtins.__dict__['_'] = wx.GetTranslation # for gsnodegraph

class Output(object):
    def __init__(self, idname, datatype, label, visible=True):
        self.idname = idname
        self.datatype = datatype
        self.label = label 
        self.visible = visible

class InputNode(NodeBase):
    def __init__(self, nodegraph, _id):
        NodeBase.__init__(self, nodegraph, _id)
        self.label = "Input"
        self.category = "INPUT"
        self.is_input = True
        self.outputs = {
            "Output": Output(idname="transients", datatype="TRANSIENTS", label="Output")
        }

class NodeGraph(NodeGraphBase):
    def __init__(self, parent, prop_panel, *args, **kwargs):
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
        NodeGraphBase.__init__(self, parent, NODE_REGISTRY, config, *args, **kwargs)
        self.Bind(EVT_GSNODEGRAPH_NODESELECT, self.UpdateNodePropertiesPnl)
        self.Bind(EVT_GSNODEGRAPH_ADDNODEBTN, self.OnAddNodeMenuButton) 

        self.PropertiesPanel = prop_panel
        self.addnodemenu = None
        self.SetBackgroundColour(XISLAND1)
        RegisterNode(InputNode, "input_nodeid")
        self.load_default_pipeline()

    def UpdateNodePropertiesPnl(self, event):
        self.PropertiesPanel.UpdatePanelContents(event.value)

    def OnAddNodeMenuButton(self, event):
        if self.addnodemenu is not None and self.addnodemenu.IsShown():
            self.addnodemenu.Close()
            return
        pos = wx.GetMousePosition()
        registry = NODE_REGISTRY.copy()
        registry.pop("input_nodeid")
        self.addnodemenu = AddNodeMenu(self, registry, size=wx.Size(250, 400))
        self.addnodemenu.Position(pos, (0, 0))
        self.addnodemenu.SetSize((250, 400))
        self.addnodemenu.Show()

    def OnLeftDown(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)

        if event.ShiftDown():
            self.middle_pnt = winpnt

        self.src_node = self.HitTest(winpnt)
        if self.src_node is not None:
            self.HandleNodeSelection()
            self.src_socket = self.src_node.HitTest(winpnt)
            if self.src_socket is not None:
                if self.src_socket.direction == SOCKET_OUTPUT:
                    pnt1 = self.src_node.pos + self.src_socket.pos
                    self.tmp_wire = NodeWire(self, pnt1, winpnt, None, None, self.src_socket.direction, self.wire_curvature)
                else:
                    for wire in self.wires:
                        if wire.dstsocket == self.src_socket:
                            dst = wire.dstsocket
                            self.src_socket = wire.srcsocket
                            self.DisconnectNodes(self.src_socket, dst)
                    self.UpdateNodeGraph()

                    if self.src_socket.direction == SOCKET_OUTPUT:
                        pnt = event.GetPosition()
                        winpnt = self.CalcMouseCoords(pnt)
                        pnt1 = self.src_socket.node.pos + self.src_socket.pos
                        self.tmp_wire = NodeWire(self, pnt1, winpnt, None, None, self.src_socket.direction, self.wire_curvature)
                        self.src_node = self.src_socket.node

        else:
            self.bbox_start = winpnt
            self.DeselectNodes()
            if self.MouseInAddNodeBtn(pnt) is True: self.addnode_btn.SetClicked(True)

        self.last_pnt = winpnt
        self.UpdateNodeGraph()

    def OnLeftUp(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)

        if self.bbox_rect != None: # select nodes in box
            self.sel_nodes = self.BoxSelectHitTest(self.bbox_rect)
            for node in self.sel_nodes:
                if node.IsSelected() != True and node.IsActive() != True:
                    node.SetSelected(True)

        if self.src_node != None:
            dst_node = self.HitTest(winpnt)
            if dst_node is not None:
                dst_socket = dst_node.HitTest(winpnt)
                if dst_socket is not None: # connect nodes
                    if (self.src_socket.direction != dst_socket.direction and self.src_socket.datatype == dst_socket.datatype and self.src_node != dst_node):
                        if not self.SocketHasWire(dst_socket):
                            if dst_socket.direction is SOCKET_INPUT:
                                self.ConnectNodes(self.src_socket, dst_socket)
                        else:
                            for wire in self.wires:
                                if wire.dstsocket == dst_socket:
                                    dst = wire.dstsocket
                                    src = wire.srcsocket
                                    self.DisconnectNodes(src, dst)
                            self.ConnectNodes(self.src_socket, dst_socket)
                            
            if self.last_active_node is None: self.SendNodeSelectEvent()
            if self.last_active_node is not self.src_node: self.SendNodeSelectEvent()
            self.last_active_node = self.src_node

        self.src_node = None
        self.src_socket = None
        self.tmp_wire = None
        self.bbox_start = None
        self.bbox_rect = None
        
        pnt = event.GetPosition()
        if self.MouseInAddNodeBtn(pnt) is True:
            self.addnode_btn.SetClicked(False)
            self.SendAddNodeBtnEvent()
        self.UpdateNodeGraph()

    def OnDeleteNode(self, event):
        if (self.active_node != None and
            self.active_node.IsOutputNode() != True and not isinstance(self.active_node, InputNode)): ##Changed for MRS
            self.DeleteNode(self.active_node)
            self.active_node = None
        self.SendNodeSelectEvent()
        self.UpdateNodeGraph()

    def DeleteNodes(self):
        for node in self.sel_nodes:
            if (node.IsOutputNode() != True and not isinstance(node, InputNode)):
                self.DeleteNode(node)
            else:
                node.SetSelected(False)
        self.sel_nodes = []

        if (self.active_node != None and self.active_node.IsOutputNode() != True and not isinstance(node, InputNode)):
            self.DeleteNode(self.active_node)
            self.active_node = None
        self.SendNodeSelectEvent()
        self.UpdateNodeGraph()

    def DuplicateNode(self, node):
        if (node.IsOutputNode() is not True and not isinstance(node, InputNode)):
            duplicate_node = self.AddNode(node.GetIdname(), location="CURSOR")
            self.UpdateNodeGraph()
            return duplicate_node
    
    def GetInputNode(self):
        for node_id in self.nodes:
            node = self.nodes[node_id]
            if isinstance(node, InputNode):
                return node
    
    def DisconnectNodes(self, src_socket, dst_socket):
        for wire in self.wires:
            if wire.srcsocket is src_socket and wire.dstsocket is dst_socket:
                self.wires.remove(wire)
                src_socket.wires.remove(wire)
                dst_socket.wires.remove(wire)
                wire.dstsocket.node.EditConnection(wire.dstsocket.idname, None, None)
        self.SendNodeDisconnectEvent()
    
    def OnMotion(self, event):
        pnt = event.GetPosition()
        winpnt = self.CalcMouseCoords(pnt)

        if event.Dragging() and ((event.LeftIsDown() and event.ShiftDown()) or event.MiddleIsDown()): # pan graph
            dx = int(winpnt[0] - self.middle_pnt[0])
            dy = int(winpnt[1] - self.middle_pnt[1])
            self.ScrollNodeGraph(dx, dy)
            self.ScenePostPan(dx, dy)
            self.UpdateNodeGraph()

        elif event.LeftIsDown():
            if self.src_node is None and self.bbox_start != None: # draw selection box
                rect = wx.Rect(topLeft=self.bbox_start, bottomRight=winpnt)
                self.bbox_rect = rect
                self.UpdateNodeGraph()

            if event.Dragging():
                if self.src_node != None:
                    if self.src_socket is None:
                        if self.sel_nodes != []: # move selected nodes
                            for node in self.sel_nodes:
                                dpnt = node.pos + winpnt - self.last_pnt
                                node.pos = dpnt
                        else: # move selected node
                            dpnt = self.src_node.pos + winpnt - self.last_pnt
                            self.src_node.pos = dpnt
                        self.last_pnt = winpnt
                        for wire in self.wires:
                            wire.pnt1 = wire.srcnode.pos + wire.srcsocket.pos
                            wire.pnt2 = wire.dstnode.pos + wire.dstsocket.pos
                        self.UpdateNodeGraph()

                    elif self.tmp_wire != None: # move wire
                        self.tmp_wire.active = True
                        if winpnt != None:
                            self.tmp_wire.pnt2 = winpnt
                        self.UpdateNodeGraph()

        else: # add node button
            if self.addnode_btn.IsClicked() is not True:
                if self.MouseInAddNodeBtn(pnt): self.addnode_btn.SetFocused(True)
                else: self.addnode_btn.SetFocused(False)
            self.UpdateNodeGraph()

    def OnDrawInterface(self, dc):
        self.addnode_btn.Draw(dc, self.ConvertCoords(wx.Point(10, 10)))

    def clear(self):
        self.nodes = {}
        self.wires = []
        self.AddNode("input_nodeid", nodeid= 'input0', pos=wx.Point(0, 100))
        self.Refresh()
    
    def load_default_pipeline(self):
        self.clear()
        self.AddNode("input_nodeid", nodeid= 'input0', pos=wx.Point(0, 100))
        self.AddNode("CoilCombinationAdaptive", nodeid= 'coil_combination_svd', pos=wx.Point(200, 100))
        self.AddNode("FreqPhaseAlignment",nodeid='freqphasealignement0', pos=wx.Point(400, 120))
        self.AddNode("EddyCurrentCorrection",nodeid='eddyccurentcorrection0', pos=wx.Point(600, 100))
        self.AddNode("RemoveBadAverages",nodeid='removebadaverages0', pos=wx.Point(800, 120))
        self.AddNode("Average", nodeid='average0', pos=wx.Point(1000, 100))
        self.ConnectNodes(self.nodes['input0'].GetSockets()[0],self.nodes['coil_combination_svd'].GetSockets()[1])
        self.ConnectNodes(self.nodes['coil_combination_svd'].GetSockets()[0],self.nodes['freqphasealignement0'].GetSockets()[1])
        self.ConnectNodes(self.nodes['freqphasealignement0'].GetSockets()[0],self.nodes['eddyccurentcorrection0'].GetSockets()[1])
        self.ConnectNodes(self.nodes['eddyccurentcorrection0'].GetSockets()[0],self.nodes['removebadaverages0'].GetSockets()[1])
        self.ConnectNodes(self.nodes['removebadaverages0'].GetSockets()[0],self.nodes['average0'].GetSockets()[1])