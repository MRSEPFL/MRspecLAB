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
        if len(filenames) > 0:
            self.label.SetLabel(filenames[0].rsplit(os.path.sep, 1)[0])
            self.list.Set([f.rsplit(os.path.sep, 1)[1] for f in filenames])
            self.clear_button.Enable()
            self.water_ref_button.Enable()
            for i in range(self.list.GetCount()):
                self.list.SetItemBackgroundColour(i, wx.Colour(255, 255, 255))
            self.dropped_file_paths = filenames
            self.dropped_file_paths.sort() # get correct sorting for wrefindex
        else:
            self.clear_button.Disable()
            self.water_ref_button.Disable()
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
            self.list.SetItemBackgroundColour(self.wrefindex, wx.Colour(255, 255, 255))
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
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        self.SetMenuBar(menuBar)
        open_ima = wx.MenuItem(fileMenu, wx.ID_ANY, "&Open .IMA", "Open .IMA files")
        open_coord = wx.MenuItem(fileMenu, wx.ID_ANY, "&Open .coord", "Open .coord file")
        fileMenu.Append(open_ima)
        fileMenu.Append(open_coord)
        self.Bind(wx.EVT_MENU, self.on_read_ima, open_ima)
        self.Bind(wx.EVT_MENU, self.on_read_coord, open_coord)

        self.splitter = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.splitter.SetMinimumPaneSize(100)

        self.leftPanel = wx.Panel(self.splitter, wx.ID_ANY)
        self.leftSizer = wx.BoxSizer(wx.VERTICAL)
        self.leftPanel.SetSizer(self.leftSizer)
        self.rightPanel = wx.Panel(self.splitter, wx.ID_ANY)
        self.rightSizer = wx.BoxSizer(wx.VERTICAL)
        self.rightPanel.SetSizer(self.rightSizer)
        self.splitter.SplitVertically(self.leftPanel, self.rightPanel, 300)

        ### LEFT PANEL ###
        self.clear_button = wx.Button(self.leftPanel, wx.ID_ANY, "Clear Inputs")
        self.water_ref_button = wx.Button(self.leftPanel, wx.ID_ANY, "Set Selection as Water Reference")
        self.leftSizer.Add(self.clear_button, 0, wx.ALL | wx.EXPAND, 5)
        self.leftSizer.Add(self.water_ref_button, 0, wx.ALL | wx.EXPAND, 5)
        self.clear_button.Disable()
        self.water_ref_button.Disable()

        self.drag_and_drop_list = wx.ListBox(self.leftPanel, wx.ID_ANY, choices=[], style=wx.LB_SINGLE | wx.LB_NEEDED_SB | wx.HSCROLL | wx.LB_SORT | wx.LB_OWNERDRAW)
        self.drag_and_drop_label = wx.StaticText(self.leftPanel, wx.ID_ANY, "Drop Inputs Files Here", style=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTRE_VERTICAL)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.on_select, self.drag_and_drop_list)

        self.leftSizer.Add(self.drag_and_drop_label, 0, wx.ALL | wx.EXPAND, 5)
        self.leftSizer.Add(self.drag_and_drop_list, 1, wx.ALL | wx.EXPAND, 5)

        ### RIGHT PANEL ###
        self.button_processing = wx.Button(self.rightPanel, wx.ID_ANY, "Start Processing", style=wx.BORDER_SUNKEN)
        self.button_processing.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.rightSizer.Add(self.button_processing, 0, wx.ALL | wx.EXPAND, 5)

        self.matplotlib_canvas = matplotlib_canvas.MatplotlibCanvas(self.rightPanel, wx.ID_ANY)
        self.rightSizer.Add(self.matplotlib_canvas, 1, wx.ALL | wx.EXPAND, 3)
        self.rightSizer.Add(self.matplotlib_canvas.toolbar, 0, wx.EXPAND, 0)
        

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