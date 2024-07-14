import os, sys, wx
from interface.file_panel import FilePanel

class MainApp(wx.App):
    def OnInit(self):
        self.frame = wx.Frame(None, title="MRS Viewer")
        self.panel = FilePanel(self.frame)
        self.panel.is_viewer = True
        self.panel.label.Hide()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panel, 1, wx.EXPAND, 0)
        self.frame.SetSizer(self.sizer)
        self.frame.Layout()
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True
    
if __name__ == "__main__":
    app = MainApp(0)
    app.MainLoop()