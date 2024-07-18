import wx
import os
import glob
import inspect
import importlib.util
import threading
import pickle

from . import utils, pipeline_window
from .main_layout import LayoutFrame
from processing import processingPipeline
from inout.readcoord import ReadlcmCoord
from interface.plot_helpers import plot_coord, get_coord_info
from interface.colours import(XISLAND1,XISLAND2)
    
class MainFrame(LayoutFrame):

    def __init__(self, *args, **kwds):
        LayoutFrame.__init__(self, *args, **kwds)

        self.processing_steps, self.rootPath = self.retrieve_steps() # dictionary of processing steps definitions
        self.pipelineWindow = pipeline_window.PipelineWindow(parent=self) # /!\ put this after retrieve_steps
        self.retrieve_pipeline() # list of processing step instances in pipeline, should be changed to strings only

        self.CreateStatusBar(1)
        self.update_statusbar()
        
        self.current_step = 0
        self.show_editor = True
        self.save_raw = False
        self.controlfile = None
        
        utils.init_logging(self.consoltext)
        utils.set_debug(True)
        self.Bind(wx.EVT_CLOSE, self.on_close) # save last files on close
        filepath = os.path.join(self.rootPath, "lastfiles.pickle") # load last files on open
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                filepaths, filepaths_wref = pickle.load(f)
            self.MRSfiles.on_drop_files(filepaths)
            self.Waterfiles.on_drop_files(filepaths_wref)
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
        # self.DDstepselection.Clear()
        # self.DDstepselection.AppendItems("")
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
                utils.log_error("Steps folder not found")
                return
            rootPath = os.path.dirname(rootPath)
        processing_files = glob.glob(os.path.join(rootPath, "steps", "*.py"))
        processing_steps = {}
        for file in processing_files:
            module_name = os.path.basename(file)[:-3]
            if module_name.startswith("_"): continue
            spec = importlib.util.spec_from_file_location(module_name, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and obj.__module__ == module_name:
                    obj = getattr(module, name)
                    processing_steps[name] = obj
        return processing_steps, rootPath

    def update_statusbar(self):
        self.SetStatusText("Current pipeline: " + " → ".join(step.__class__.__name__ for step in self.steps))

    def on_toggle_editor(self, event):
        self.show_editor = not self.show_editor
        if self.show_editor: self.pipelineWindow.Show()
        else: self.pipelineWindow.Hide()
        self.Layout()
        if event is not None: event.Skip()

    def on_button_step_processing(self, event):
        self.pipelineWindow.Hide()
        self.button_step_processing.Disable()
        self.button_auto_processing.Disable()
        if 0 < self.current_step:
            self.button_terminate_processing.Disable()
        for filepath in self.MRSfiles.filepaths:
            if not os.path.exists(filepath):
                utils.log_error(f"File not found:\n\t{filepath}")
                self.reset()
                return
        for filepath in self.Waterfiles.filepaths:
            if not os.path.exists(filepath):
                utils.log_error(f"File not found:\n\t{filepath}")
                self.reset()
                return

        thread_processing = threading.Thread(target=processingPipeline.processPipeline, args=[self])
        thread_processing.start()
        event.Skip()
        
    def on_autorun_processing(self, event):
        self.DDstepselection.Clear()
        self.DDstepselection.AppendItems("")
        self.fast_processing = not self.fast_processing
        if not self.fast_processing:
            self.button_auto_processing.SetBitmap(self.bmp_autopro)
            utils.log_info("AUTORUN PAUSED")
        else:
            self.button_auto_processing.SetBitmap(self.bmp_pause)
            self.button_step_processing.Disable()
            utils.log_info("AUTORUN ACTIVATED")
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
            utils.log_info("Saving Raw data Enabled")
        else:
            self.button_toggle_save_raw.SetWindowStyleFlag(wx.NO_BORDER)
            self.button_toggle_save_raw.SetBackgroundColour(wx.Colour(XISLAND1))
            utils.log_info("Saving Raw data Disabled")
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
            utils.log_error(f"File not found:\n\t{filepath}")
            return
        self.controlfile = filepath
        utils.log_info(f"Control file set to:\n\t{filepath}")
        event.Skip()
        
    def on_DDstepselection_select(self, event):
        selected_item = self.DDstepselection.GetValue()
        if(selected_item==""):
            self.matplotlib_canvas.clear()
        elif(selected_item=="lcmodel"):
            filepath = os.path.join(self.lcmodelsavepath, "result.coord")
            if os.path.exists(filepath):
                self.matplotlib_canvas.clear()
                f = ReadlcmCoord(filepath)
                plot_coord(f, self.matplotlib_canvas.figure, title=filepath)
                self.matplotlib_canvas.draw()
                self.infotext.SetValue(f"File: {filepath}\n{get_coord_info(f)}")
            else:
                utils.log_warning("LCModel output not found")
        else:
            index = self.DDstepselection.GetSelection()
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
        current_node = self.pipelineWindow.pipelinePanel.nodegraph.GetInputNode()
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
                    for wire in socket.GetWires():
                        current_node = wire.dstsocket.node
                        self.pipeline.append(current_node.GetLabel())
                        self.steps.append(current_node)

    def on_close(self, event):
        filepaths = self.MRSfiles.filepaths
        filepaths_wref = self.Waterfiles.filepaths
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