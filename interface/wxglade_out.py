import wx
import os
# import matplotlib_canvas
from . import matplotlib_canvas  # Use a relative import to import wxglade_out
from . import DragList


import sys
import wx
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
except Exception:
    pass

from gsnodegraph.gsnodegraph import EVT_GSNODEGRAPH_ADDNODEBTN
from gsnodegraph.nodes import OutputNode, MixNode, ImageNode, BlurNode, BlendNode, ValueNode, FrequencyPhaseAlignementNode,AverageNode,RemoveBadAveragesNode,LineBroadeningNode,ZeroPaddingNode,EddyCurrentCorrectionNode,InputNode
from gsnodegraph.nodegraph import NodeGraph
import gsnodegraph.nodes


# Install a custom displayhook to keep Python from setting the global
# _ (underscore) to the value of the last evaluated expression.
# If we don't do this, our mapping of _ to gettext can get overwritten.
# This is useful/needed in interactive debugging with PyShell.
def _displayHook(obj):
    """ Custom display hook to prevent Python stealing '_'. """

    if obj is not None:
        print(repr(obj))
        
def get_node_type(node):
    if isinstance(node, gsnodegraph.nodes.nodes.ZeroPaddingNode):
        return "ZeroPadding"
    elif isinstance(node, gsnodegraph.nodes.nodes.RemoveBadAveragesNode):
        return "RemoveBadAverages"
    elif isinstance(node, gsnodegraph.nodes.nodes.FrequencyPhaseAlignementNode):
        return "FreqPhaseAlignment"
    elif isinstance(node, gsnodegraph.nodes.nodes.AverageNode):
        return "Average"
    elif isinstance(node, gsnodegraph.nodes.nodes.EddyCurrentCorrectionNode):
        return "EddyCurrentCorrection"
    elif isinstance(node, gsnodegraph.nodes.nodes.LineBroadeningNode):
        return "LineBroadening"
    else:
        return "Unknown steps"


# Add translation macro to builtin similar to what gettext does.
import builtins
builtins.__dict__['_'] = wx.GetTranslation



class FileDrop(wx.FileDropTarget):

    def __init__(self, listbox, label):
        wx.FileDropTarget.__init__(self)
        self.list = listbox
        self.label = label
        self.dropped_file_paths = []
        self.wrefindex = None

    def OnDropFiles(self, x, y, filenames):
        if len(filenames) == 0:
            self.clear_button.Disable()
            self.water_ref_button.Disable()
            return False
        self.label.SetLabel(filenames[0].rsplit(os.path.sep, 1)[0])
        self.list.Set([f.rsplit(os.path.sep, 1)[1] for f in filenames])
        self.clear_button.Enable()
        if filenames[0].lower().endswith(".coord"):
            self.water_ref_button.Disable() # no processing for .coords
        else: self.water_ref_button.Enable()
        self.dropped_file_paths = filenames
        self.dropped_file_paths.sort() # get correct sorting for wrefindex
        return True
    
    def on_clear(self, event):
        self.dropped_file_paths = []
        self.label.SetLabel("Drop Inputs Files Here")
        self.list.Set([])
        self.clear_button.Disable()
        self.water_ref_button.Disable()
        print("filepaths cleared")
        event.Skip()

    def on_water_ref(self, event):
        newindex = self.list.GetSelection()
        if newindex == wx.NOT_FOUND:
            print("No file selected")
            return
        self.list.SetItemBackgroundColour(newindex, wx.Colour(171, 219, 227))
        if self.wrefindex is not None:
            self.list.SetItemBackgroundColour(self.wrefindex, self.list.GetBackgroundColour())
        self.wrefindex = newindex
        print("water reference set to " + self.list.GetStrings()[self.wrefindex])
        event.Skip()

class MyFrame(wx.Frame):

    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        WIDTH = 1200
        HEIGHT = 800
        self.SetSize((WIDTH, HEIGHT))
        self.SetTitle("MRSprocessing")

        fileMenu = wx.Menu()
        viewMenu = wx.Menu()
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(viewMenu, "&View")
        self.SetMenuBar(menuBar)

        open_ima = wx.MenuItem(fileMenu, wx.ID_ANY, "&Open DICOM files (.ima, .dcm)", "Open .ima or .dcm files")
        open_twix = wx.MenuItem(fileMenu, wx.ID_ANY, "&Open Twix files (.dat)", "Open .dat files")
        open_coord = wx.MenuItem(fileMenu, wx.ID_ANY, "&Open COORD file", "Open .coord file")
        load_pipeline = wx.MenuItem(fileMenu, wx.ID_ANY, "&Load Pipeline", "Load .pipe file")
        save_pipeline = wx.MenuItem(fileMenu, wx.ID_ANY, "&Save Pipeline", "Save .pipe file")
        fileMenu.Append(open_ima)
        fileMenu.Append(open_twix)
        fileMenu.Append(open_coord)
        fileMenu.AppendSeparator()
        fileMenu.Append(load_pipeline)
        fileMenu.Append(save_pipeline)
        self.Bind(wx.EVT_MENU, self.on_read_ima, open_ima)
        self.Bind(wx.EVT_MENU, self.on_read_twix, open_twix)
        self.Bind(wx.EVT_MENU, self.on_read_coord, open_coord)
        self.Bind(wx.EVT_MENU, self.on_load_pipeline, load_pipeline)
        self.Bind(wx.EVT_MENU, self.on_save_pipeline, save_pipeline)

        self.toggle_editor = wx.MenuItem(viewMenu, wx.ID_ANY, "&Hide Editor", "Toggle Editor")
        viewMenu.Append(self.toggle_editor)
        self.Bind(wx.EVT_MENU, self.on_toggle_editor, self.toggle_editor)
        
        

        self.mainSplitter = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.rightSplitter = wx.SplitterWindow(self.mainSplitter, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)       
        self.leftSplitter = wx.SplitterWindow(self.mainSplitter, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.pipelineplotSplitter = wx.SplitterWindow(self.rightSplitter, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.consoleinfoSplitter = wx.SplitterWindow(self.rightSplitter, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)

        self.mainSplitter.SetMinimumPaneSize(100)
        self.rightSplitter.SetMinimumPaneSize(100)  
        self.leftSplitter.SetMinimumPaneSize(100)


        self.leftPanel = wx.Panel(self.leftSplitter, wx.ID_ANY)
        self.leftSizer = wx.BoxSizer(wx.VERTICAL)
        self.leftPanel.SetSizer(self.leftSizer)
        self.rightPanel = wx.Panel(self.pipelineplotSplitter, wx.ID_ANY)
        self.rightSizer = wx.BoxSizer(wx.VERTICAL)
        self.rightPanel.SetSizer(self.rightSizer)
        
        


        ### LEFT PANEL ###
        ## notebook of available steps
        self.notebook_1 = wx.Notebook(self.leftSplitter, wx.ID_ANY, style=wx.NB_BOTTOM)
        self.notebook_1_pane_1 = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.notebook_1_pane_1, "Import Data Steps")
        self.notebook_1_pane_2 = wx.ScrolledWindow(self.notebook_1, wx.ID_ANY)

        self.notebook_1.AddPage(self.notebook_1_pane_2, "Quality Control Steps")
        

        self.notebook_1_pane_2.SetScrollRate(10, 10)  # Set scroll rate (adjust as needed)
        
        available_icons_sizer = wx.GridSizer(rows=3, cols=2, hgap=5, vgap=5)
        available_icon_labels = ["ZeroPadding", "LineBroadening", "FreqPhaseAlignment", "RemoveBadAverages", "Average"]

        for label in available_icon_labels:
            # Create a button with the specified label
            icon_button = wx.Button(self.notebook_1_pane_2, label=label)
            
            # Set the fixed size for the button (e.g., 100x100 pixels)
            icon_button.SetMinSize((120, 100))

            # Set the background and foreground colors for the button
            # icon_button.SetBackgroundColour(wx.Colour(100, 100, 100))
            # icon_button.SetForegroundColour(wx.Colour(250, 250, 250))
            icon_button.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

            # Bind the event for the button (if needed)
            icon_button.Bind(wx.EVT_BUTTON, self.OnAddStep)

            # Add the button to the sizer with wx.ALIGN_CENTER_HORIZONTAL flag
            available_icons_sizer.Add(icon_button, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        self.notebook_1_pane_2.SetSizer(available_icons_sizer)

        
        
        self.clear_button = wx.Button(self.leftPanel, wx.ID_ANY, "Clear Inputs")
        self.water_ref_button = wx.Button(self.leftPanel, wx.ID_ANY, "Set Selection as Water Reference")
        self.leftSizer.Add(self.clear_button, 0, wx.ALL | wx.EXPAND, 5)
        self.leftSizer.Add(self.water_ref_button, 0, wx.ALL | wx.EXPAND, 5)
        self.clear_button.Disable()
        self.water_ref_button.Disable()

        self.drag_and_drop_list = wx.ListBox(self.leftPanel, wx.ID_ANY, choices=[], style=wx.LB_SINGLE | wx.LB_NEEDED_SB | wx.HSCROLL | wx.LB_SORT | wx.LB_OWNERDRAW)
        self.drag_and_drop_label = wx.StaticText(self.leftPanel, wx.ID_ANY, "Drop Inputs Files Here", style=wx.ALIGN_CENTRE_VERTICAL)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.read_file, self.drag_and_drop_list)

        self.leftSizer.Add(self.drag_and_drop_label, 0, wx.ALL | wx.EXPAND, 5)
        self.leftSizer.Add(self.drag_and_drop_list, 1, wx.ALL | wx.EXPAND, 5)

        self.leftSplitter.SplitHorizontally(self.notebook_1, self.leftPanel, 300)

        ### RIGHT PANEL ###
        self.button_processing = wx.Button(self.rightPanel, wx.ID_ANY, "Start Processing", style=wx.BORDER_SUNKEN)
        self.button_processing.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.matplotlib_canvas = matplotlib_canvas.MatplotlibCanvas(self.rightPanel, wx.ID_ANY)
        self.infotext = wx.TextCtrl(self.consoleinfoSplitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        
        self.consoltext = wx.TextCtrl(self.consoleinfoSplitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.consoltext.SetBackgroundColour(wx.Colour(0, 0, 0))  # Set the background color to black
        self.consoltext.SetForegroundColour(wx.Colour(255, 255, 255))

        self.rightSizer.Add(self.button_processing, 0, wx.ALL | wx.EXPAND, 5)
        self.rightSizer.Add(self.matplotlib_canvas, 1, wx.ALL | wx.EXPAND, 0)
        self.rightSizer.Add(self.matplotlib_canvas.toolbar, 0, wx.EXPAND, 0)
        




        ## pipelinepart ##
        # self.pipelinePanel = wx.Panel(self.pipelineplotSplitter, wx.ID_ANY)
        # self.pipelineSizer = wx.BoxSizer(wx.HORIZONTAL)
        # self.pipelinePanel.SetSizer(self.pipelineSizer)
        
        #pipeline node graph directly imported from a modified version of the main  of gsnodegraph
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
        self.pipelinePanel = NodeGraph(self.pipelineplotSplitter, registry=node_registry, config=config)

        # Add nodes to the node graph
        node1 = self.pipelinePanel.AddNode("input_nodeid", nodeid= 'input0', pos=wx.Point(200, 100))
        node2 = self.pipelinePanel.AddNode("zeropadding_nodeid",nodeid='zeropadding_node0', pos=wx.Point(400, 120))
        node3 = self.pipelinePanel.AddNode("linebroadening_nodeid", nodeid='linebroadening0',pos=wx.Point(600, 100))
        node4 = self.pipelinePanel.AddNode("freqphasealignement_nodeid",nodeid='freqphasealignement0', pos=wx.Point(800, 120))
        node5 = self.pipelinePanel.AddNode("eddyccurentcorrection_nodeid",nodeid='eddyccurentcorrection0', pos=wx.Point(1000, 100))
        node6 = self.pipelinePanel.AddNode("removebadaverages_nodeid",nodeid='removebadaverages0', pos=wx.Point(1200, 120))
        node7 = self.pipelinePanel.AddNode("average_nodeid", nodeid='average0', pos=wx.Point(1400, 100))
        self.pipelinePanel.ConnectNodes(self.pipelinePanel.nodes['input0'].GetSockets()[0],self.pipelinePanel.nodes['zeropadding_node0'].GetSockets()[1])
        self.pipelinePanel.ConnectNodes(self.pipelinePanel.nodes['zeropadding_node0'].GetSockets()[0],self.pipelinePanel.nodes['linebroadening0'].GetSockets()[1])
        self.pipelinePanel.ConnectNodes(self.pipelinePanel.nodes['linebroadening0'].GetSockets()[0],self.pipelinePanel.nodes['freqphasealignement0'].GetSockets()[1])
        self.pipelinePanel.ConnectNodes(self.pipelinePanel.nodes['freqphasealignement0'].GetSockets()[0],self.pipelinePanel.nodes['eddyccurentcorrection0'].GetSockets()[1])
        self.pipelinePanel.ConnectNodes(self.pipelinePanel.nodes['eddyccurentcorrection0'].GetSockets()[0],self.pipelinePanel.nodes['removebadaverages0'].GetSockets()[1])
        self.pipelinePanel.ConnectNodes(self.pipelinePanel.nodes['removebadaverages0'].GetSockets()[0],self.pipelinePanel.nodes['average0'].GetSockets()[1])



        # Maximize the window
        self.Maximize(True)

        # Bind events
        self.pipelinePanel.Bind(EVT_GSNODEGRAPH_ADDNODEBTN, self.OnAddNodeMenuBtn)
        
        
        
        # self.list_ctrl = DragList.MyDragList(self.pipelinePanel,style=wx.BORDER_SUNKEN|wx.LC_REPORT)
        # self.list_ctrl.InsertColumn(0, "Pipeline Steps", width = 100)

        # self.list_ctrl.InsertItem(0, "ZeroPadding")
        # self.list_ctrl.InsertItem(1, "LineBroadening")
        # self.list_ctrl.InsertItem(2, "FreqPhaseAlignment")
        # self.list_ctrl.InsertItem(3, "EddyCurrentCorrection")
        # self.list_ctrl.InsertItem(4, "RemoveBadAverages")
        # self.list_ctrl.InsertItem(5, "Average")




        # self.pipelineparameters = wx.TextCtrl(self.pipelinePanel, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        # self.pipelineparameters.SetBackgroundColour(wx.Colour(200, 200, 200))  # Set the background color to black
        
        # self.context_menu_pipeline = wx.Menu()
        # self.context_menu_pipeline.Append(1, "Delete step")
        # self.context_menu_pipeline.Append(2, "Plot step Results")

        
        # self.Bind(wx.EVT_MENU, self.OnDeleteClick, id=1)
        # self.Bind(wx.EVT_MENU, self.OnPlotClick, id=2)

        # self.list_ctrl.Bind(wx.EVT_CONTEXT_MENU, self.OnRightClickList)

        
        # self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)


        
        # self.pipelineSizer.Add(self.list_ctrl, 0, wx.EXPAND, 0)
        # self.pipelineSizer.Add(self.pipelineparameters, 1, wx.EXPAND, 0)

        
        
        self.rightSplitter.SplitHorizontally(self.pipelineplotSplitter, self.consoleinfoSplitter, -150)
        self.rightSplitter.SetSashGravity(1.)
        
        self.consoleinfoSplitter.SplitVertically(self.consoltext, self.infotext, -150)
        self.consoleinfoSplitter.SetSashGravity(1.)
        
        

        
        self.pipelineplotSplitter.SplitVertically(self.pipelinePanel,self.rightPanel , -150)
        self.pipelineplotSplitter.SetSashGravity(1.)
        
        




        self.mainSplitter.SplitVertically(self.leftSplitter, self.rightSplitter, 300)
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.on_button_processing, self.button_processing)
        self.dt = FileDrop(self.drag_and_drop_list, self.drag_and_drop_label)
        self.leftPanel.SetDropTarget(self.dt)
        self.dt.clear_button = self.clear_button
        self.dt.water_ref_button = self.water_ref_button
        self.Bind(wx.EVT_BUTTON, self.dt.on_clear, self.clear_button)
        self.Bind(wx.EVT_BUTTON, self.dt.on_water_ref, self.water_ref_button)

    def on_button_processing(self, event): # wxGlade: MyFrame.<event_handler>
        print("Event handler 'on_button_processing' not implemented!")
        event.Skip()
        
    def OnAddNodeMenuBtn(self, event):
        # print(self.ng.nodes['lol'].GetSockets().GetWires())
        current_node= self.pipelinePanel.GetInputNode()
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

        




    
    
