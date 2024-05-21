import wx
from . import PipelineNodeGraph
from gs.nodegraph_dnd import NodeGraphDropTarget
from gs.nodeproperties_pnl import NodePropertiesPanel

class PipelineWindow(wx.Frame):
    def __init__(self, *args, **kw):
        super(PipelineWindow, self).__init__(*args, **kw)

        self.SetSize(wx.Size(1200, 500))
        self.mainpanel = wx.Panel(self, wx.ID_ANY)
        self.pipelinesizer= wx.BoxSizer(wx.HORIZONTAL)
        self.mainpanel.SetSizer(self.pipelinesizer)

        self.pipelinePanel = PipelineNodeGraph.NodeGraphPanel(self.mainpanel, size=(100, 100))
        self.pipelinePanel.SetDropTarget(NodeGraphDropTarget(self.pipelinePanel))
        
        self.prop_pnl = NodePropertiesPanel(self.mainpanel,idname="PROPERTIES_PNL", menu_item=None,size=(600, 500))
        self.prop_pnl.SetSizeHints( 270,100)
        
        self.pipelinesizer.Add(self.pipelinePanel, 1, wx.ALL | wx.EXPAND, 5)
        self.pipelinesizer.Add(self.prop_pnl, 0, wx.ALL | wx.EXPAND, 5)
        
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.SetIcon(wx.Icon("resources/icon_32p.png"))

    def on_close(self, event):
        self.Hide()
        
        
