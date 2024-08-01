import os, wx
from interface import images
from interface.colours import XISLAND1

class FittingFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(FittingFrame, self).__init__(*args, **kw)
        self.SetTitle("Fitting Options")
        self.SetIcon(images.icon_img_32.GetIcon())
        self.last_directory = wx.EmptyString

        self.SetBackgroundColour(wx.Colour(XISLAND1))
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.FlexGridSizer(5, 2, 0, 0)
        self.sizer.AddGrowableCol(1)
        self.SetSizerAndFit(self.main_sizer)

        self.basis_file_ctrl = wx.FilePickerCtrl(self, wx.ID_ANY, self.last_directory, "Select a file", "*.basis", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE)
        self.control_file_ctrl = wx.FilePickerCtrl(self, wx.ID_ANY, self.last_directory, "Select a file", "*.control", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE)
        self.wm_file_ctrl = wx.FilePickerCtrl(self, wx.ID_ANY, self.last_directory, "Select a file", "*.nii; *nii.gz", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE)
        self.gm_file_ctrl = wx.FilePickerCtrl(self, wx.ID_ANY, self.last_directory, "Select a file", "*.nii; *nii.gz", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE)
        self.csf_file_ctrl = wx.FilePickerCtrl(self, wx.ID_ANY, self.last_directory, "Select a file", "*.nii; *nii.gz", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE)

        self.clear_button = wx.Button(self, wx.ID_ANY, "Clear")
        self.clear_button.SetToolTip("Clear all fields")

        if self.Parent.basis_file_user is not None:
            self.basis_file_ctrl.SetPath(self.Parent.basis_file_user)
        if self.Parent.control_file_user is not None:
            self.control_file_ctrl.SetPath(self.Parent.control_file_user)
        if self.Parent.wm_file_user is not None:
            self.wm_file_ctrl.SetPath(self.Parent.wm_file_user)
        if self.Parent.gm_file_user is not None:
            self.gm_file_ctrl.SetPath(self.Parent.gm_file_user)
        if self.Parent.csf_file_user is not None:
            self.csf_file_ctrl.SetPath(self.Parent.csf_file_user)

        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, "Basis file"), 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(self.basis_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, "Control file"), 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(self.control_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, "WM segmentation file"), 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(self.wm_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, "GM segmentation file"), 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(self.gm_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, "CSF segmentation file"), 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(self.csf_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        self.main_sizer.Add(self.sizer, 1, wx.EXPAND, 5)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.clear_button, 0, wx.ALL | wx.EXPAND, 5)

        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_basis_file_changed, self.basis_file_ctrl)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_control_file_changed, self.control_file_ctrl)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_wm_file_changed, self.wm_file_ctrl)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_gm_file_changed, self.gm_file_ctrl)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_csf_file_changed, self.csf_file_ctrl)
        self.Bind(wx.EVT_BUTTON, self.on_clear, self.clear_button)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.SetMinSize((400, 250))
        self.SetMaxSize((-1, 250))
        self.Layout()
    
    def on_basis_file_changed(self, event):
        self.Parent.basis_file_user = self.basis_file_ctrl.GetPath()
        self.last_directory = os.path.dirname(self.basis_file_ctrl.GetPath())
        event.Skip()
    
    def on_control_file_changed(self, event):
        self.Parent.control_file_user = self.control_file_ctrl.GetPath()
        self.last_directory = os.path.dirname(self.control_file_ctrl.GetPath())
        event.Skip()
    
    def on_wm_file_changed(self, event):
        self.Parent.wm_file_user = self.wm_file_ctrl.GetPath()
        self.last_directory = os.path.dirname(self.wm_file_ctrl.GetPath())
        event.Skip()
    
    def on_gm_file_changed(self, event):
        self.Parent.gm_file_user = self.gm_file_ctrl.GetPath()
        self.last_directory = os.path.dirname(self.gm_file_ctrl.GetPath())
        event.Skip()

    def on_csf_file_changed(self, event):
        self.Parent.csf_file_user = self.csf_file_ctrl.GetPath()
        self.last_directory = os.path.dirname(self.csf_file_ctrl.GetPath())
        event.Skip()
    
    def on_clear(self, event):
        self.basis_file_ctrl.SetPath("")
        self.control_file_ctrl.SetPath("")
        self.wm_file_ctrl.SetPath("")
        self.gm_file_ctrl.SetPath("")
        self.csf_file_ctrl.SetPath("")
        self.Parent.basis_file_user = None
        self.Parent.control_file_user = None
        self.Parent.wm_file_user = None
        self.Parent.gm_file_user = None
        self.Parent.csf_file_user = None
        event.Skip()

    def on_close(self, event):
        self.Hide()