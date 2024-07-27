### mod
# ----------------------------------------------------------------------------
# Gimel Studio Copyright 2019-2023 by the Gimel Studio project contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------

import wx
from wx.lib.embeddedimage import PyEmbeddedImage
from gswidgetkit import Label, Button, EVT_BUTTON
import gswidgetkit.foldpanelbar as fpb
from interface.colours import AREA_BG_COLOR, TEXT_COLOR, PROP_BG_COLOR

ICON_HELP = PyEmbeddedImage(
    b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAAAYJJ'
    b'REFUSIntldtZwkAQhX/8LAArYKcDSogVSAdiBaYDQgdQgXZArMB0AB1MqMBYAT7sRDbLLqDP'
    b'zFtmz54zO7fAzS7Y6BJAVR3wBMwCdwc0wIeItP8SUNUxsABKYA/URgwwNsEJsAKWItKleJIC'
    b'Rv4JPACliNQZ3ByogC/gMSVyIhCQj4AiF1mEb4BDSuQ+caeyyKc9OEhXYZgaWItIJyKdqhbA'
    b'Dp/OKiS7i6JxwCs+LWEkNcda7I1k0x8atgIWxpF9bqmqbeQrVPVg+e59c/MVEbZV1TL7Anxn'
    b'xAUdA98i8h74muCMyD8QTdVgUCTroF8iq8ebfe6iu+01AllT1SnHDnu5NGQpgY7TZ4fWF3qW'
    b'IXdEGYhr0ODXQs6qM+Tg09OEjligBlzYMYnzTerA7kyImmQgYJGt8f2cS1Vu+hf4ndReA86O'
    b'fgafXS1xivqpLOzCVlWfz5DPgW2OPPmCKLIKvzpahuvaWRAOWAKrP63rSMjhJ7zg2ML9D6e+'
    b'ZhZudtZ+AOGFtUl0bXYfAAAAAElFTkSuQmCC')

class NodeInfoPanel(wx.Panel):
    def __init__(self, parent, *args, **kwds):
        wx.Panel.__init__(self, parent, *args, **kwds)
        self.SetBackgroundColour(AREA_BG_COLOR)

        nodeinfo_pnl_sizer = wx.GridBagSizer(vgap=1, hgap=1)
        self.node_label = Label(self, label="")
        self.help_button = Button(self, label="", flat=True, bmp=(ICON_HELP.GetBitmap(), 'left'))
        nodeinfo_pnl_sizer.Add(self.node_label, (0, 1), flag=wx.TOP | wx.BOTTOM, border=10)
        nodeinfo_pnl_sizer.Add(self.help_button, (0, 4), flag=wx.TOP | wx.BOTTOM | wx.RIGHT, border=10)
        nodeinfo_pnl_sizer.AddGrowableCol(2)
        self.SetSizer(nodeinfo_pnl_sizer)
        self.help_button.Bind(EVT_BUTTON, self.OnHelpButton)

    #Adapted for MRSoftware
    def OnHelpButton(self, event):
        node = self.Parent.Parent.selected_node
        if node is None: return
        propertystr = ""
        for p in node.parameters:
            propertystr += str(type(p))[20:-6] + ": " + p.label + "\n"
        dlg = wx.MessageDialog(None, node.NodeMeta["description"] + "\n\nParameters: \n" + propertystr,
                               caption=node.GetLabel() + " by " + node.GetAuthor() + " v" + str(node.GetVersion()), style=wx.ICON_INFORMATION)
        dlg.ShowModal()

class NodePropertiesPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.thumb_pnl_expanded = False
        self.caption_style = fpb.CaptionBarStyle()
        self.caption_style.SetCaptionColour(wx.Colour(TEXT_COLOR))
        self.caption_style.SetFirstColour(wx.Colour(PROP_BG_COLOR))
        self.caption_style.SetCaptionStyle(fpb.CAPTIONBAR_SINGLE)
        self.selected_node = None

        self.reset_button = Button(self, label="RESET PARAMETERS", flat=True)
        self.reset_button.SetToolTip("Reset node parameters to their default values")

        node_panel = wx.Panel(self)
        self.info_panel = NodeInfoPanel(node_panel)
        self.props_panel = wx.Panel(node_panel)
        self.props_sizer = wx.BoxSizer(wx.VERTICAL)
        self.props_panel.SetSizer(self.props_sizer)
        
        node_sizer = wx.BoxSizer(wx.VERTICAL)
        node_panel.SetSizer(node_sizer)
        node_sizer.Add(self.info_panel, flag=wx.EXPAND | wx.BOTH)
        node_sizer.Add(self.props_panel, 1, flag=wx.EXPAND | wx.BOTH)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.reset_button, flag=wx.EXPAND | wx.LEFT | wx.RIGHT)
        main_sizer.Add(node_panel, 1, flag=wx.EXPAND | wx.BOTH)
        self.SetSizer(main_sizer)
        self.reset_button.Bind(EVT_BUTTON, self.reset_parameter)
        self.SetBackgroundColour(AREA_BG_COLOR)

    @property
    def Parent(self):
        return self.parent

    @property
    def AUIManager(self):
        return self.parent.mgr

    @property
    def Statusbar(self):
        return self.parent.statusbar

    def UpdatePanelContents(self, selected_node):
        if selected_node is None or not hasattr(selected_node, "NodePanelUI"):
            return
        self.props_panel.DestroyChildren()
        self.Freeze()
        if selected_node is not None and hasattr(selected_node, "NodePanelUI"):
            self.info_panel.node_label.SetLabel(selected_node.GetLabel())
            panel_bar = fpb.FoldPanelBar(self.props_panel, agwStyle=fpb.FPB_VERTICAL)
            selected_node.NodePanelUI(self.props_panel, panel_bar)
            panel_bar.ApplyCaptionStyleAll(self.caption_style)
            self.props_sizer.Add(panel_bar, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, border=6)
            self.props_sizer.Fit(self.props_panel)
            self.selected_node = selected_node
        else:
            self.props_sizer.Clear(delete_windows=True)
            self.selected_node = None
        self.Layout()
        self.Refresh()
        self.Thaw()
        
    def reset_parameter(self, event):
        if self.selected_node is None: return
        self.selected_node.resetParameters()
        self.UpdatePanelContents(self.selected_node)