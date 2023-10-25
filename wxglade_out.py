import wx
import matplotlib_canvas

class FileDrop(wx.FileDropTarget):

    def __init__(self, window, button):
        wx.FileDropTarget.__init__(self)
        self.window = window
        self.dropped_file_paths = []
        self.button = button
        self.button.Disable()

    def OnDropFiles(self, x, y, filenames):
        for name in filenames:
            self.dropped_file_paths.append(name)
            print(name)
        if len(self.dropped_file_paths) > 0:
            self.window.SetLabel("\n".join(self.dropped_file_paths))
            self.button.Enable()
        else: self.button.Disable()
        return True
    
    def clear(self, event):
        self.dropped_file_paths = []
        print("filepaths cleared")
        self.window.SetLabel("Drop Inputs Files Here")
        self.button.Disable()

class MyFrame(wx.Frame):

    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((1200, 800))
        self.SetTitle("MRSprocessing")

        self.splitter = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.splitter.SetMinimumPaneSize(100)


        self.leftPanel = wx.Panel(self.splitter, wx.ID_ANY)
        self.leftSizer = wx.BoxSizer(wx.VERTICAL)
        self.leftPanel.SetSizer(self.leftSizer)
        self.rightPanel = wx.Panel(self.splitter, wx.ID_ANY)
        self.rightSizer = wx.BoxSizer(wx.VERTICAL)
        self.rightPanel.SetSizer(self.rightSizer)
        self.splitter.SplitVertically(self.leftPanel, self.rightPanel)

        ### LEFT PANEL ###
        self.drag_n_drop_button = wx.Button(self.leftPanel, wx.ID_ANY, "Clear Inputs")
        self.leftSizer.Add(self.drag_n_drop_button, 0, wx.ALL | wx.EXPAND, 5)

        self.scrolled = wx.ScrolledWindow(self.leftPanel, wx.ID_ANY, style=wx.VSCROLL)
        self.label_drag_and_drop = wx.StaticText(self.scrolled, wx.ID_ANY, "Drop Inputs Files Here", style=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTRE_VERTICAL)
        self.label_drag_and_drop.CenterOnParent()
        self.scrolled_window_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scrolled.SetSizer(self.scrolled_window_sizer)
        self.scrolled_window_sizer.Add(self.label_drag_and_drop, 0, wx.ALL | wx.EXPAND, 5)

        self.leftSizer.Add(self.scrolled, 1, wx.ALL | wx.EXPAND, 5)

        ### RIGHT PANEL ###
        self.button_processing = wx.Button(self.rightPanel, wx.ID_ANY, "Start Processing")
        self.rightSizer.Add(self.button_processing, 0, wx.ALL | wx.EXPAND, 5)

        self.matplotlib_canvas = matplotlib_canvas.MatplotlibCanvas(self.rightPanel, wx.ID_ANY)
        self.rightSizer.Add(self.matplotlib_canvas, 1, wx.ALL | wx.EXPAND, 3)
        self.rightSizer.Add(self.matplotlib_canvas.toolbar, 0, wx.EXPAND, 0)
        

        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.on_button_processing, self.button_processing)
        self.dt = FileDrop(self.label_drag_and_drop, self.drag_n_drop_button)
        self.leftPanel.SetDropTarget(self.dt)
        self.Bind(wx.EVT_BUTTON, self.dt.clear, self.drag_n_drop_button)

    def on_button_processing(self, event): # wxGlade: MyFrame.<event_handler>
        print("Event handler 'on_button_processing' not implemented!")
        event.Skip()