import wx
import os
import glob
import inspect
import importlib.util
import threading
import pickle
import shutil

# for plot button
# import tkinter as tk
# from tkinter import filedialog, messagebox, simpledialog
# import matplotlib.pyplot as plt
import numpy as np
# import pandas as pd

import nibabel as nib
from scipy.ndimage import rotate, zoom
# import cv2

from interface import utils
from interface.pipeline_frame import PipelineFrame
from interface.fitting_frame import FittingFrame
from interface.main_layout import LayoutFrame

from interface.metabolite_map_frame import MetaboliteMapParameterDialog
from processing.get_mapping import create_brain_mask

from interface.plot_helpers import plot_coord, get_coord_info#, plot_ext
from processing.processing_pipeline import processPipeline, autorun_pipeline_exe
from inout.read_coord import ReadlcmCoord

class MainFrame(LayoutFrame):

    def __init__(self, *args, **kwds):

        LayoutFrame.__init__(self, *args, **kwds)

        utils.init_logging(self.info_text)
        utils.set_debug(False)
        self.debug_button.SetValue(False)

        self.current_step = 0
        self.basis_file = None
        self.basis_file_user = None
        self.control_file_user = None
        self.wm_file_user = None
        self.gm_file_user = None
        self.csf_file_user = None

        # for loading images
        # self.img_file_user = None
        # self.background_image = self.load_brain_image() #self.load_background_image()
        # Plot parameters
        self.param = {
            "vmin": None,
            "vmax": None,
        }

        self.brain_image = {
            "selected_img_path": None,
            "selected_img": None,
            "selected_img_view": None,
            "slice_index": None,
            "selected_img_rotation": None,
        }


        self.data_to_plot = {
            "dir": None,
            "metab_list": None,
            "metab_to_plot": None,
            "metab_ref": None,
            "dim": None,
            "slice": None,
            "coord": None,
            "sz": None,
            "use_ref": None,
            "crlb_threshold": None,
            "scaling": None,
            "conc_map_to_plot": None,
        }

        self.external_nodes_library = os.path.join(os.getcwd(), "customer_nodes")
        try:
            if not os.path.exists(self.external_nodes_library): os.mkdir(self.external_nodes_library)
        except:
            self.on_open_external_nodes(wx.PyEvent())
        self.copy_customer_processing_scripts()
        
        self.outputpath_base = os.path.join(os.getcwd(), "output")
        try:
            if not os.path.exists(self.outputpath_base): os.mkdir(self.outputpath_base)
        except:
            self.on_change_output(wx.PyEvent())
        self.outputpath = self.outputpath_base
        self.load_lastfiles()

        self.retrieve_steps() # dictionary of processing steps definitions
        self.pipeline_frame = PipelineFrame(parent=self) # /!\ put this after retrieve_steps
        self.pipeline_frame.Hide()
        self.fitting_frame = FittingFrame(parent=self)
        self.fitting_frame.Hide()
        self.retrieve_pipeline()

        self.metabolite_map_frame = MetaboliteMapParameterDialog(parent=self) # /!\ put this after retrieve_steps
        self.metabolite_map_frame.Hide()

        self.load_brain_image()
        self.update_map()

        self.CreateStatusBar(1)
        self.update_statusbar()

        self.Bind(wx.EVT_CLOSE, self.on_close) # save last files on close
        self.Bind(wx.EVT_BUTTON, self.reset, self.button_terminate_processing)
        self.Bind(wx.EVT_BUTTON, self.on_autorun_processing, self.button_auto_processing)
        self.Bind(wx.EVT_BUTTON, self.on_open_output_folder, self.folder_button)
        self.Bind(wx.EVT_BUTTON, self.on_open_pipeline, self.pipeline_button)
        self.Bind(wx.EVT_BUTTON, self.on_open_external_nodes, self.extenal_nodes)
        self.Bind(wx.EVT_BUTTON, self.on_change_output, self.change_output_button)
        self.Bind(wx.EVT_BUTTON, self.on_open_fitting, self.fitting_button)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.on_show_debug, self.show_debug_button)
        self.Bind(wx.EVT_CHECKBOX, self.on_toggle_debug, self.debug_button)
        self.Bind(wx.EVT_BUTTON, self.on_reload, self.reload_button)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_BUTTON, self.on_button_step_processing, self.button_step_processing)
        self.Bind(wx.EVT_COMBOBOX, self.on_plot_box_selection)
        # self.Bind(wx.EVT_BUTTON, self.on_nplot, self.button_nplot)
        self.Bind(wx.EVT_BUTTON, self.on_open_metabolite_map_plot, self.button_nplot)

        self.on_show_debug(None)
        self.reset()

    def reset(self, event=None):
        self.processing = False
        self.fast_processing = False
        self.button_terminate_processing.Disable()
        self.button_step_processing.Enable()
        self.button_auto_processing.Enable()
        self.button_nplot.Enable()
        if self.current_step >= len(self.steps):
            self.button_step_processing.SetBitmap(self.run_bmp)
        self.button_auto_processing.SetBitmap(self.autorun_bmp)
        self.current_step = 0
        self.Layout()
        if event is not None: event.Skip()
    
    def copy_customer_processing_scripts(self):
        self.programpath = os.path.dirname(os.path.dirname(__file__))
        source_folders = self.external_nodes_library #os.path.join(self.programpath, "customer_nodes")
        backup_folder = os.path.join(self.programpath, "customer_nodes/backup")
        destination_folder = os.path.join(self.programpath, "nodes")
        try:
            # Ensure the destination folder exists; create it if it doesn't
            os.makedirs(destination_folder, exist_ok=True)

            # Loop through each source folder
            #for source_folder in source_folders:
            # Find all Python (.py) files in the current source folder
            python_files = glob.glob(os.path.join(source_folders, '*.py'))
                
            # Copy each file to the destination folder
            for file_path in python_files:
                file_name = os.path.basename(file_path)
                destination_path = os.path.join(destination_folder, file_name)

                # # Check if a file with the same name already exists
                # if os.path.exists(destination_path):
                #     base_name, extension = os.path.splitext(file_name)
                #     counter = 1

                #     # Find a unique filename by appending a counter
                #     while os.path.exists(destination_path):
                #         new_file_name = f"{base_name}_{counter}{extension}"
                #         destination_path = os.path.join(destination_folder, new_file_name)
                #         counter += 1

                # Check if a file with the same name already exists
                if os.path.exists(destination_path):
                    # Send a reminder
                    print(f"Reminder: The file '{file_name}' already exists in '{destination_folder}'.")
                    
                    # Prepare to back up the old file
                    os.makedirs(backup_folder, exist_ok=True)
                    backup_path = os.path.join(backup_folder, file_name)

                    # Create a unique backup filename if necessary
                    if os.path.exists(backup_path):
                        base_name, extension = os.path.splitext(file_name)
                        counter = 1
                        
                        # Find a unique backup filename by appending a counter
                        while os.path.exists(backup_path):
                            backup_path = os.path.join(backup_folder, f"{base_name}_{counter}{extension}")
                            counter += 1
                    
                    # Move the existing file to the backup folder
                    shutil.move(destination_path, backup_path)
                    print(f"Backup of the existing file has been created: '{backup_path}'")

                # Copy the new file to the destination folder
                shutil.copy(file_path, destination_path)
                print(f"'{file_path}' has been copied to '{destination_path}'.")

                # # Copy the file to the unique destination path
                # shutil.copy(file_path, destination_path)
                # print(f"Copied '{file_path}' to '{destination_path}'")

            print("All Customer Processing scripts have been copied successfully.")

        except FileNotFoundError:
            print(f"One of the source folders not found.")
        except PermissionError:
            print("Permission denied. Please check your folder permissions.")
        except Exception as e:
            print(f"An error occurred: {e}")

    
    def retrieve_steps(self):
        self.programpath = os.path.dirname(os.path.dirname(__file__))
        processing_files = glob.glob(os.path.join(self.programpath, "nodes", "*.py"))
        self.processing_steps = {}
        for file in processing_files:
            module_name = os.path.basename(file)[:-3]
            if module_name.startswith("_"): continue
            spec = importlib.util.spec_from_file_location(module_name, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and obj.__module__ == module_name:
                    obj = getattr(module, name)
                    self.processing_steps[name] = obj

    def update_statusbar(self):
        self.SetStatusText("Current pipeline: " + " → ".join(step.__class__.__name__ for step in self.steps))

    def on_button_step_processing(self, event):
        self.button_step_processing.Disable()
        self.button_auto_processing.Disable()
        if self.current_step > 0:
            self.button_terminate_processing.Disable()
        thread_processing = threading.Thread(target=processPipeline, args=[self])
        thread_processing.start()
        event.Skip()
        
    def on_autorun_processing(self, event):
        self.fast_processing = not self.fast_processing
        if not self.fast_processing:
            self.button_auto_processing.SetBitmap(self.autorun_bmp)
        else:
            self.button_auto_processing.SetBitmap(self.pause_bmp)
            self.button_step_processing.Disable()
            if 0 < self.current_step:
                self.button_terminate_processing.Disable()
            thread_processing = threading.Thread(target=autorun_pipeline_exe, args=[self])
            thread_processing.start()
        event.Skip()
    
    def load_brain_image(self):
        """Load a 3D NIfTI image and return the data."""
        # Check if self.img_file_user has a valid path
        if self.brain_image["selected_img_path"] is not None:
            # Use the stored path from self.img_file_user
            img = nib.load(self.brain_image["selected_img_path"])  # Load the image from the file path stored in self.img_file_user
            return img.get_fdata()  # Get the data from the NIfTI file
        else:
            utils.log_info(f"Image file is not set.")

    def on_open_output_folder(self, event):
        if os.path.exists(self.outputpath):
            os.startfile(self.outputpath)
        event.Skip()

    def on_open_pipeline(self, event):
        self.pipeline_frame.Show()
        event.Skip()
    
    def on_open_metabolite_map_plot(self,event):
        self.metabolite_map_frame.Show()
        event.Skip()
    
    def update_map(self):

        fig = self.matplotlib_canvas.figure
        fig.clf()  # Clear figure
        self.matplotlib_canvas.draw()  # Refresh the canvas
        utils.log_info("Start update main canvas")

        # if (self.brain_image["selected_img"] is None or self.brain_image["selected_img"].size == 0) and \
        if (self.brain_image["selected_img_path"] is None or self.brain_image["selected_img"] is None) and \
        (self.data_to_plot["coord"] is None):
            utils.log_info("Nothing to plot")
            return  # Nothing to plot

        ax = fig.add_subplot(111)

        # Handle background image
        if self.brain_image["selected_img_path"]: 
            if self.brain_image["selected_img"] is not None:
                if self.brain_image["selected_img"].size > 0:
                    views = {
                        0: self.brain_image["selected_img"][self.brain_image['slice_index'], :, :],
                        1: self.brain_image["selected_img"][:, self.brain_image['slice_index'], :],
                        2: self.brain_image["selected_img"][:, :, self.brain_image['slice_index']]
                    }
                    background_slice = views.get(self.brain_image["selected_img_view"])

                if background_slice is None:
                    utils.log_error("Selected image view is incorrect!")
                    return

                background_slice = rotate(
                    background_slice, self.brain_image["selected_img_rotation"], reshape=False, mode='nearest'
                )
                ax.imshow(background_slice, cmap='gray', interpolation='nearest')

        # Handle metabolite concentration map
        if self.data_to_plot["conc_map_to_plot"] is not None and self.data_to_plot["conc_map_to_plot"].size > 0:
            utils.log_info(f"Plot slice {self.data_to_plot['slice']} of {self.data_to_plot['metab_to_plot']}")
            conc_map = self.data_to_plot["conc_map_to_plot"]
            vmin, vmax = np.nanmin(np.abs(conc_map)), np.nanmax(np.abs(conc_map))
            concentration_masked = conc_map

            # If background exists, interpolate concentration map to match its size
            if self.brain_image["selected_img"] is not None and self.brain_image["selected_img"].size > 0:
                background_height, background_width = background_slice.shape
                concentration_masked = zoom(conc_map, (background_height / conc_map.shape[0], background_width / conc_map.shape[1]), order=1)
                mask = create_brain_mask(background_slice)  # Assuming mask function exists
                concentration_masked = np.where(mask == 1, concentration_masked, np.nan)

            cax = ax.imshow(concentration_masked, cmap='coolwarm', interpolation='nearest', alpha=1, vmin=self.param["vmin"], vmax=self.param["vmax"])
            fig.colorbar(cax, ax=ax, orientation='vertical', label='Concentration')
            ax.set_title(f"Slice {self.data_to_plot['slice']} (min={vmin:.2g}, max={vmax:.2g})")
            ax.axis('off')

        self.matplotlib_canvas.draw_idle()


    # def update_map(self):

    #     # Clear the existing canvas
    #     fig = self.matplotlib_canvas.figure
    #     fig.clf()  # Clear figure
    #     utils.log_info("Start plotting metabolite maps")

    #     # print(f"Applied: vmin={self.param['vmin']}, vmax={self.param['vmax']}, slice={self.param['slice_index']}")
        
    #     if self.brain_image["selected_img"] or self.data_to_plot["coord"]:

    #         ax = fig.add_subplot(111)  # Create a subplot for each slice

    #         if self.brain_image["selected_img"]:

    #             if self.brain_image["selected_img_view"] == 0:
    #                 background_slice = self.brain_image["selected_img"][self.brain_image['slice_index'], :, :]
    #             elif self.brain_image["selected_img_view"]  == 1:
    #                 background_slice = self.brain_image["selected_img"][:, self.brain_image['slice_index'], :]
    #             elif self.brain_image["selected_img_view"]  == 2:
    #                 background_slice = self.brain_image["selected_img"][:, :, self.brain_image['slice_index']]
    #             else:
    #                 utils.log_error(f"selected image view is wrong!")

    #             background_slice = rotate(background_slice, self.brain_image["selected_img_rotation"], reshape=False, mode='nearest')

    #             # Plot the background slice if available
    #             ax.imshow(background_slice, cmap='gray', interpolation='nearest')  # Background

    #             # ax.set_title(f"Slice {self.brain_image['slice_index']}")
        
    #         if not self.brain_image["selected_img"] and self.data_to_plot["coord"]:
    #             utils.log_info(f"Plot slice {self.data_to_plot['slice']} of {self.data_to_plot['metab_to_plot']}")
    #             # mydata = get_conc_map(self.data_to_plot)
    #             # Plot the concentration data with mask
    #             concentration_data = self.data_to_plot['conc_map_to_plot']
    #             # print(concentration_data)
    #             vmin, vmax = np.nanmin(np.abs(concentration_data)), np.nanmax(np.abs(concentration_data))
    #             # print(vmin,vmax)
    #             cax = ax.imshow(concentration_data, cmap='coolwarm', interpolation='nearest', alpha=1, vmin=self.param["vmin"], vmax=self.param["vmax"])
    #             fig.colorbar(cax, ax=ax, orientation='vertical', label='Concentration')   
    #             ax.axis('off')
    #             ax.set_title(f"Slice {self.data_to_plot['slice']}:(min={vmin:.2g},max={vmax:.2g})")
            
    #         if self.brain_image["selected_img"] and self.data_to_plot["coord"]:
                
    #             # if self.brain_image["selected_img_view"] == 0:
    #             #     background_slice = self.brain_image["selected_img"][self.brain_image['slice_index'], :, :]
    #             # elif self.brain_image["selected_img_view"]  == 1:
    #             #     background_slice = self.brain_image["selected_img"][:, self.brain_image['slice_index'], :]
    #             # elif self.brain_image["selected_img_view"]  == 2:
    #             #     background_slice = self.brain_image["selected_img"][:, :, self.brain_image['slice_index']]
    #             # else:
    #             #     utils.log_error(f"selected image view is wrong!")

    #             # background_slice = rotate(background_slice, self.brain_image["selected_img_rotation"], reshape=False, mode='nearest')
            
    #             # # Plot the background slice if available
    #             # ax.imshow(background_slice, cmap='gray', interpolation='nearest')  # Background

    #             # Get the dimensions of the background slice
    #             background_height, background_width = background_slice.shape

    #             # Interpolate the concentration data to match the background slice size
    #             conc_map = self.data_to_plot['conc_map_to_plot']
    #             concentration_interpolated = zoom(conc_map, (background_height / conc_map.shape[0], background_width / conc_map.shape[1]), order=1)
    #             concentration_masked = concentration_interpolated  # Assume we use the full concentration data without any mask

    #             # Create a mask for the background (you can define your own logic for masking)
    #             mask = create_brain_mask(background_slice)  # Assuming this function exists in your class
    #             concentration_masked = np.where(mask == 1, concentration_interpolated, np.nan)  # Mask the concentration data
                
    #             # Plot the concentration data with mask
    #             cax = ax.imshow(concentration_masked, cmap='coolwarm', interpolation='nearest', alpha=1, vmin=self.param["vmin"], vmax=self.param["vmax"])


    #         # Refresh canvas
    #         fig = self.matplotlib_canvas.draw_idle()

    def on_open_external_nodes(self, event):
        dirDialog = wx.DirDialog(self.Parent, "Select a folder for the customer nodes library", style=wx.DD_DIR_MUST_EXIST)
        if dirDialog.ShowModal() == wx.ID_CANCEL: return
        temp = os.path.join(dirDialog.GetPath())
        if not os.path.exists(temp):
            try: os.mkdir(temp)
            except:
                utils.log_error(f"Could not create folder {temp}")
                return
        self.external_nodes_library = temp
        self.copy_customer_processing_scripts()
        self.retrieve_steps()
        self.retrieve_pipeline()
        self.update_statusbar()

    def on_change_output(self, event):
        dirDialog = wx.DirDialog(self.Parent, "Choose a new output folder", style=wx.DD_DIR_MUST_EXIST)
        if dirDialog.ShowModal() == wx.ID_CANCEL: return
        temp = os.path.join(dirDialog.GetPath(), "output")
        if not os.path.exists(temp):
            try: os.mkdir(temp)
            except:
                utils.log_error(f"Could not create folder {temp}")
                return
        self.outputpath_base = temp

    def on_open_fitting(self, event):
        self.fitting_frame.Show()
        event.Skip()
    
    def on_show_debug(self, event):
        if self.show_debug_button.GetValue():
            self.debug_button.Show()
            self.reload_button.Show()
            self.show_debug_button.SetLabel("Hide debug options")
        else:
            self.debug_button.Hide()
            self.reload_button.Hide()
            self.show_debug_button.SetLabel("Show debug options")
        self.Layout()
        if event is not None: event.Skip()

    def on_toggle_debug(self, event):
        utils.set_debug(self.debug_button.GetValue())
        if event is not None: event.Skip()
    
    def on_reload(self, event):
        self.copy_customer_processing_scripts()
        self.retrieve_steps()
        self.retrieve_pipeline()
        self.update_statusbar()
        if event is not None: event.Skip()

    def on_plot_box_selection(self, event):
        selected_item = self.plot_box.GetValue()
        if selected_item == "":
            self.matplotlib_canvas.clear()
        elif selected_item == "lcmodel":
            if os.path.exists(self.last_coord):
                self.matplotlib_canvas.clear()
                f = ReadlcmCoord(self.last_coord)
                plot_coord(f, self.matplotlib_canvas.figure, title=self.last_coord)
                self.matplotlib_canvas.draw()
                self.file_text.SetValue(f"File: {self.last_coord}\n{get_coord_info(f)}")
            else:
                utils.log_warning("LCModel output not found")
        else:
            index = self.plot_box.GetSelection()
            for step in self.steps:
                if step.__class__.__name__ in selected_item:
                    dataDict = {
                        "input": self.dataSteps[index-1],
                        "wref": self.wrefSteps[index-1],
                        "output": self.dataSteps[index],
                        "wref_output": self.wrefSteps[index]
                    }
                    self.matplotlib_canvas.clear()
                    step.plot(self.matplotlib_canvas.figure, dataDict)
                    self.matplotlib_canvas.draw()
                    event.Skip()
                    return
            utils.log_warning("Step not found")

    def retrieve_pipeline(self):
        current_node = self.pipeline_frame.nodegraph.GetInputNode()
        self.pipeline = []
        self.steps = []
        while current_node is not None:
            for socket in current_node.GetSockets():
                if socket.direction == 1:
                    if len(socket.GetWires()) == 0:
                        current_node = None
                        continue
                    if len(socket.GetWires()) > 1:
                        utils.log_error("Only serial pipelines are allowed for now")
                        self.pipeline = []
                        self.steps = []
                        return
                    current_node = socket.GetWires()[0].dstsocket.node
                    self.pipeline.append(current_node.GetLabel())
                    self.steps.append(current_node)
    
    def save_lastfiles(self):
        # tosave = [self.MRSfiles.filepaths, self.Waterfiles.filepaths, self.basis_file_user, self.control_file_user, self.wm_file_user, self.gm_file_user, self.csf_file_user]
        tosave = [
            self.MRSfiles.filepaths, 
            self.Waterfiles.filepaths, 
            self.basis_file_user, 
            self.control_file_user, 
            self.wm_file_user, 
            self.gm_file_user, 
            self.csf_file_user, 
            self.img_file_user
            ]
        print(f"got {len(tosave)} values for filepaths")
        filepath = os.path.join(os.getcwd(), "lastfiles.pickle")
        with open(filepath, 'wb') as f:
            pickle.dump(tosave, f)

    def load_lastfiles(self):
        filepath = os.path.join(os.getcwd(), "lastfiles.pickle")
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                # filepaths, filepaths_wref, self.basis_file_user, self.control_file_user, self.wm_file_user, self.gm_file_user, self.csf_file_user = pickle.load(f)
                filepaths, filepaths_wref, self.basis_file_user, self.control_file_user, self.wm_file_user, self.gm_file_user, self.csf_file_user, self.img_file_user = pickle.load(f)
            # with open(filepath, 'rb') as f: # To solve error: ValueError: not enough values to unpack (expected 8, got 7)
            #     try:
            #         data = pickle.load(f)
            #         if len(data) == 8:
            #             filepaths, filepaths_wref, self.basis_file_user, self.control_file_user, self.wm_file_user, self.gm_file_user, self.csf_file_user, self.img_file_user = data
            #         else:
            #             print(f"Error: Expected 8 values, but got {len(data)} values. Using defaults.")
            #             filepaths, filepaths_wref, self.basis_file_user, self.control_file_user, self.wm_file_user, self.gm_file_user, self.csf_file_user = data #, self.img_file_user = [None]*8   Default values
            #     except (EOFError, ValueError) as e:
            #         print(f"Error loading pickle file: {e}. Using defaults.")
            #         filepaths, filepaths_wref, self.basis_file_user, self.control_file_user, self.wm_file_user, self.gm_file_user, self.csf_file_user, self.img_file_user = [None]*8  # Default values

            
            self.MRSfiles.on_drop_files(filepaths)
            self.Waterfiles.on_drop_files(filepaths_wref)

    def on_close(self, event):
        try: self.save_lastfiles()
        except: pass
        self.Destroy()
        
    def on_resize(self, event):
        self.Layout()
        self.Refresh()

class MainApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

if __name__ == "__main__":
    app = MainApp(0)
    app.MainLoop()