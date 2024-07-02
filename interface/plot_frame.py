import wx
from .plot_canvas import MatplotlibCanvas
from utils.colours import XISLAND1

class PlotFrame(wx.Frame):
    def __init__(self, title):
        super().__init__(None)
        self.SetTitle(title)
        self.SetIcon(wx.Icon("resources/icon_32p.png"))
        self.SetBackgroundColour(wx.Colour(XISLAND1)) 
        self.SetSize((1200, 800))
        self.Show(True)

        self.splitter = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.panel = wx.Panel(self.splitter, wx.ID_ANY)
        self.canvas = MatplotlibCanvas(self.panel, wx.ID_ANY)
        self.text = wx.TextCtrl(self.splitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.text.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.NORMAL,wx.FONTWEIGHT_NORMAL, False))
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND, 0)
        self.sizer.Add(self.canvas.toolbar, 0, wx.EXPAND, 0)
        self.panel.SetSizer(self.sizer)
        
        self.splitter.SetMinimumPaneSize(200)
        self.splitter.SplitVertically(self.panel, self.text, -150)
        self.splitter.SetSashGravity(1.)

        self.Layout()