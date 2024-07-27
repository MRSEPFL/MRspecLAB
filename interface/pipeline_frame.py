import wx
import os
import pickle
from . import utils
from .pipeline_nodegraph import NodeGraphPanel
from .node_properties import NodePropertiesPanel
from .colours import XISLAND1
import interface.images as images

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

class PipelineFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(PipelineFrame, self).__init__(*args, **kw)
        self.SetSize(wx.Size(1200, 500))

        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.panel = wx.Panel(self.splitter)
        self.panel.SetBackgroundColour(wx.Colour(XISLAND1)) 
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.load_button = wx.Button(self.panel, wx.ID_ANY, "Load")
        self.load_button.SetMinSize((-1, 25))
        self.load_button.SetToolTip("Load a pipeline from a .pipe file")
        
        self.save_button = wx.Button(self.panel, wx.ID_ANY, "Save")
        self.save_button.SetMinSize((-1, 25))
        self.save_button.SetToolTip("Save the pipeline to a .pipe file")
        
        self.clear_button = wx.Button(self.panel, wx.ID_ANY, "Clear")
        self.clear_button.SetMinSize((-1, 25))
        self.clear_button.SetToolTip("Clear the pipeline")
        
        self.button_sizer.Add(self.load_button, 0, wx.ALL | wx.EXPAND, 5)
        self.button_sizer.Add(self.save_button, 0, wx.ALL | wx.EXPAND, 5)
        self.button_sizer.Add(self.clear_button, 0, wx.ALL | wx.EXPAND, 5)

        self.node_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.node_sizer)
        self.prop_panel = NodePropertiesPanel(self.splitter)
        self.prop_panel.SetMinSize((300, -1))
        self.node_panel = NodeGraphPanel(self.panel, self.prop_panel, size=(100, 100))
        self.node_panel.SetDropTarget(NodeGraphDropTarget(self.node_panel))
        self.node_sizer.Add(self.button_sizer, 0, wx.EXPAND, 0)
        self.node_sizer.Add(self.node_panel, 1, wx.EXPAND, 0)


        self.splitter.SplitVertically(self.panel, self.prop_panel, -100)
        self.splitter.SetMinimumPaneSize(100)
        self.splitter.SetSashGravity(1)

        self.Bind(wx.EVT_BUTTON, self.on_load_pipeline, self.load_button)
        self.Bind(wx.EVT_BUTTON, self.on_save_pipeline, self.save_button)
        self.Bind(wx.EVT_BUTTON, self.on_clear, self.clear_button)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.SetIcon(images.icon_img_32.GetIcon())

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
        nodes = dict(self.node_panel.nodegraph.nodes)
        for n in nodes.keys():
            params = [(v.idname, v.value) for k, v in nodes[n].properties.items()]
            tosave.append([nodes[n].idname, nodes[n].id, nodes[n].pos, params])
        tosave = [tosave]
        wires = list(self.node_panel.nodegraph.wires)
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
        self.node_panel.nodegraph.nodes = {}
        self.node_panel.nodegraph.wires = []
        for data in toload[0]:
            self.node_panel.nodegraph.AddNode(data[0], data[1], data[2])
            for p in data[3]:
                self.node_panel.nodegraph.nodes[data[1]].properties[p[0]].value = p[1]
        for data in toload[1]:
            src = self.node_panel.nodegraph.nodes[data[0]].FindSocket(data[1])
            dst = self.node_panel.nodegraph.nodes[data[2]].FindSocket(data[3])
            self.node_panel.nodegraph.ConnectNodes(src, dst)
        self.node_panel.nodegraph.Refresh()
        self.Parent.retrieve_pipeline()
        self.Parent.update_statusbar()
        event.Skip()

    def on_clear(self, event):
        self.node_panel.nodegraph.nodes = {}
        self.node_panel.nodegraph.wires = []
        self.node_panel.nodegraph.AddNode("input_nodeid", nodeid= 'input0', pos=wx.Point(0, 100))
        self.node_panel.nodegraph.Refresh()
        self.Parent.retrieve_pipeline()
        self.Parent.update_statusbar()
        event.Skip()
