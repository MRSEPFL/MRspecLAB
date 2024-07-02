import wx
from .pipeline_nodegraph import NodeGraphPanel
from .node_properties import NodePropertiesPanel

### adapted from Gimel Studio
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
class NodeGraphDropTarget(wx.DropTarget):
    def __init__(self, window, *args, **kwargs):
        super(NodeGraphDropTarget, self).__init__(*args, **kwargs)
        self._window = window
        self._composite = wx.DataObjectComposite()
        self._textDropData = wx.TextDataObject()
        self._fileDropData = wx.FileDataObject()
        self._composite.Add(self._textDropData)
        self._composite.Add(self._fileDropData)
        self.SetDataObject(self._composite)

    def OnDrop(self, x, y):
        return True

    def OnData(self, x, y, result):
        self.GetData()
        formatType, formatId = self.GetReceivedFormatAndId()
        if formatType in (wx.DF_TEXT, wx.DF_UNICODETEXT): return self.OnTextDrop()
        elif formatType == wx.DF_FILENAME: return self.OnFileDrop()

    def GetReceivedFormatAndId(self):
        _format = self._composite.GetReceivedFormat()
        formatType = _format.GetType()
        try: formatId = _format.GetId()
        except Exception: formatId = None
        return formatType, formatId

    def OnTextDrop(self):
        try:
            self._window.AddNode(self._textDropData.GetText(), nodeid=None, pos=(0, 0), location="CURSOR")
            self._window.UpdateNodegraph()
        except Exception as error:
            self.ShowError(error)
        return wx.DragCopy

    def OnFileDrop(self):
        return wx.DragCopy

    def ShowError(self, error=""):
        dlg = wx.MessageDialog(None, "\n {}!".format(str(error)), _("Error!"), style=wx.ICON_ERROR)
        dlg.ShowModal()
        return False

class PipelineWindow(wx.Frame):
    def __init__(self, *args, **kw):
        super(PipelineWindow, self).__init__(*args, **kw)

        self.SetSize(wx.Size(1200, 500))
        self.mainpanel = wx.Panel(self, wx.ID_ANY)
        self.pipelinesizer= wx.BoxSizer(wx.HORIZONTAL)
        self.mainpanel.SetSizer(self.pipelinesizer)

        self.pipelinePanel = NodeGraphPanel(self.mainpanel, size=(100, 100))
        self.pipelinePanel.SetDropTarget(NodeGraphDropTarget(self.pipelinePanel))
        
        self.prop_pnl = NodePropertiesPanel(self.mainpanel,idname="PROPERTIES_PNL", menu_item=None,size=(600, 500))
        self.prop_pnl.SetSizeHints( 270,100)
        
        self.pipelinesizer.Add(self.pipelinePanel, 1, wx.ALL | wx.EXPAND, 5)
        self.pipelinesizer.Add(self.prop_pnl, 0, wx.ALL | wx.EXPAND, 5)
        
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.SetIcon(wx.Icon("resources/icon_32p.png"))

    def on_close(self, event):
        self.Hide()
        
        
