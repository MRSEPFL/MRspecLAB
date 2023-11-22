from . import PipelineNodeGraph
from GimelStudio.nodegraph_dnd import NodeGraphDropTarget

import wx

SomeNewEvent, EVT_SOME_NEW_EVENT = wx.lib.newevent.NewEvent()

class PipelineWindow(wx.Frame):
    def __init__(self, *args, **kw):
        super(PipelineWindow, self).__init__(*args, **kw)


        self.pipelinePanel  = PipelineNodeGraph.NodeGraphPanel(self, size=(100, 100))
        self.pipelinePanel.SetDropTarget(NodeGraphDropTarget(self.pipelinePanel))
        
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        self.Hide()