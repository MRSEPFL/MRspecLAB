#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# a class to make matplotib.backend_wxagg.FigureCanvasWxAgg compatible to wxGlade

import wx

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2Wx

class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent, id=wx.ID_ANY):
        # 1x1 grid, first subplot
        figure = self.figure = Figure()
        #self.axes = figure.add_subplot(111)
        FigureCanvas.__init__(self, parent, id, figure)
        self.toolbar = NavigationToolbar2Wx(self)
        self.toolbar.Realize()

    def clear(self):
        self.figure.axes.clear()
        self.figure.clear()
        self.draw()
