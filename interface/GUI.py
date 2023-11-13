import wx
import os
import glob
import inspect
import importlib.util
import threading
import suspect
import sys
import pickle
import io
import time

from . import wxglade_out
from .plots import plot_ima, plot_coord
from readcoord import ReadlcmCoord
import processingPipeline

class MyFrame(wxglade_out.MyFrame):

    def __init__(self, *args, **kwds):
        wxglade_out.MyFrame.__init__(self, *args, **kwds)

        self.rootPath = os.path.dirname(__file__)
        while not os.path.exists(os.path.join(self.rootPath, "lcmodel")): self.rootPath = os.path.dirname(self.rootPath)
        processing_files = glob.glob(os.path.join(self.rootPath, "processing", "*.py"))
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
        
        # self.pipeline = ["ZeroPadding", "LineBroadening", "FreqPhaseAlignment", "EddyCurrentCorrection", "RemoveBadAverages", "Average"]
        self.pipeline = [self.list_ctrl.GetItemText(i) for i in range(self.list_ctrl.GetItemCount())]
        self.steps = [self.processing_steps[step]() for step in self.pipeline]
        # self.processing_steps = dict of the definitions of all processing steps
        # self.pipeline = mirror of the content of self.list_ctrl; might replace by self.list_ctrl.GetStrings()
        # self.steps = instances of the processing steps in the pipeline; should be updated every time self.pipeline or self.list_ctrl is updated 
        self.supported_files = ["ima", "dcm", "dat", "coord"]
        self.CreateStatusBar(1)
        self.SetStatusText("Current pipeline: " + " → ".join(self.pipeline))
        self.processing = False
        self.fast_processing = False
        self.next = False
        self.show_editor = True
        sys.stdout = self.consoltext
        self.on_toggle_editor(None)

    def on_read_ima(self, event):
        self.import_to_list("IMA files (*.ima)|*.ima|DICOM files (*.dcm)|*.dcm")
        event.Skip()

    def on_read_twix(self, event):
        self.import_to_list("TWIX files (*.dat)|*.dat")
        event.Skip()

    def on_read_coord(self, event):
        self.import_to_list("coord files (*.coord)|*.coord")
        event.Skip()
    
    def on_save_pipeline(self, event):
        if self.steps == []:
            print("No pipeline to save")
            return
        fileDialog = wx.FileDialog(self, "Save pipeline as", wildcard="Pipeline files (*.pipe)|*.pipe", defaultDir=self.rootPath, style=wx.FD_SAVE)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepath = fileDialog.GetPath()
        if filepath == "":
            print(f"File not found")
            return
        tosave = [(step.__class__.__name__, step.parameters) for step in self.steps]
        with open(filepath, 'wb') as f:
            pickle.dump(tosave, f)
        event.Skip()

    def on_load_pipeline(self, event):
        fileDialog = wx.FileDialog(self, "Choose a file", wildcard="Pipeline files (*.pipe)|*.pipe", defaultDir=self.rootPath, style=wx.FD_OPEN)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepath = fileDialog.GetPath()
        if filepath == "" or not os.path.exists(filepath):
            print("File not found")
            return
        with open(filepath, 'rb') as f:
            toload = pickle.load(f)
        self.list_ctrl.DeleteAllItems()
        self.pipeline = []
        self.steps = []
        for data in toload:
            self.list_ctrl.Append([data[0]])
            self.pipeline = [data[0]]
            self.steps.append(self.processing_steps[data[0]]())
            self.steps[-1].parameters = data[1]
        self.SetStatusText("Current pipeline: " + " → ".join(step.__class__.__name__ for step in self.steps))
        event.Skip()

    def on_toggle_editor(self, event):
        self.show_editor = not self.show_editor
        if self.show_editor:
            self.pipelineplotSplitter.SplitVertically(self.pipelinePanel, self.rightPanel)
            self.leftSplitter.SplitHorizontally(self.notebook_1, self.leftPanel)
            self.toggle_editor.SetItemLabel("Hide Editor")
        else:
            self.pipelineplotSplitter.Unsplit(self.pipelineplotSplitter.GetWindow1())
            self.leftSplitter.Unsplit(self.leftSplitter.GetWindow1())
            self.toggle_editor.SetItemLabel("Show Editor")
        self.Layout()
        if event is not None: event.Skip()

    def import_to_list(self, wildcard):
        fileDialog = wx.FileDialog(self, "Choose a file", wildcard=wildcard, defaultDir=self.rootPath, style=wx.FD_OPEN | wx.FD_MULTIPLE)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepaths = fileDialog.GetPaths()
        files = []
        for filepath in filepaths:
            if filepath == "" or not os.path.exists(filepath):
                print(f"File not found:\n\t{filepath}")
            else: files.append(filepath)
        ext = filepaths[0].rsplit(os.path.sep, 1)[1].rsplit(".", 1)[1]
        if not all([f.endswith(ext) for f in filepaths]):
            print("Inconsistent file types")
            return False
        if ext.lower().strip() not in self.supported_files:
            print("Invalid file type")
            return False
        self.dt.OnDropFiles(None, None, files)
        
    def OnDeleteClick(self, event):
        selected_item = self.list_ctrl.GetFirstSelected()
        if selected_item >= 0:
            self.list_ctrl.DeleteItem(selected_item)
            self.pipeline.pop(selected_item)
            self.steps.pop(selected_item)
            
    def OnPlotClick(self, event):
        if not self.dataSteps or len(self.dataSteps) <= 1: # first entry is the original data
            self.consoltext.AppendText("Need to process the data before plotting the results\n")
            return
        selected_item_index = self.list_ctrl.GetFirstSelected()
        if len(self.dataSteps) < selected_item_index + 2: # for step 1 (index 0), we should have a length of 2 (original and result of step 1)
            self.consoltext.AppendText("The step has not been performed yet\n")
            return
        self.matplotlib_canvas.clear()
        plot_ima(self.dataSteps[selected_item_index + 1], self.matplotlib_canvas, title="Result of " + self.pipeline[selected_item_index])
        event.Skip()
    

        
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
            self.pipeline.insert(selected_item_index+1, new_item_text)
            self.steps.insert(selected_item_index+1, self.processing_steps[new_item_text]())
            
        

    def on_button_processing(self, event):
        if not self.processing:
            self.processing = True
            self.next = False
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
            plot_ima(f, self.matplotlib_canvas.figure, title=filepath)
            self.infotext.SetValue("")
            self.infotext.WriteText(f"File: {filepath}\n\tNumber of points: {f.np}\n\tScanner frequency (MHz): {f.f0}\n\tDwell time (s): {f.dt}\n\tFrequency delta (Hz): {f.df}\n"
                                + f"\tSpectral Width (Hz): {f.sw}\n\tEcho time (ms): {f.te}\n\tRepetition time (ms): {f.tr}\n"
                                + f"\tPPM range: {[f.hertz_to_ppm(-f.sw / 2.0), f.hertz_to_ppm(f.sw / 2.0)]}\n\tCentre: {f.centre}\n"
                                + "\tMetadata: " + "\n\t\t".join([f"{k}: {v}" for k, v in f.metadata.items()]))
        elif filepath.lower().endswith(".coord"):
            f = ReadlcmCoord(filepath)
            plot_coord(f, self.matplotlib_canvas.figure, title=filepath)
            dtab = '\n\t\t'
            self.infotext.SetValue("")
            self.infotext.WriteText(f"File: {filepath}\n\tNumber of points: {len(f['ppm'])}\n\tNumber of metabolites: {len(f['conc'])} ({f['nfit']} fitted)\n"
                                    + f"\t0th-order phase: {f['ph0']}\n\t1st-order phase: {f['ph1']}\n\tFWHM: {f['linewidth']}\n\tSNR: {f['SNR']}\n\tData shift: {f['datashift']}\n"
                                    + f"""\tMetabolites:\n\t\t{dtab.join([f"{c['name']}: {c['c']} (±{c['SD']}%, Cr: {c['c_cr']})" for c in f['conc']])}\n""")
        if event is not None: event.Skip()

    def waitforprocessingbutton(self, label):
        self.button_processing.Enable()
        self.button_processing.SetLabel(label)
        while not self.next: time.sleep(0.1)
        self.next = False

    def processPipeline(self):
        return processingPipeline.processPipeline(self)

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True