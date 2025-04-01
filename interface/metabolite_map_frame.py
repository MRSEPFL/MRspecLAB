import wx
import os
import re
import numpy as np
from interface import utils
from processing.get_mapping import get_metabolite_list, get_coord_map,get_conc_map


class MetaboliteMapParameterDialog(wx.Frame):
    """Popup window for adjusting parameters (Resizable & Adaptive, Two-Column Layout)."""

    def __init__(self, parent):
        screen_width, screen_height = wx.GetDisplaySize()  # Get screen size
        default_width = min(700, int(screen_width * 0.5))  # Adaptive width
        default_height = min(800, int(screen_height * 0.8))

        super().__init__(parent, title="Plotting Parameters",
                         size=(default_width, default_height),
                         style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER)

        self.max_slices = 1  
        self.max_d = 1
        self.metab_list = None

        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(5, 10)  # Grid layout for two columns

        # --- File Section ---
        sizer.Add(wx.StaticText(panel, label="Image Selection"), pos=(0, 0), span=(1, 4),
                  flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)
        
        sizer.Add(wx.StaticText(panel, label="Choose image file:"), pos=(1, 0), flag=wx.ALL, border=5)
        self.img_picker = wx.FilePickerCtrl(panel, message="Select an image file", wildcard="*.nii; *nii.gz")
        sizer.Add(self.img_picker, pos=(1, 1), span=(1, 3), flag=wx.EXPAND | wx.ALL, border=5)
        self.img_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_img_selected)  # Bind event to update slices

        sizer.Add(wx.StaticText(panel, label="Image orientation:"), pos=(2, 0), flag=wx.ALL, border=5)
        self.img_view_ctrl = wx.Choice(panel, choices=["Orientation 1", "Orientation 2", "Orientation 3"])
        self.img_view_ctrl.SetSelection(1)
        sizer.Add(self.img_view_ctrl, pos=(2, 1), flag=wx.EXPAND | wx.ALL, border=5)

        sizer.Add(wx.StaticText(panel, label="Rotation angle:"), pos=(2, 2), flag=wx.ALL, border=5)
        self.img_rot_ctrl = wx.SpinCtrl(panel, value="90", min=0, max=360)
        sizer.Add(self.img_rot_ctrl, pos=(2, 3), flag=wx.EXPAND | wx.ALL, border=5)

        # --- Slice Selection ---
        sizer.Add(wx.StaticText(panel, label="Slice Selection"), pos=(3, 0), span=(1, 4),
                  flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        sizer.Add(wx.StaticText(panel, label="Select slice:"), pos=(4, 0), flag=wx.ALL, border=5)
        self.slice_ctrl = wx.SpinCtrl(panel, value="1", min=1, max=self.max_slices)
        sizer.Add(self.slice_ctrl, pos=(4, 1), flag=wx.EXPAND | wx.ALL, border=5)

        # --- Clear Images Button (spanning across both columns) ---
        clear_button = wx.Button(panel, label="Clear Images")
        sizer.Add(clear_button, pos=(5, 0), span=(1, 4), flag=wx.EXPAND | wx.ALL, border=10)
        clear_button.Bind(wx.EVT_BUTTON, self.on_clear)

        # --- Folder Selection ---
        sizer.Add(wx.StaticText(panel, label="CSI Folder Selection"), pos=(6, 0), span=(1, 4),
                  flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        sizer.Add(wx.StaticText(panel, label="Choose a folder:"), pos=(7, 0), flag=wx.ALL, border=5)
        self.folder_picker = wx.DirPickerCtrl(panel, message="Select a folder")
        sizer.Add(self.folder_picker, pos=(7, 1), span=(1, 3), flag=wx.EXPAND | wx.ALL, border=5)
        self.folder_picker.Bind(wx.EVT_DIRPICKER_CHANGED, self.on_folder_selected)  # Bind event to update slices

        # --- Metabolite Selection ---
        sizer.Add(wx.StaticText(panel, label="Metabolite Selection"), pos=(8, 0), span=(1, 4),
                  flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        sizer.Add(wx.StaticText(panel, label="Select metabolite to plot:"), pos=(9, 0), flag=wx.ALL, border=5)
        self.choice_ctrl = wx.Choice(panel, choices=[])
        sizer.Add(self.choice_ctrl, pos=(9, 1), flag=wx.EXPAND | wx.ALL, border=5)

        sizer.Add(wx.StaticText(panel, label="Select reference metabolite:"), pos=(9, 2), flag=wx.ALL, border=5)
        self.ref_ctrl = wx.Choice(panel, choices=[])
        sizer.Add(self.ref_ctrl, pos=(9, 3), flag=wx.EXPAND | wx.ALL, border=5)
        self.ref_ctrl.Bind(wx.EVT_CHOICE, self.on_ref_select)

        self.use_ref = wx.CheckBox(panel, label="conc./reference metabolite")
        self.use_ref.Enable(False)
        sizer.Add(self.use_ref, pos=(10, 0), span=(1, 4), flag=wx.ALL, border=5)
        # self.use_ref.Bind(wx.EVT_CHECKBOX, self.on_use_ref_toggle)  # Bind event

        # --- Mapping Options ---
        sizer.Add(wx.StaticText(panel, label="Mapping Options"), pos=(11, 0), span=(1, 4),
                  flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        sizer.Add(wx.StaticText(panel, label="Choose the map orientation:"), pos=(12, 0), flag=wx.ALL, border=5)
        self.map_view_ctrl = wx.Choice(panel, choices=["Orientation 1", "Orientation 2", "Orientation 3"])
        self.map_view_ctrl.SetSelection(1)
        sizer.Add(self.map_view_ctrl, pos=(12, 1), flag=wx.EXPAND | wx.ALL, border=5)

        sizer.Add(wx.StaticText(panel, label="Select slice (CSI):"), pos=(12, 2), flag=wx.ALL, border=5)
        self.map_slice_ctrl = wx.SpinCtrl(panel, value="1", min=1, max=self.max_d)
        sizer.Add(self.map_slice_ctrl, pos=(12, 3), flag=wx.EXPAND | wx.ALL, border=5)

        sizer.Add(wx.StaticText(panel, label="CRLB threshold:"), pos=(13, 0), flag=wx.ALL, border=5)
        self.crlb_ctrl = wx.SpinCtrl(panel, value="20", min=0, max=999)
        sizer.Add(self.crlb_ctrl, pos=(13, 1), flag=wx.EXPAND | wx.ALL, border=5)

        sizer.Add(wx.StaticText(panel, label="Scaling factor:"), pos=(13, 2), flag=wx.ALL, border=5)
        self.scaling_ctrl = wx.TextCtrl(panel, value="1.0")
        sizer.Add(self.scaling_ctrl, pos=(13, 3), flag=wx.EXPAND | wx.ALL, border=5)

        # --- Colorbar Settings ---
        sizer.Add(wx.StaticText(panel, label="Colorbar Settings"), pos=(14, 0), span=(1, 4),
                  flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        sizer.Add(wx.StaticText(panel, label="Colorbar min:"), pos=(15, 0), flag=wx.ALL, border=5)
        self.vmin_ctrl = wx.TextCtrl(panel, value="0.1")
        sizer.Add(self.vmin_ctrl, pos=(15, 1), flag=wx.EXPAND | wx.ALL, border=5)

        sizer.Add(wx.StaticText(panel, label="Colorbar max:"), pos=(15, 2), flag=wx.ALL, border=5)
        self.vmax_ctrl = wx.TextCtrl(panel, value="0.35")
        sizer.Add(self.vmax_ctrl, pos=(15, 3), flag=wx.EXPAND | wx.ALL, border=5)

        # --- Apply Button (spanning across both columns) ---
        apply_button = wx.Button(panel, label="Apply")
        apply_button.Bind(wx.EVT_BUTTON, self.on_apply)
        sizer.Add(apply_button, pos=(16, 0), span=(1, 4), flag=wx.EXPAND | wx.ALL, border=10)

        # Allow columns to expand
        sizer.AddGrowableCol(1)
        sizer.AddGrowableCol(3)

        self.Bind(wx.EVT_CLOSE, self.on_close)
        panel.SetSizer(sizer)

        self.SetMinSize((400, 400))  # Prevent it from getting too small
        self.Show()  # Display the popup


# class MetaboliteMapParameterDialog(wx.Frame):
#     """Popup window for adjusting parameters (Resizable)."""
#     def __init__(self, parent):
#         super().__init__(parent, title="Plotting Parameters", size=(300, 1000), style=wx.DEFAULT_FRAME_STYLE)

#         # self.Parent = parent  # Store parent reference
#         self.max_slices = 1  # Default to 1 before loading the image
#         self.max_d = 1
#         self.metab_list = None

#         panel = wx.Panel(self)
#         sizer = wx.BoxSizer(wx.VERTICAL)

#         # --- File Picker ---
#         self.img_picker = wx.FilePickerCtrl(panel, message="Select an image file", wildcard="*.nii; *nii.gz")
#         self.img_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_img_selected)  # Bind event to update slices

#         self.img_view = ["Orientation 1", "Orientation 2", "Orientation 3"]
#         self.img_view_ctrl = wx.Choice(panel, choices=self.img_view)
#         self.img_view_ctrl.SetSelection(1)  # Default selection

#         self.img_rot_ctrl = wx.SpinCtrl(panel, value="90", min=0, max=360)

#         clear_button = wx.Button(panel, label="Clear images")
#         clear_button.Bind(wx.EVT_BUTTON, self.on_clear)

#         # --- Slice Index (Dynamically Updated) ---
#         self.slice_ctrl = wx.SpinCtrl(panel, value="1", min=1, max=self.max_slices)

#         # --- Folder Picker Control ---
#         self.folder_picker = wx.DirPickerCtrl(panel, message="Select a folder")
#         self.folder_picker.Bind(wx.EVT_DIRPICKER_CHANGED, self.on_folder_selected)  # Bind event to update slices

#         # --- Selection List ---
#         self.choices = []#["Metabolite 1", "Metabolite 2", "Metabolite 3"]
#         self.choice_ctrl = wx.Choice(panel, choices=self.choices)
#         # self.choice_ctrl.SetSelection(0)  # Default selection

#         self.ref = []
#         self.ref_ctrl = wx.Choice(panel, choices=self.ref)
#         self.ref_ctrl.Bind(wx.EVT_CHOICE, self.on_ref_select)

#         self.use_ref = wx.CheckBox(panel, label="conc./reference metabolite")
#         self.use_ref.Enable(False) # Start as disable
#         # self.use_ref.Bind(wx.EVT_CHECKBOX, self.on_use_ref_toggle)  # Bind event

#         self.map_view = ["Orientation 1", "Orientation 2", "Orientation 3"]
#         self.map_view_ctrl = wx.Choice(panel, choices=self.map_view)
#         self.map_view_ctrl.SetSelection(1)  # Default selection

#         self.map_slice_ctrl = wx.SpinCtrl(panel, value="1", min=1, max=self.max_d)

#         self.crlb_ctrl = wx.SpinCtrl(panel, value="20", min=0, max=999)

#         self.scaling_ctrl = wx.TextCtrl(panel, value="1.0")

#         # --- Parameter Inputs ---
#         self.vmin_ctrl = wx.TextCtrl(panel, value="0.1")
#         self.vmax_ctrl = wx.TextCtrl(panel, value="0.35")

#         apply_button = wx.Button(panel, label="Apply")
#         apply_button.Bind(wx.EVT_BUTTON, self.on_apply)

#         # --- Add Widgets to Layout ---
#         sizer.Add(wx.StaticText(panel, label="Choose image file (optional):"), 0, wx.ALL, 5)
#         sizer.Add(self.img_picker, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(wx.StaticText(panel, label="Choose image orientation:"), 0, wx.ALL, 5)
#         sizer.Add(self.img_view_ctrl, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(wx.StaticText(panel, label="Select slice:"), 0, wx.ALL, 5)
#         sizer.Add(self.slice_ctrl, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(wx.StaticText(panel, label="Rotation angle:"), 0, wx.ALL, 5)
#         sizer.Add(self.img_rot_ctrl, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(clear_button, 0, wx.EXPAND | wx.ALL, 5)
                
#         sizer.Add(wx.StaticText(panel, label="Choose a folder:"), 0, wx.ALL, 5)
#         sizer.Add(self.folder_picker, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(wx.StaticText(panel, label="Choose the dimension:"), 0, wx.ALL, 5)
#         sizer.Add(self.map_view_ctrl, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(wx.StaticText(panel, label="Select slice (CSI):"), 0, wx.ALL, 5)
#         sizer.Add(self.map_slice_ctrl, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(wx.StaticText(panel, label="Select metabolite to plot:"), 0, wx.ALL, 5)
#         sizer.Add(self.choice_ctrl, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(wx.StaticText(panel, label="Select reference metabolite:"), 0, wx.ALL, 5)
#         sizer.Add(self.ref_ctrl, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(self.use_ref, 0, wx.ALL, 10)

#         sizer.Add(wx.StaticText(panel, label="CRLB threshold:"), 0, wx.ALL, 5)
#         sizer.Add(self.crlb_ctrl, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(wx.StaticText(panel, label="scaling factor:"), 0, wx.ALL, 5)
#         sizer.Add(self.scaling_ctrl, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(wx.StaticText(panel, label="Colorbar min:"), 0, wx.ALL, 5)
#         sizer.Add(self.vmin_ctrl, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(wx.StaticText(panel, label="Colorbar max:"), 0, wx.ALL, 5)
#         sizer.Add(self.vmax_ctrl, 0, wx.EXPAND | wx.ALL, 5)

#         sizer.Add(apply_button, 0, wx.EXPAND | wx.ALL, 5)

#         self.Bind(wx.EVT_CLOSE, self.on_close)

#         panel.SetSizer(sizer)
#         self.SetMinSize((300, 1000))  # Prevent panel from becoming too small
#         self.Show()  # Display the popup

    def get_selected_image_size(self):
        """Returns the shape of the selected brain image if available."""
        if "selected_img" in self.Parent.brain_image and self.Parent.brain_image["selected_img"] is not None:
            return self.Parent.brain_image["selected_img"].shape  # Returns (height, width, depth)
        else:
            utils.log_error("Error: Selected image not found or not loaded.")
            return None  # Return None if the image isn't available

    def get_max_slices(self):
        """Get the number of available slices from background image."""
        if not hasattr(self, "img_picker"):  # Ensure img_picker exists before accessing it
            return 1  # Default slice count

        selected_img_path = self.img_picker.GetPath()
        img_view = self.img_view_ctrl.GetSelection()

        if selected_img_path:  # Only process if a file is selected
            self.Parent.brain_image["selected_img_path"] = selected_img_path
            self.Parent.brain_image["selected_img"] = self.Parent.load_brain_image()
            if self.Parent.brain_image["selected_img"] is not None:
                img_size = self.get_selected_image_size()
                return img_size[img_view]  # Number of slices
        return 1  # Default if no image is loaded

    def on_img_selected(self, event):
        """Update slice range when the user selects a new image file."""
        utils.log_info(f"image selected")
        self.max_slices = self.get_max_slices()
        self.slice_ctrl.SetRange(1, max(1, self.max_slices))  # Prevent min > max issue
    
    def on_ref_select(self, event):
        """Enable checkbox only if a valid reference is selected."""
        ref_selected = self.ref_ctrl.GetSelection()

        # print(ref_selected)
        
        # Enable checkbox if any reference (other than "Select Reference") is chosen
        if ref_selected > 0:
            self.use_ref.Enable(True)
        else:
            self.use_ref.Enable(False)

    def get_max_d(self):

        """Get the number of available slices from CSI coords in selected folder."""
        print(f"Start reading .coord")

        if not hasattr(self, "folder_picker"):  # Ensure img_picker exists before accessing it
            return 1  # Default slice count

        dir = self.folder_picker.GetPath()

        if dir:  # Only process if a file is selected

            pattern = re.compile(r"(\d+)_(\d+)_(\d+)\.coord$")  # Regex pattern for m_n_k.coord
        
            indices = []  # List to store (m, n, k) tuples
            
            for filename in os.listdir(dir):
                match = pattern.match(filename)  # Match the pattern
                if match:
                    m, n, k = map(int, match.groups())  # Extract and convert to integers
                    indices.append((m, n, k))

            if not indices:
                utils.log_error("No valid files found in the folder.")
                return None

            indices = np.array(indices)
            x, y, z = indices.max(axis=0) # Get matrix dimensions

            # print(f"coord file dimensions: {x,y,z}")

            map_view = self.map_view_ctrl.GetSelection()

            if map_view == 0:
                return x
            elif map_view == 1:
                return y
            elif map_view == 2:
                return z
            return 1

        return 1  # Default if no folder is loaded
    

    def get_metabolite_list_from_folder(self):

        folder_path = self.folder_picker.GetPath()
        pattern = re.compile(r"(\d+)_(\d+)_(\d+)\.coord$")  # Regex pattern for m_n_k.coord
        
        for filename in os.listdir(folder_path):
            match = pattern.match(filename)
            if match:
                break
        
        metab_list = get_metabolite_list(os.path.join(folder_path,filename))

        return metab_list

    def on_folder_selected(self, event):

        # print(f"folder selected")

        # for updating the maximal silce number
        self.max_d = self.get_max_d()
        self.map_slice_ctrl.SetRange(1, max(1, self.max_d))  # Prevent min > max issue

        # for updating the matabolite list
        self.metab_list = self.get_metabolite_list_from_folder()
        
        self.choice_ctrl.Set(self.metab_list)  # Update choice list
        # if self.choices:
        #     self.choice_ctrl.SetSelection(0)  # Select first by default

        ref_list = ["None"] + self.metab_list
        self.ref_ctrl.Set(ref_list)  # Update choice list

    def on_apply(self, event):
        """Handle Apply button click."""
        self.Parent.param = {
            "vmin": float(self.vmin_ctrl.GetValue()),
            "vmax": float(self.vmax_ctrl.GetValue()),
        }

        self.Parent.brain_image = {
            "selected_img_path": self.img_picker.GetPath(),
            "selected_img_view": self.img_view_ctrl.GetSelection(),
            "slice_index": self.slice_ctrl.GetValue(),
            "selected_img_rotation": self.img_rot_ctrl.GetValue(),
        }

        self.Parent.brain_image["selected_img"] = None
        if self.img_picker.GetPath():
            self.Parent.brain_image["selected_img"] = self.Parent.load_brain_image()

        # self.Parent.selected_metabolite = self.choice_ctrl.GetStringSelection()

        x, y, z = 0, 0, 0
        coord = None
        if self.folder_picker.GetPath():
            x, y, z, coord = get_coord_map(self.folder_picker.GetPath())

        use_ref = False
        if self.use_ref.IsChecked():
            if self.ref_ctrl.GetStringSelection():
                use_ref = True

        self.Parent.data_to_plot = {
            "dir": self.folder_picker.GetPath(),
            "metab_list": self.metab_list,
            "metab_to_plot": self.choice_ctrl.GetStringSelection(),
            "metab_ref": self.ref_ctrl.GetStringSelection(),
            "dim": self.map_view_ctrl.GetSelection(),
            "slice": int(self.map_slice_ctrl.GetValue()),
            "coord": coord,
            "sz": [x, y, z],
            "use_ref": use_ref,
            "crlb_threshold": int(self.crlb_ctrl.GetValue()),
            "scaling": float(self.scaling_ctrl.GetValue())
        }
        self.Parent.data_to_plot["conc_map_to_plot"] = get_conc_map(self.Parent.data_to_plot)

        # utils.log_debug("Updated parameters for metabolite maps:", self.Parent.param)  # Debugging
        self.Parent.update_map()
        event.Skip()

    def on_clear(self, event):

        self.img_picker.SetPath("")

        self.Parent.brain_image = {
            "selected_img_path": None,
            "selected_img": None,
            "selected_img_view": None,
            "slice_index": None,
            "selected_img_rotation": None,
        }

        self.Parent.update_map()
        event.Skip()

    def on_close(self, event):
        """Handle window close event."""
        self.Hide()