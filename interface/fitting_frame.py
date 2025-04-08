import os, wx
from interface import images
from interface.colours import XISLAND1

class FittingFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(FittingFrame, self).__init__(*args, **kw)
        self.SetTitle("Fitting Options")
        #self.SetIcon(images.icon_img_32.GetIcon())

        self.last_directory = wx.EmptyString
        self.SetBackgroundColour(wx.Colour(XISLAND1))

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.FlexGridSizer(5, 2, 0, 0)
        self.sizer.AddGrowableCol(1)
        self.SetSizer(self.main_sizer)  # or SetSizerAndFit, but we'll call Fit manually

        # Create controls
        self.basis_file_ctrl = wx.FilePickerCtrl(self, message="Select a file", wildcard="*.basis")
        self.control_file_ctrl = wx.FilePickerCtrl(self, message="Select a file", wildcard="*.control")
        self.wm_file_ctrl = wx.FilePickerCtrl(self, message="Select a file", wildcard="*.nii;*.nii.gz")
        self.gm_file_ctrl = wx.FilePickerCtrl(self, message="Select a file", wildcard="*.nii;*.nii.gz")
        self.csf_file_ctrl = wx.FilePickerCtrl(self, message="Select a file", wildcard="*.nii;*.nii.gz")

        self.clear_button = wx.Button(self, label="Clear")
        self.apply_button = wx.Button(self, label="Apply")
        self.clear_button.SetToolTip("Clear all fields")
        self.apply_button.SetToolTip("Apply changes")

        # If parent has existing file paths, set them
        if self.Parent.basis_file_user:
            self.basis_file_ctrl.SetPath(self.Parent.basis_file_user)
        if self.Parent.control_file_user:
            self.control_file_ctrl.SetPath(self.Parent.control_file_user)
        if self.Parent.wm_file_user:
            self.wm_file_ctrl.SetPath(self.Parent.wm_file_user)
        if self.Parent.gm_file_user:
            self.gm_file_ctrl.SetPath(self.Parent.gm_file_user)
        if self.Parent.csf_file_user:
            self.csf_file_ctrl.SetPath(self.Parent.csf_file_user)

        # Add to sizer
        self.sizer.Add(wx.StaticText(self, label="Basis file"), 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(self.basis_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(wx.StaticText(self, label="Control file"), 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(self.control_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(wx.StaticText(self, label="WM segmentation file"), 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(self.wm_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(wx.StaticText(self, label="GM segmentation file"), 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(self.gm_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(wx.StaticText(self, label="CSF segmentation file"), 0, wx.ALL | wx.EXPAND, 5)
        self.sizer.Add(self.csf_file_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        self.main_sizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.clear_button, 0, wx.ALL, 5)
        button_sizer.Add(self.apply_button, 0, wx.ALL, 5)
        self.main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)

        #self.main_sizer.Add(self.clear_button, 0, wx.ALL | wx.EXPAND, 5)

        # Bind events
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_basis_file_changed, self.basis_file_ctrl)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_control_file_changed, self.control_file_ctrl)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_wm_file_changed, self.wm_file_ctrl)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_gm_file_changed, self.gm_file_ctrl)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_csf_file_changed, self.csf_file_ctrl)
        self.Bind(wx.EVT_BUTTON, self.on_clear, self.clear_button)
        self.Bind(wx.EVT_BUTTON, self.on_apply, self.apply_button)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Remove self.SetMaxSize((-1, 250)).  Instead, let's do:
        self.SetMinSize((400, 250))       # bigger min size
        # self.SetMaxSize((-1, 250))      # <--- remove or comment out

        # Fit everything to size
        self.main_sizer.Fit(self)
        self.main_sizer.SetSizeHints(self)
        self.CentreOnScreen()

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

    def on_apply(self, event):
        self.Hide()

    def on_close(self, event):
        self.Hide()
