### modified from GimelStudio
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
import wx.adv
import wx.stc
from interface.colours import(XISLAND2, ACCENT_COLOR, ADD_NODE_MENU_BG)

class NodesVListBox(wx.VListBox):
    def __init__(self, *args, **kw):
        self.parent = args[0]
        wx.VListBox.__init__(self, *args, **kw)
        self.SetBackgroundColour(ADD_NODE_MENU_BG)
        self.Bind(wx.EVT_MOTION, self.OnStartDrag)

    def GetItemText(self, item):
        return self.GetNodeObject(item).GetLabel()

    def GetNodeObject(self, node_type):
        return self.NodeRegistry[self.NodeRegistryMap[node_type]](None, None)

    @property
    def NodeRegistryMap(self):
        return self.parent._nodeRegistryMapping

    @property
    def NodeRegistry(self):
        return self.parent._nodeRegistry

    def OnStartDrag(self, event):
        """ Start of drag n drop event handler. """
        if event.Dragging():
            selection = self.NodeRegistryMap[self.GetSelection()]
            data = wx.TextDataObject()
            data.SetText(selection)
            dropSource = wx.DropSource(self)
            dropSource.SetData(data)
            result = dropSource.DoDragDrop()
            if result:
                self.SetSelection(-1)

    def OnDrawItem(self, dc, rect, n):
        """ Draws the item itself. """
        # Monkey-patch some padding for the left side
        rect[0] += 16

        color = wx.Colour("#000")##Changed MRS

        if self.GetSelection() == n: dc.SetFont(self.GetFont().Bold())
        else: dc.SetFont(self.GetFont())
        dc.SetTextForeground(color)
        dc.SetBrush(wx.Brush(color, wx.SOLID))
        dc.DrawLabel(text=self.GetItemText(n), rect=rect, alignment=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        # Monkey-patch some padding for the right side
        rect[2] -= 18

    def OnMeasureItem(self, n):
        """ Returns the height required to draw the n'th item. """
        height = 0
        for line in self.GetItemText(n).split('\n'):
            w, h = self.GetTextExtent(line)
            height += h
        return height + 20

    def OnDrawBackground(self, dc, rect, n):
        if self.GetSelection() == n: color = wx.Colour(ACCENT_COLOR)
        else: color = wx.Colour(XISLAND2) #change color add node menue
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(color, wx.SOLID))
        dc.DrawRoundedRectangle(rect, 4)

class AddNodeMenu(wx.PopupTransientWindow):
    def __init__(self, parent, node_registry, size,style=wx.BORDER_NONE | wx.PU_CONTAINS_CONTROLS):
        wx.PopupTransientWindow.__init__(self, parent, style)
        self.parent = parent
        self._size = size
        self._nodeRegistry = node_registry
        self._nodeRegistryMapping = {}
        self.SetBackgroundColour(XISLAND2)
        self.InitRegistryMapping()
        self.InitAddNodeMenuUI()

    def InitRegistryMapping(self):
        i = 0
        for item in self._nodeRegistry:
            if item != "corenode_outputcomposite":
                self._nodeRegistryMapping[i] = item
                i += 1

    def InitAddNodeMenuUI(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Nodes list box
        self.nodes_listbox = NodesVListBox(self, size=self._size, style=wx.BORDER_NONE)
        self.nodes_listbox.SetBackgroundColour(XISLAND2)
        self.nodes_listbox.SetItemCount(len(self._nodeRegistryMapping))
        main_sizer.Add(self.nodes_listbox, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(main_sizer)

        # Bindings
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnClickSelectItem, self.nodes_listbox)
        self.Bind(wx.EVT_LISTBOX, self.OnClickSelectItem, self.nodes_listbox)

    @property
    def NodeGraph(self):
        return self.parent

    def OnClickSelectItem(self, event):
        pass