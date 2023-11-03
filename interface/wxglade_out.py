import wx
import os
# import matplotlib_canvas
from . import matplotlib_canvas  # Use a relative import to import wxglade_out


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
        ext = filenames[0].rsplit(os.path.sep, 1)[1].rsplit(".", 1)[1]
        if not all([f.endswith(ext) for f in filenames]):
            print("Inconsistent file types")
            return False
        if ext.lower() != "coord" and ext.lower().strip() != "ima":
            print("Invalid file type")
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
        open_ima = wx.MenuItem(fileMenu, wx.ID_ANY, "&Open .IMA", "Open .IMA files")
        open_coord = wx.MenuItem(fileMenu, wx.ID_ANY, "&Open .coord", "Open .coord file")
        fileMenu.Append(open_ima)
        fileMenu.Append(open_coord)
        self.Bind(wx.EVT_MENU, self.on_read_ima, open_ima)
        self.Bind(wx.EVT_MENU, self.on_read_coord, open_coord)
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
        self.notebook_1_pane_2 = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.notebook_1_pane_2, "Quality Control Steps")
        

        available_icons_sizer = wx.GridSizer(rows=3, cols=2, hgap=5, vgap=5)
        available_icon_labels = ["ZeroPadding", "LineBroadening", "FreqPhaseAlignment", "RemoveBadAverages","Average"]
        
        for label in available_icon_labels:
            icon_label = wx.StaticText(self.notebook_1_pane_2 , label=label, style=wx.ALIGN_CENTER)
            icon_label.SetBackgroundColour(wx.Colour(100, 100, 100))
            icon_label.SetForegroundColour(wx.Colour(250, 250, 250))

            icon_label.Bind(wx.EVT_LEFT_DOWN, self.OnAddStep)
            available_icons_sizer.Add(icon_label, 1, wx.ALL | wx.EXPAND, 5)
        
        self.notebook_1_pane_2 .SetSizer(available_icons_sizer)
        
        
        
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
        self.pipelinePanel = wx.Panel(self.pipelineplotSplitter, wx.ID_ANY)
        self.pipelineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.pipelinePanel.SetSizer(self.pipelineSizer)
        
        self.list_ctrl = wx.ListCtrl(self.pipelinePanel,style=wx.BORDER_SUNKEN|wx.LC_REPORT)
        self.list_ctrl.InsertColumn(0, "Pipeline Steps", width = 100)

        self.list_ctrl.InsertItem(0, "ZeroPadding")
        self.list_ctrl.InsertItem(1, "LineBroadening")
        self.list_ctrl.InsertItem(2, "FreqPhaseAlignment")
        self.list_ctrl.InsertItem(3, "RemoveBadAverages")
        self.list_ctrl.InsertItem(4, "Average")

        
        self.pipelineparameters = wx.TextCtrl(self.pipelinePanel, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.pipelineparameters.SetBackgroundColour(wx.Colour(200, 200, 200))  # Set the background color to black
        
        self.context_menu_pipeline = wx.Menu()
        self.context_menu_pipeline.Append(1, "Delete step")
        self.context_menu_pipeline.Append(2, "Plot step Results")

        
        self.Bind(wx.EVT_MENU, self.OnDeleteClick, id=1)
        self.Bind(wx.EVT_MENU, self.OnPlotClick, id=2)

        self.list_ctrl.Bind(wx.EVT_CONTEXT_MENU, self.OnRightClickList)

        
        # self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)


        
        self.pipelineSizer.Add(self.list_ctrl, 0, wx.EXPAND, 0)
        self.pipelineSizer.Add(self.pipelineparameters, 1, wx.EXPAND, 0)

        
        
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
        




    
    
