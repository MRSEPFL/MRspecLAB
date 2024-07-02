import wx
import os
import glob
import inspect
import importlib.util
import threading
import suspect
import pickle
from datetime import datetime

from .main_layout import LayoutFrame
from .plot_helpers import plot_mrs, plot_coord
from inout.readcoord import ReadlcmCoord
from processing import processingPipeline
from .plot_frame import PlotFrame
from . import pipeline_window
from utils.colours import(XISLAND1,XISLAND2,INFO_COLOR,ERROR_COLOR,WARNING_COLOR,DEBUG_COLOR)

myEVT_LOG = wx.NewEventType()
EVT_LOG = wx.PyEventBinder(myEVT_LOG, 1)
class LogEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id, text=None, colour=None):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.text = text
        self.colour = colour

    def GetText(self): return self.text
    def GetColour(self): return self.colour
    
class MainFrame(LayoutFrame):

    def __init__(self, *args, **kwds):
        LayoutFrame.__init__(self, *args, **kwds)

        self.processing_steps, self.rootPath = self.retrieve_steps() # dictionary of processing steps definitions
        self.pipelineWindow = pipeline_window.PipelineWindow(parent=self) # /!\ put this after retrieve_steps
        self.pipeline, self.steps = self.retrieve_pipeline() # list of processing step instances in pipeline, should be changed to strings only

        self.supported_files = ["ima", "dcm", "dat", "sdat", "coord"]
        self.supported_sequences = ["PRESS", "STEAM", "sSPECIAL", "MEGA"]
        self.CreateStatusBar(1)
        self.SetStatusText("Current pipeline: " + " → ".join(self.pipeline))
        
        self.current_step = 0
        self.show_editor = True
        self.debug = True
        self.save_raw = False
        self.controlfile = None
        
        self.Bind(EVT_LOG, self.on_log)
        self.Bind(wx.EVT_CLOSE, self.on_close) # save last files on close
        filepath = os.path.join(self.rootPath, "lastfiles.pickle") # load last files on open
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                filepaths, filepaths_wref = pickle.load(f)
            self.inputMRSfiles_dt.OnDropFiles(None, None, filepaths)
            self.inputwref_dt.OnDropFiles(None, None, filepaths_wref)
        self.on_toggle_editor(None)
        
        self.bmpterminatecolor = wx.Bitmap("resources/terminate.png")
        self.bmpRunLCModel = wx.Bitmap("resources/run_lcmodel.png")

        self.reset()

    def reset(self, event=None):
        self.processing = False
        self.fast_processing = False
        self.button_terminate_processing.Disable()
        self.button_step_processing.Enable()
        self.button_auto_processing.Enable()
        self.button_open_pipeline.Enable()
        self.DDstepselection.Clear()
        self.DDstepselection.AppendItems("")
        self.DDstepselection
        if self.current_step >= len(self.steps):
            self.button_step_processing.SetBitmap(self.bmp_steppro)
        self.button_auto_processing.SetBitmap(self.bmp_autopro)
        self.current_step = 0
        self.Layout()
        if event is not None: event.Skip()
    
    def retrieve_steps(self):
        rootPath = os.path.dirname(__file__)
        while not os.path.exists(os.path.join(rootPath, "lcmodel")):
            if rootPath == "":
                self.log_error("Steps folder not found")
                return
            rootPath = os.path.dirname(rootPath)
        processing_files = glob.glob(os.path.join(rootPath, "steps", "*.py"))
        processing_steps = {}
        for file in processing_files:
            module_name = os.path.basename(file)[:-3]
            if module_name == "__init__": continue
            spec = importlib.util.spec_from_file_location(module_name, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and obj.__module__ == module_name:
                    obj = getattr(module, name)
                    processing_steps[name] = obj
        return processing_steps, rootPath

    def on_save_pipeline(self, event, filepath=None):
        if self.steps == []:
            self.log_warning("No pipeline to save")
            return
        if filepath is None:
            fileDialog = wx.FileDialog(self, "Save pipeline as", wildcard="Pipeline files (*.pipe)|*.pipe", defaultDir=self.rootPath, style=wx.FD_SAVE)
            if fileDialog.ShowModal() == wx.ID_CANCEL: return
            filepath = fileDialog.GetPath()
        if filepath == "":
            self.log_error(f"File not found")
            return
        tosave = []
        nodes = dict(self.pipelineWindow.pipelinePanel.nodegraph.nodes)
        for n in nodes.keys():
            params = [(v.idname, v.value) for k, v in nodes[n].properties.items()]
            tosave.append([nodes[n].idname, nodes[n].id, nodes[n].pos, params])
        tosave = [tosave]
        wires = list(self.pipelineWindow.pipelinePanel.nodegraph.wires)
        tosave.append([[w.srcsocket.node.id, w.srcsocket.idname, w.dstsocket.node.id, w.dstsocket.idname] for w in wires])
        # print(tosave)
        with open(filepath, 'wb') as f:
            pickle.dump(tosave, f)
        if event is not None: event.Skip()

    def on_load_pipeline(self, event):
        fileDialog = wx.FileDialog(self, "Choose a file", wildcard="Pipeline files (*.pipe)|*.pipe", defaultDir=self.rootPath, style=wx.FD_OPEN)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepath = fileDialog.GetPath()
        if filepath == "" or not os.path.exists(filepath):
            self.log_error("File not found: " + filepath)
            return
        with open(filepath, 'rb') as f:
            toload = pickle.load(f)
        self.pipelineWindow.pipelinePanel.nodegraph.nodes = {}
        self.pipelineWindow.pipelinePanel.nodegraph.wires = []
        for data in toload[0]:
            self.pipelineWindow.pipelinePanel.nodegraph.AddNode(data[0], data[1], data[2])
            for p in data[3]:
                self.pipelineWindow.pipelinePanel.nodegraph.nodes[data[1]].properties[p[0]].value = p[1]
        for data in toload[1]:
            src = self.pipelineWindow.pipelinePanel.nodegraph.nodes[data[0]].FindSocket(data[1])
            dst = self.pipelineWindow.pipelinePanel.nodegraph.nodes[data[2]].FindSocket(data[3])
            self.pipelineWindow.pipelinePanel.nodegraph.ConnectNodes(src, dst)
        self.pipelineWindow.pipelinePanel.nodegraph.Refresh()
        self.pipeline, self.steps = self.retrieve_pipeline()
        self.SetStatusText("Current pipeline: " + " → ".join(step.__class__.__name__ for step in self.steps))
        event.Skip()

    def on_toggle_editor(self, event):
        self.show_editor = not self.show_editor
        if self.show_editor: self.pipelineWindow.Show()
        else: self.pipelineWindow.Hide()
        self.Layout()
        if event is not None: event.Skip()

    def on_read_coord(self, event):
        fileDialog = wx.FileDialog(self, "Choose a file", wildcard="coord files (*.coord)|*.coord", defaultDir=self.rootPath, style=wx.FD_OPEN)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepath = fileDialog.GetPaths()[0]
        if filepath == "" or not os.path.exists(filepath):
            print(f"File not found:\n\t{filepath}")
            return
        self.read_file(None, filepath)
        event.Skip()

    def on_plot_click(self, event):
        if not self.dataSteps or len(self.dataSteps) <= 1: # first entry is the original data
            self.consoltext.AppendText("Need to process the data before plotting the results\n")
            return
        selected_item_index = self.list_ctrl.GetFirstSelected()
        if len(self.dataSteps) < selected_item_index + 2: # for step 1 (index 0), we should have a length of 2 (original and result of step 1)
            self.consoltext.AppendText("The step has not been performed yet\n")
            return
        self.matplotlib_canvas.clear()
        plot_mrs(self.dataSteps[selected_item_index + 1], self.matplotlib_canvas, title="Result of " + self.pipeline[selected_item_index])
        event.Skip()
    
    def on_button_step_processing(self, event):
        self.pipelineWindow.Hide()
        self.button_open_pipeline.Disable()
        self.button_step_processing.Disable()
        self.button_auto_processing.Disable()
        if 0 < self.current_step:
            self.button_terminate_processing.Disable()
        for filepath in self.inputMRSfiles_dt.filepaths:
            if not os.path.exists(filepath):
                self.log_error(f"File not found:\n\t{filepath}")
                return
        for filepath in self.inputwref_dt.filepaths:
            if not os.path.exists(filepath):
                self.log_error(f"File not found:\n\t{filepath}")
                return

        thread_processing = threading.Thread(target=processingPipeline.processPipeline, args=[self])
        thread_processing.start()
        event.Skip()
        
    def on_autorun_processing(self, event):
        self.fast_processing = not self.fast_processing
        if not self.fast_processing:
            self.button_auto_processing.SetBitmap(self.bmp_autopro)
            self.log_info("AUTORUN PAUSED")
        else:
            self.button_auto_processing.SetBitmap(self.bmp_pause)
            self.button_step_processing.Disable()
            self.log_info("AUTORUN ACTIVATED")
            if 0 < self.current_step:
                self.button_terminate_processing.Disable()
            thread_processing = threading.Thread(target=processingPipeline.autorun_pipeline_exe, args=[self])
            thread_processing.start()
        event.Skip()

    def on_open_output_folder(self, event):
        if hasattr(self, "outputpath") and os.path.exists(self.outputpath):
            os.startfile(self.outputpath)
        else:
            output_folder = os.path.join(self.rootPath, "output")
            if not os.path.exists(output_folder): os.mkdir(output_folder)
            os.startfile(output_folder)
        event.Skip()        

    def on_toggle_save_raw(self, event):
        self.save_raw = self.button_toggle_save_raw.GetValue()
        if(self.save_raw):
            self.button_toggle_save_raw.SetWindowStyleFlag(wx.SIMPLE_BORDER)
            self.button_toggle_save_raw.SetBackgroundColour(wx.Colour(XISLAND2))
            self.log_info("Saving Raw data Enabled")
        else:
            self.button_toggle_save_raw.SetWindowStyleFlag(wx.NO_BORDER)
            self.button_toggle_save_raw.SetBackgroundColour(wx.Colour(XISLAND1))
            self.log_info("Saving Raw data Disabled")
        event.Skip()

    def on_open_pipeline(self, event):
        self.pipelineWindow.Show()
        self.Layout()
        if event is not None: event.Skip()
        
    def on_set_control(self, event):
        fileDialog = wx.FileDialog(self, "Choose a file", wildcard=".control file (*.control)|*.control", defaultDir=self.rootPath, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepath = fileDialog.GetPaths()[0]
        if filepath == "" or not os.path.exists(filepath):
            self.log_error(f"File not found:\n\t{filepath}")
            return
        self.controlfile = filepath
        self.log_info(f"Control file set to:\n\t{filepath}")
        event.Skip()

    def read_file(self, event, filepath=None, new_window=False):
        if filepath is None:
            index = self.inputwref_drag_and_drop_list.GetSelection()
            if index == wx.NOT_FOUND:
                return
            filepath = self.inputMRSfiles_dt.filepaths[index]
        if filepath == "" or not os.path.exists(filepath):
            print("File not found")
            return
        if not any([filepath.lower().endswith(ext) for ext in self.supported_files]):
            self.log_error("Invalid file type")
            return
        
        if new_window:
            child = PlotFrame(os.path.basename(filepath))
            canvas = child.canvas
            text = child.text
        else:
            canvas = self.matplotlib_canvas
            text = self.infotext
        
        if filepath.lower().endswith(".coord"):
            f = ReadlcmCoord(filepath)
            canvas.clear()
            plot_coord(f, canvas.figure, title=filepath)
            canvas.draw()
            dtab = '\n\t\t'
            text.SetValue("")

            def pad_string(input_str, desired_length):
                desired_length = int(desired_length)    
                return input_str.ljust(desired_length)

            text.WriteText(f"File: {filepath}\n\tNumber of points: {len(f['ppm'])}\n\tNumber of metabolites: {len(f['conc'])} ({f['nfit']} fitted)\n"
                                    + f"\t0th-order phase: {f['ph0']}\n\t1st-order phase: {f['ph1']}\n\tFWHM: {f['linewidth']}\n\tSNR: {f['SNR']}\n\tData shift: {f['datashift']}\n"
                                    + f"""\tMetabolites:\n\t\t{dtab.join([f"{pad_string(c['name'], 4)}: (±{pad_string(str(c['SD']) + '%', 3)}, Cr: {str(c['c_cr'])})" for c in f['conc']])}\n""")
            if event is not None: event.Skip()
            return
        
        else:
            f = None
            if filepath.lower().endswith((".ima", ".dcm")):
                f = suspect.io.load_siemens_dicom(filepath)
            elif filepath.lower().endswith(".dat"):
                f = suspect.io.load_twix(filepath)
                f = suspect.processing.channel_combination.combine_channels(f)
            elif filepath.lower().endswith(".sdat"):
                f = suspect.io.load_sdat(filepath)
            if len(f.shape) == 1: flist = [f]
            else: flist = [f.inherit(d) for d in f]
            canvas.clear()
            plot_mrs(flist, canvas.figure, title=filepath)
            canvas.draw()
            text.SetValue("")
            info = f"File: {filepath}"
            if hasattr(f, "np"): info += f"\n\tNumber of points: {f.np}"
            if hasattr(f, "f0"): info += f"\n\tScanner frequency (MHz): {f.f0}"
            if hasattr(f, "dt"): info += f"\n\tDwell time (s): {f.dt}"
            if hasattr(f, "df"): info += f"\n\tFrequency delta (Hz): {f.df}"
            if hasattr(f, "sw"): info += f"\n\tSpectral Width (Hz): {f.sw}"
            if hasattr(f, "te"): info += f"\n\tEcho time (ms): {f.te}"
            if hasattr(f, "tr"): info += f"\n\tRepetition time (ms): {f.tr}"
            info += f"\n\tPPM range: {[f.hertz_to_ppm(-f.sw / 2.0), f.hertz_to_ppm(f.sw / 2.0)]}"
            try:
                if hasattr(f, "centre"): info += f"\n\tCentre: {f.centre}"
            except: pass
            if hasattr(f, "metadata") and hasattr(f.metadata, "items"): info += "\n\tMetadata: " + "\n\t\t".join([f"{k}: {v}" for k, v in f.metadata.items()])
            text.WriteText(info)
        if event is not None: event.Skip()
        return
        
    def on_DDstepselection_select(self, event):
        selected_item = self.DDstepselection.GetValue()
        if(selected_item==""):
            self.matplotlib_canvas.clear()
        elif(selected_item=="lcmodel"):
            filepath = os.path.join(self.lcmodelsavepath, "result.coord")
            if os.path.exists(filepath):
                self.matplotlib_canvas.clear()
                self.read_file(None, filepath)
                self.matplotlib_canvas.draw()
            else:
                self.log_warning("LCModel output not found")
        else:
            index = self.DDstepselection.GetSelection()
            for step in self.steps:
                if step.__class__.__name__ in selected_item:
                    dataDict = {
                        "input": self.dataSteps[index-1],
                        "wref": self.wrefSteps[index-1],
                        "original": self.dataSteps[0],
                        "wref_original": self.wrefSteps[0],
                        "output": self.dataSteps[index],
                        "wref_output": self.wrefSteps[index]
                    }
                    self.matplotlib_canvas.clear()
                    step.plot(self.matplotlib_canvas.figure, dataDict)
                    self.matplotlib_canvas.draw()
                    event.Skip()
                    return
            self.log_warning("Step not found")

    def retrieve_pipeline(self):
        current_node = self.pipelineWindow.pipelinePanel.nodegraph.GetInputNode()
        pipeline = []
        steps = []
        while current_node is not None:
            for socket in current_node.GetSockets():
                if socket.direction == 1:
                    if len(socket.GetWires()) == 0:
                        current_node = None
                        continue
                    if len(socket.GetWires()) > 1:
                        self.log_error("Only serial pipelines are allowed for now")
                        return pipeline, steps
                    for wire in socket.GetWires():
                        current_node = wire.dstsocket.node
                        pipeline.append(current_node.label)
                        steps.append(current_node)
        return pipeline, steps
    
    def log_text(self, colour, *args):
        text = ""
        for arg in args: text += str(arg)
        evt = LogEvent(myEVT_LOG, -1, text=text, colour=colour)
        wx.PostEvent(self, evt)

    def on_log(self, event):
        text = event.GetText()
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")+": "+text
        text=formatted_datetime+""
        colour = event.GetColour()
        self.consoltext.BeginTextColour(colour)
        self.consoltext.WriteText(text)
        self.consoltext.EndTextColour()
        self.consoltext.Newline()
        self.consoltext.SetScrollPos(wx.VERTICAL, self.consoltext.GetScrollRange(wx.VERTICAL))
        self.consoltext.ShowPosition(self.consoltext.GetLastPosition())
        event.Skip()

    def log_info(self, *args):
        colour = INFO_COLOR
        self.log_text(colour, *args)

    def log_error(self, *args):
        colour = ERROR_COLOR
        self.log_text(colour, *args)

    def log_warning(self, *args):
        colour = WARNING_COLOR
        self.log_text(colour, *args)

    def log_debug(self, *args):
        if not self.debug: return
        colour = DEBUG_COLOR
        self.log_text(colour, *args)

    def on_close(self, event):
        filepaths = self.inputMRSfiles_dt.filepaths
        filepaths_wref = self.inputwref_dt.filepaths
        if len(filepaths) > 0:
            tosave = [filepaths, filepaths_wref]
            filepath = os.path.join(self.rootPath, "lastfiles.pickle")
            with open(filepath, 'wb') as f:
                pickle.dump(tosave, f)
        self.Destroy()
        
    def OnResize(self, event):
        self.Layout()
        self.Refresh()

class MainApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True