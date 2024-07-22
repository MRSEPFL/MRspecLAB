import wx
import os
import pickle
from . import utils
from .pipeline_nodegraph import NodeGraphPanel
from .node_properties import NodePropertiesPanel
from .colours import XISLAND1
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
        dlg = wx.MessageDialog(None, "\n {}!".format(str(error)), "Error!", style=wx.ICON_ERROR)
        dlg.ShowModal()
        return False

class PipelineWindow(wx.Frame):
    def __init__(self, *args, **kw):
        super(PipelineWindow, self).__init__(*args, **kw)
        self.SetSize(wx.Size(1200, 500))
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.pipelinePanel = NodeGraphPanel(self.splitter, size=(100, 100))
        self.pipelinePanel.SetDropTarget(NodeGraphDropTarget(self.pipelinePanel))
        self.prop_pnl = NodePropertiesPanel(self.splitter)
        self.prop_pnl.SetMinSize((300, -1))
        self.splitter.SplitVertically(self.pipelinePanel, self.prop_pnl, -100)
        self.splitter.SetMinimumPaneSize(100)
        self.splitter.SetSashGravity(1)

        fileMenu = wx.Menu()
        menuBar = wx.MenuBar()
        menuBar.SetBackgroundColour(wx.Colour(XISLAND1))
        menuBar.Append(fileMenu, "&File")
        self.SetMenuBar(menuBar)

        load_pipeline = wx.MenuItem(fileMenu, wx.ID_ANY, "&Load Pipeline", "Load .pipe file")
        save_pipeline = wx.MenuItem(fileMenu, wx.ID_ANY, "&Save Pipeline", "Save .pipe file")
        fileMenu.Append(load_pipeline)
        fileMenu.Append(save_pipeline)
        self.Bind(wx.EVT_MENU, self.on_load_pipeline, load_pipeline)
        self.Bind(wx.EVT_MENU, self.on_save_pipeline, save_pipeline)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.SetIcon(wx.Icon("resources/icon_32p.png"))

    def on_close(self, event):
        self.Parent.retrieve_pipeline()
        self.Parent.update_statusbar()
        self.Hide()
        
    def on_save_pipeline(self, event, filepath=None):
        self.Parent.retrieve_pipeline()
        if self.Parent.steps == []:
            utils.log_warning("No pipeline to save")
            return
        if filepath is None:
            fileDialog = wx.FileDialog(self, "Save pipeline as", wildcard="Pipeline files (*.pipe)|*.pipe", defaultDir=self.Parent.rootPath, style=wx.FD_SAVE)
            if fileDialog.ShowModal() == wx.ID_CANCEL: return
            filepath = fileDialog.GetPath()
        if filepath == "":
            utils.log_error(f"File not found")
            return
        tosave = []
        nodes = dict(self.pipelinePanel.nodegraph.nodes)
        for n in nodes.keys():
            params = [(v.idname, v.value) for k, v in nodes[n].properties.items()]
            tosave.append([nodes[n].idname, nodes[n].id, nodes[n].pos, params])
        tosave = [tosave]
        wires = list(self.pipelinePanel.nodegraph.wires)
        tosave.append([[w.srcsocket.node.id, w.srcsocket.idname, w.dstsocket.node.id, w.dstsocket.idname] for w in wires])
        with open(filepath, 'wb') as f:
            pickle.dump(tosave, f)
        if event is not None: event.Skip()

    def on_load_pipeline(self, event):
        fileDialog = wx.FileDialog(self, "Choose a file", wildcard="Pipeline files (*.pipe)|*.pipe", defaultDir=self.Parent.rootPath, style=wx.FD_OPEN)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepath = fileDialog.GetPath()
        if filepath == "" or not os.path.exists(filepath):
            utils.log_error("File not found: " + filepath)
            return
        with open(filepath, 'rb') as f:
            toload = pickle.load(f)
        self.pipelinePanel.nodegraph.nodes = {}
        self.pipelinePanel.nodegraph.wires = []
        for data in toload[0]:
            self.pipelinePanel.nodegraph.AddNode(data[0], data[1], data[2])
            for p in data[3]:
                self.pipelinePanel.nodegraph.nodes[data[1]].properties[p[0]].value = p[1]
        for data in toload[1]:
            src = self.pipelinePanel.nodegraph.nodes[data[0]].FindSocket(data[1])
            dst = self.pipelinePanel.nodegraph.nodes[data[2]].FindSocket(data[3])
            self.pipelinePanel.nodegraph.ConnectNodes(src, dst)
        self.pipelinePanel.nodegraph.Refresh()
        self.Parent.retrieve_pipeline()
        self.Parent.update_statusbar()
        event.Skip()
