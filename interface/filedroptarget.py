import wx
import os

class FileDrop(wx.FileDropTarget):
    def __init__(self, parent, listbox: wx.ListBox, label):
        wx.FileDropTarget.__init__(self)
        self.parent = parent
        self.list = listbox
        self.label = label
        self.filepaths = []
        self.root = ""
        self.list.Bind(wx.EVT_LISTBOX, self.on_click)
        self.list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_dclick)

    def OnDropFiles(self, x, y, filenames):
        if len(filenames) == 0:
            if len(self.filepaths) == 0:
                self.on_clear(wx.CommandEvent())
            return False
        self.filepaths.extend(filenames)
        self.list.Set([])
        if len(self.filepaths) > 1: # find common root folder
            root = ""
            if all([f[0] == self.filepaths[0][0] for f in self.filepaths]):
                root = os.path.commonpath(self.filepaths)
            if root != "": self.list.Append([f.replace(root, "") for f in self.filepaths])
            else: self.list.Append([f for f in self.filepaths])
        else: self.list.Append([f for f in self.filepaths])
        _sorted = sorted(enumerate(self.filepaths), key=lambda x: x[1])
        self.filepaths = [f[1] for f in _sorted]
        order = [f[0] for f in _sorted]
        temp = self.list.GetStrings()
        self.list.Set([temp[i] for i in order])  # sort filepaths and list in the same order
        self.label.SetLabel(str(len(self.filepaths)) +" files") # + (("\n" + "Root folder: " + self.root) if len(self.root) > 0 else ""))
        self.label.Parent.Layout()
        self.clear_button.Enable()
        self.minus_button.Enable()
        return True
    
    def on_clear(self, event):
        self.filepaths = []
        self.list.Set([])
        self.clear_button.Disable()
        self.minus_button.Disable()
        self.label.SetLabel("0 files")
        self.label.Parent.Layout()
        self.parent.log_info("Filepaths cleared")
        event.Skip()
        
    def on_plus(self, event):
        wildcard = "MRS files ("
        for ext in self.parent.supported_files: wildcard += f"*.{ext}, "
        wildcard = wildcard[:-2] + ")|"
        for ext in self.parent.supported_files: wildcard += f"*.{ext};"
        wildcard = wildcard[:-1]
        if hasattr(self.parent, "last_directory") and os.path.exists(self.parent.last_directory):
            defaultDir = self.parent.last_directory
        else: defaultDir = self.parent.rootPath
        fileDialog = wx.FileDialog(self.parent, "Choose a file", wildcard=wildcard, defaultDir=defaultDir, style=wx.FD_OPEN | wx.FD_MULTIPLE)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepaths = fileDialog.GetPaths()
        self.parent.last_directory = fileDialog.GetDirectory()
        files = []
        for filepath in filepaths:
            if filepath == "" or not os.path.exists(filepath):
                self.parent.log_warning(f"File not found:\n\t{filepath}")
            else: files.append(filepath)
        ext = filepaths[0].rsplit(os.path.sep, 1)[1].rsplit(".", 1)[1]
        if not all([f.endswith(ext) for f in filepaths]):
            self.parent.log_error("Inconsistent file types")
            return False
        if ext.lower().strip() not in self.parent.supported_files:
            self.parent.log_error("Invalid file type")
            return False
        self.OnDropFiles(None, None, files)
        event.Skip()

    def on_minus(self, event):
        deleted_item = self.list.GetSelection()
        if deleted_item != wx.NOT_FOUND:
            new_paths = self.filepaths
            new_paths.pop(deleted_item)
            self.filepaths = []
            self.list.Set([])
            self.OnDropFiles(0, 0, new_paths)
        event.Skip()

    def on_click(self, event):
        # self.list.Deselect(self.list.GetSelection())
        event.Skip()

    def on_dclick(self, event):
        filename = self.filepaths[self.list.GetSelection()]
        self.parent.read_file(event, filename, new_window=True)
        event.Skip()