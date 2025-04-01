import wx
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2Wx

class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent, id=wx.ID_ANY):
        figure = self.figure = Figure()
        FigureCanvas.__init__(self, parent, id, figure)
        self.toolbar = NavigationToolbar2Wx(self)
        self.toolbar.Realize()

    def clear(self):
        self.figure.axes.clear()
        self.figure.clear()
        self.draw()
