import wx
import os
import glob
import inspect
import importlib.util
import threading
import pickle

from interface import utils
from interface.pipeline_frame import PipelineFrame
from interface.fitting_frame import FittingFrame
from interface.main_layout import LayoutFrame
from interface.plot_helpers import plot_coord, get_coord_info
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
        
        self.outputpath_base = os.path.join(os.getcwd(), "output")
        if not os.path.exists(self.outputpath_base): os.mkdir(self.outputpath_base)
        self.outputpath = self.outputpath_base
        self.load_lastfiles()

        self.retrieve_steps() # dictionary of processing steps definitions
        self.pipeline_frame = PipelineFrame(parent=self) # /!\ put this after retrieve_steps
        self.pipeline_frame.Hide()
        self.fitting_frame = FittingFrame(parent=self)
        self.fitting_frame.Hide()
        self.retrieve_pipeline()

        self.CreateStatusBar(1)
        self.update_statusbar()

        self.Bind(wx.EVT_CLOSE, self.on_close) # save last files on close
        self.Bind(wx.EVT_BUTTON, self.reset, self.button_terminate_processing)
        self.Bind(wx.EVT_BUTTON, self.on_autorun_processing, self.button_auto_processing)
        self.Bind(wx.EVT_BUTTON, self.on_open_output_folder, self.folder_button)
        self.Bind(wx.EVT_BUTTON, self.on_open_pipeline, self.pipeline_button)
        self.Bind(wx.EVT_BUTTON, self.on_open_fitting, self.fitting_button)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.on_show_debug, self.show_debug_button)
        self.Bind(wx.EVT_CHECKBOX, self.on_toggle_debug, self.debug_button)
        self.Bind(wx.EVT_BUTTON, self.on_reload, self.reload_button)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_BUTTON, self.on_button_step_processing, self.button_step_processing)
        self.Bind(wx.EVT_COMBOBOX, self.on_plot_box_selection)

        self.on_show_debug(None)
        self.reset()

    def reset(self, event=None):
        self.processing = False
        self.fast_processing = False
        self.button_terminate_processing.Disable()
        self.button_step_processing.Enable()
        self.button_auto_processing.Enable()
        if self.current_step >= len(self.steps):
            self.button_step_processing.SetBitmap(self.run_bmp)
        self.button_auto_processing.SetBitmap(self.autorun_bmp)
        self.current_step = 0
        self.Layout()
        if event is not None: event.Skip()
    
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

    def on_open_output_folder(self, event):
        if os.path.exists(self.outputpath):
            os.startfile(self.outputpath)
        event.Skip()

    def on_open_pipeline(self, event):
        self.pipeline_frame.Show()
        event.Skip()

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
        tosave = [self.MRSfiles.filepaths, self.Waterfiles.filepaths, self.basis_file_user, self.control_file_user, self.wm_file_user, self.gm_file_user, self.csf_file_user]
        filepath = os.path.join(os.getcwd(), "lastfiles.pickle")
        with open(filepath, 'wb') as f:
            pickle.dump(tosave, f)

    def load_lastfiles(self):
        filepath = os.path.join(os.getcwd(), "lastfiles.pickle")
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                filepaths, filepaths_wref, self.basis_file_user, self.control_file_user, self.wm_file_user, self.gm_file_user, self.csf_file_user = pickle.load(f)
            self.MRSfiles.on_drop_files(filepaths)
            self.Waterfiles.on_drop_files(filepaths_wref)

    def on_close(self, event):
        self.save_lastfiles()
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