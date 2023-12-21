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
##Changed the imports to adapt them to MrSoftware repository

import gswidgetkit.foldpanelbar as fpb
from gswidgetkit.buttons import Button
from gswidgetkit.label import  Label
from gswidgetkit.buttons import EVT_BUTTON

from GimelStudio.constants import (PROP_BG_COLOR, AREA_BG_COLOR, 
                                   AREA_TOPBAR_COLOR, TEXT_COLOR)
from GimelStudio.icons import (ICON_HELP, ICON_NODEPROPERTIES_PANEL,
                                   ICON_MORE_MENU_SMALL) #changed for MRSoftware
#from gimelstudio.core.node.property import ThumbProp
from GimelStudio.core.node.property import VectorProp
from .message_dlgs import ShowNotImplementedDialog
from .panel_base import PanelBase


class NodeInfoPanel(wx.Panel):
    def __init__(self, parent, *args, **kwds):
        wx.Panel.__init__(self, parent, *args, **kwds)
        #Added for MRSoftware
        self.parent=parent
        self.SetBackgroundColour(AREA_BG_COLOR)

        nodeinfo_pnl_sizer = wx.GridBagSizer(vgap=1, hgap=1)

        self.node_label = Label(self, label="")
        self.help_button = Button(self, label="", flat=True, bmp=(ICON_HELP.GetBitmap(), 'left'))

        nodeinfo_pnl_sizer.Add(self.node_label, (0, 1),
                                flag=wx.TOP | wx.BOTTOM, border=10)
        nodeinfo_pnl_sizer.Add(self.help_button, (0, 4),
                                flag=wx.TOP | wx.BOTTOM | wx.RIGHT, border=10)
        nodeinfo_pnl_sizer.AddGrowableCol(2)
        self.SetSizer(nodeinfo_pnl_sizer)

        self.help_button.Bind(EVT_BUTTON, self.OnHelpButton)

    #Adapted for MRSoftware
    def OnHelpButton(self, event):
        print(type(self.parent.Parent))
        if self.parent.Parent.selected_node is not None:
            properties_description=""
            for key in self.parent.Parent.selected_node.processing_step.parameters:
                if key in self.parent.Parent.selected_node.properties:
                    properties_description=  insert_newlines(key +": "+self.parent.Parent.selected_node.properties[key].description,90) +"\n"
                    
                
            dlg = wx.MessageDialog(None,
                            "Description :" +  "\n"+self.parent.Parent.selected_node.NodeMeta["description"] +"\n \n"+"Parameters: \n"+properties_description,
                            _(self.parent.Parent.selected_node.NodeMeta["label"] + " by " + self.parent.Parent.selected_node.NodeMeta["author"]), style=wx.ICON_INFORMATION)
            dlg.ShowModal()  


           
                
#added for MRSoftware         
def insert_newlines(input_string, interval):
    result = ""
    for i in range(0, len(input_string), interval):
        result += input_string[i:i+interval] + '\n'
    return result


class NodePropertiesPanel(PanelBase):
    def __init__(self, parent, idname, menu_item, *args, **kwargs):
        PanelBase.__init__(self, parent, idname, menu_item)

        self.thumb_pnl_expanded = False

        self.caption_style = fpb.CaptionBarStyle()
        self.caption_style.SetCaptionColour(wx.Colour(TEXT_COLOR))
        self.caption_style.SetFirstColour(wx.Colour(PROP_BG_COLOR))
        self.caption_style.SetCaptionStyle(fpb.CAPTIONBAR_SINGLE)
        
        ##Added for MRSoftware to control the help button and reset parameter
        self.selected_node=None

        self.BuildUI()
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

    def BuildUI(self):
        primary_sizer = wx.BoxSizer(wx.VERTICAL)

        # Topbar
        topbar = wx.Panel(self)
        topbar.SetBackgroundColour(AREA_TOPBAR_COLOR)


        #Removed following lines for MRS Software:
        # self.area_icon = wx.StaticBitmap(topbar,
        #                                  bitmap=ICON_NODEPROPERTIES_PANEL.GetBitmap())
        # self.area_label = Label(topbar, label="", color="#ccc", font_bold=False)

        # self.menu_button = Button(topbar, label="", flat=True,
        #                           bmp=(ICON_MORE_MENU_SMALL.GetBitmap(), 'left'))

        # topbar_sizer.Add(self.area_icon, (0, 0), flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=8)
        # topbar_sizer.Add(self.area_label, (0, 1), flag=wx.ALL, border=8)
        # topbar_sizer.Add(self.menu_button, (0, 4), flag=wx.ALL, border=3)
        # topbar_sizer.AddGrowableCol(2)
        
        #Added button for MRSoftware
        topbar_sizer = wx.BoxSizer(wx.VERTICAL)

        
        bmp_reset= wx.Bitmap("resources/reset_parameters_btn.png", wx.BITMAP_TYPE_PNG) 
        
        # self.resetParameters_button = custom_wxwidgets.BtmButtonNoBorder(topbar, wx.ID_ANY, bmp_reset)
        # self.resetParameters_button.SetBackgroundColour(wx.Colour(AREA_TOPBAR_COLOR)) 
        
        self.resetParameters_button = Button(topbar, label="", flat=True,
                                  bmp=(bmp_reset, 'left'))

        
        topbar_sizer.Add(self.resetParameters_button, 0, wx.ALL | wx.EXPAND, 5)

        topbar.SetSizer(topbar_sizer)

        # Main panel
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_panel.SetSizer(main_sizer)

        # Node info
        self.nodeinfo_pnl = NodeInfoPanel(main_panel)

        # Panel where the Properties will be placed
        self.props_panel = wx.Panel(main_panel)
        self.props_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.props_panel.SetSizer(self.props_panel_sizer)

        main_sizer.Add(self.nodeinfo_pnl, flag=wx.EXPAND | wx.BOTH)
        main_sizer.Add(self.props_panel, 1, flag=wx.EXPAND | wx.BOTH)

        primary_sizer.Add(topbar, flag=wx.EXPAND | wx.LEFT | wx.RIGHT)
        primary_sizer.Add(main_panel, 1, flag=wx.EXPAND | wx.BOTH)

        self.SetSizer(primary_sizer)

        self.resetParameters_button.Bind(EVT_BUTTON, self.reset_parameter)

    def UpdatePanelContents(self, selected_node):
        if selected_node is None or not hasattr(selected_node, "NodePanelUI"):
            return
        # Destroy the current panels and freeze to prevent glitching
        self.props_panel.DestroyChildren()
        self.Freeze()

        if selected_node is not None and hasattr(selected_node, "NodePanelUI"):
            self.nodeinfo_pnl.node_label.SetLabel(selected_node.GetLabel())

            # Node Properties
            panel_bar = fpb.FoldPanelBar(self.props_panel, agwStyle=fpb.FPB_VERTICAL)

            selected_node.NodePanelUI(self.props_panel, panel_bar)
            self.CreateThumbPanel(selected_node, self.props_panel, panel_bar)
            panel_bar.ApplyCaptionStyleAll(self.caption_style)

            self.props_panel_sizer.Add(panel_bar, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, border=6)
            self.props_panel_sizer.Fit(self.props_panel)
            self.selected_node=selected_node#Added for MRSoftware
        else:
            # Delete the window if the node is not selected
            self.props_panel_sizer.Clear(delete_windows=True)
            self.selected_node=None#Added for MRSoftware

        # Update everything then allow refreshing
        self.Layout()
        self.Refresh()
        self.Thaw()

    def CreateThumbPanel(self, node, panel, panel_bar):
        pass
        # Create the default Thumbnail panel
        # prop = ThumbProp(idname="Thumbnail", default=None, fpb_label="Node Thumbnail",
        #                  thumb_img=node.thumbnail)
        # prop.CreateUI(panel, panel_bar)
        
    def reset_parameter(self,event):
        if self.selected_node is not None:

            self.selected_node.processing_step.resetParameters()
            for key in self.selected_node.processing_step.parameters:

        
                if key in self.selected_node.properties:
                    if isinstance(self.selected_node.properties[key], VectorProp):
                        self.selected_node.properties[key].value=(self.selected_node.processing_step.parameters[key][0],self.selected_node.processing_step.parameters[key][1],0)
                    else:
                        self.selected_node.properties[key].value=self.selected_node.processing_step.parameters[key]

            self.UpdatePanelContents(self.selected_node)
            # Update everything then allow refreshing


            
            
        # def EditParametersProcessing(self):
        # for key, value in self.properties.items():
        #     if key == "freqRange":
        #        self.processing_step.parameters[key] = self.properties[key].value[:-1]
        #     elif key in self.processing_step.parameters:
        #         self.processing_step.parameters[key] = self.properties[key].value

            
        