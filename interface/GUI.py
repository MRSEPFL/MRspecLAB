import wx
import os
import time
import glob
import inspect
import importlib.util
import zipfile
import shutil
import threading
import numpy as np
import suspect

from . import wxglade_out
from .plots import plot_ima, plot_coord
from readcoord import ReadlcmCoord
import processingPipeline

class MyFrame(wxglade_out.MyFrame):

    def __init__(self, *args, **kwds):
        wxglade_out.MyFrame.__init__(self, *args, **kwds)
        processing_files = glob.glob(os.path.join(os.path.dirname(__file__), os.pardir, "processing", "*.py"))
        self.processing_steps = {}
        for file in processing_files:
            module_name = os.path.basename(file)[:-3]
            if module_name != "__init__":
                spec = importlib.util.spec_from_file_location(module_name, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and obj.__module__ == module_name:
                        obj = getattr(module, name)
                        self.processing_steps[name] = obj
        
        # self.pipeline = ["ZeroPadding", "LineBroadening", "FreqPhaseAlignment", "RemoveBadAverages", "Average"]
        self.pipeline = [self.list_ctrl.GetItemText(i) for i in range(self.list_ctrl.GetItemCount())]

        self.CreateStatusBar(1)
        self.SetStatusText("Current pipeline: " + " → ".join(self.pipeline))
        self.processing = False
        self.next = False
        self.steps = []

    def on_read_ima(self, event):
        self.import_to_list("IMA files (*.ima)|*.ima|DICOM files (*.dcm)|*.dcm")
        event.Skip()

    def on_read_coord(self, event):
        self.import_to_list("coord files (*.coord)|*.coord")
        event.Skip()
    
    def import_to_list(self, wildcard):
        fileDialog = wx.FileDialog(self, "Choose a file", wildcard=wildcard, defaultDir=os.path.dirname(os.path.dirname(__file__)), style=wx.FD_OPEN | wx.FD_MULTIPLE)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepaths = fileDialog.GetPaths()
        files = []
        for filepath in filepaths:
            if filepath == "" or not os.path.exists(filepath):
                print(f"File not found:\n\t{filepath}")
            else: files.append(filepath)
        self.dt.OnDropFiles(None, None, files)
        
    def OnDeleteClick(self, event):
        selected_item = self.list_ctrl.GetFirstSelected()
        if selected_item >= 0:
            self.list_ctrl.DeleteItem(selected_item)
            
    def OnPlotClick(self, event):
        if not self.steps:
            self.consoltext.AppendText("Need to process the data before plotting the results\n")

        else:
            selected_item_index = self.list_ctrl.GetFirstSelected()
            if not self.steps[selected_item_index].outputData:
                self.consoltext.AppendText("The step has not been performed yet\n")
                
            else:
                self.matplotlib_canvas.clear()
                self.steps[selected_item_index].plot(self.matplotlib_canvas)
                
                # while not self.next: time.sleep(0.1)
                # self.next = False


        print("not implemented")
    

        
    def OnRightClickList(self, event):
        pos = event.GetPosition()
        pos = self.list_ctrl.ScreenToClient(pos)
        item, flags = self.list_ctrl.HitTest(pos)
        
        if item != -1:
            self.list_ctrl.Select(item)  # Select the item that was right-clicked
            self.PopupMenu(self.context_menu_pipeline)
            
    def OnAddStep(self, event):
        # Get the label text to add it to the list
        label = event.GetEventObject()
        new_item_text = label.GetLabel()
        selected_item_index = self.list_ctrl.GetFirstSelected()
        if selected_item_index >= 0:
            self.list_ctrl.InsertItem(selected_item_index+1, new_item_text)
            
        

    def on_button_processing(self, event):
        if not self.processing:
    
            self.pipeline = [self.list_ctrl.GetItemText(i) for i in range(self.list_ctrl.GetItemCount())]
            self.steps = [] # instantiate the processing steps to keep their parameters, processedData etc.
            for step in self.pipeline:
                if step not in self.processing_steps.keys():
                    print(f"Processing step {step} not found")
                    continue
                self.steps.append(self.processing_steps[step]())
            self.processing = True
            self.next = False
            self.button_processing.SetLabel("Next")
            thread = threading.Thread(target=self.processPipeline, args=())
            thread.start()
        else:
            self.next = True
        event.Skip()

    def read_file(self, event, filepath=None): # file double-clicked in list
        if filepath is None:
            index = self.drag_and_drop_list.GetSelection()
            if index == wx.NOT_FOUND:
                return
            filepath = self.dt.dropped_file_paths[index]
        if filepath == "" or not os.path.exists(filepath):
            print("File not found")
            return
        if filepath.lower().endswith(".ima"):
            f = suspect.io.load_siemens_dicom(filepath)
            plot_ima(f, self.matplotlib_canvas, title=filepath)
            self.infotext.SetValue("")
            self.infotext.WriteText(f"File: {filepath}\n\tNumber of points: {f.np}\n\tScanner frequency (MHz): {f.f0}\n\tDwell time (s): {f.dt}\n\tFrequency delta (Hz): {f.df}\n"
                                + f"\tSpectral Width (Hz): {f.sw}\n\tEcho time (ms): {f.te}\n\tRepetition time (ms): {f.tr}\n"
                                + f"\tPPM range: {[f.hertz_to_ppm(-f.sw / 2.0), f.hertz_to_ppm(f.sw / 2.0)]}\n\tCentre: {f.centre}\n"
                                + "\tMetadata: " + "\n\t\t".join([f"{k}: {v}" for k, v in f.metadata.items()]))
        elif filepath.lower().endswith(".coord"):
            f = ReadlcmCoord(filepath)
            plot_coord(f, self.matplotlib_canvas, title=filepath)
            dtab = '\n\t\t'
            self.infotext.SetValue("")
            self.infotext.WriteText(f"File: {filepath}\n\tNumber of points: {len(f['ppm'])}\n\tNumber of metabolites: {len(f['conc'])} ({f['nfit']} fitted)\n"
                                    + f"\t0th-order phase: {f['ph0']}\n\t1st-order phase: {f['ph1']}\n\tFWHM: {f['linewidth']}\n\tSNR: {f['SNR']}\n\tData shift: {f['datashift']}\n"
                                    + f"""\tMetabolites:\n\t\t{dtab.join([f"{c['name']}: {c['c']} (±{c['SD']}%, Cr: {c['c_cr']})" for c in f['conc']])}\n""")
        if event is not None: event.Skip()


    def processPipeline(self):
        return processingPipeline.processPipeline(self)

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True