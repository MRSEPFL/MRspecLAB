import wx
import os
import glob
import inspect
import importlib.util
import threading
import suspect
import pickle
import time
import matplotlib
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

import constants
from . import wxglade_out
from .plots import plot_ima, plot_coord
from inout.readcoord import ReadlcmCoord
from processing import processingPipeline
from .wxglade_out import PlotFrame

from datetime import datetime

from constants import(XISLAND1,XISLAND2,XISLAND3,XISLAND4,XISLAND5,XISLAND6)

# def get_node_type(node):
#     if isinstance(node, gsnodegraph.nodes.nodes.ZeroPaddingNode):
#         return "ZeroPadding"
#     elif isinstance(node, gsnodegraph.nodes.nodes.RemoveBadAveragesNode):
#         return "RemoveBadAverages"
#     elif isinstance(node, gsnodegraph.nodes.nodes.FrequencyPhaseAlignementNode):
#         return "FreqPhaseAlignment"
#     elif isinstance(node, gsnodegraph.nodes.nodes.AverageNode):
#         return "Average"
#     elif isinstance(node, gsnodegraph.nodes.nodes.EddyCurrentCorrectionNode):
#         return "EddyCurrentCorrection"
#     elif isinstance(node, gsnodegraph.nodes.nodes.LineBroadeningNode):
#         return "LineBroadening"
#     else:
#         return "Unknown steps"

myEVT_LOG = wx.NewEventType()
EVT_LOG = wx.PyEventBinder(myEVT_LOG, 1)
class LogEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id, text=None, colour=None):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.text = text
        self.colour = colour

    def GetText(self):
        return self.text
    
    def GetColour(self):
        return self.colour
    
class MyFrame(wxglade_out.MyFrame):

    def __init__(self, *args, **kwds):
        wxglade_out.MyFrame.__init__(self, *args, **kwds)

        self.rootPath = os.path.dirname(__file__)
        while not os.path.exists(os.path.join(self.rootPath, "lcmodel")): self.rootPath = os.path.dirname(self.rootPath)
        processing_files = glob.glob(os.path.join(self.rootPath, "steps", "*.py"))
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
        
        self.pipeline,self.steps = self.retrievePipeline()
        self.supported_files = ["ima", "dcm", "dat", "sdat", "coord"]
        self.supported_sequences = ["PRESS", "STEAM", "sSPECIAL", "MEGA"]
        self.CreateStatusBar(1)
        self.SetStatusText("Current pipeline: " + " → ".join(self.pipeline))
        
        self.processing = False
        self.fast_processing = False
        self.next = False
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
        
        self.bmpterminatecolor= wx.Bitmap("resources/terminate.png")
        self.bmpRunLCModel= wx.Bitmap("resources/run_lcmodel.png")

        self.current_step=0
        self.proces_completion =False
    
    def on_save_pipeline(self, event, filepath=None):
        if self.steps == []:
            print("No pipeline to save")
            return
        if filepath is None:
            fileDialog = wx.FileDialog(self, "Save pipeline as", wildcard="Pipeline files (*.pipe)|*.pipe", defaultDir=self.rootPath, style=wx.FD_SAVE)
            if fileDialog.ShowModal() == wx.ID_CANCEL: return
            filepath = fileDialog.GetPath()
        if filepath == "":
            print(f"File not found")
            return
        tosave = [[(step.__class__.__name__, step.parameters) for step in self.steps]]
        nodes = dict(self.pipelineWindow.pipelinePanel.nodegraph.nodes)
        tosave.append([[nodes[n].idname, nodes[n].id, nodes[n].pos] for n in nodes.keys()])
        wires = list(self.pipelineWindow.pipelinePanel.nodegraph.wires)
        tosave.append([[w.srcsocket.node.id, w.srcsocket.idname, w.dstsocket.node.id, w.dstsocket.idname] for w in wires])
        with open(filepath, 'wb') as f:
            pickle.dump(tosave, f)
        if event is not None: event.Skip()

    def on_load_pipeline(self, event):
        fileDialog = wx.FileDialog(self, "Choose a file", wildcard="Pipeline files (*.pipe)|*.pipe", defaultDir=self.rootPath, style=wx.FD_OPEN)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepath = fileDialog.GetPath()
        if filepath == "" or not os.path.exists(filepath):
            print("File not found")
            return
        with open(filepath, 'rb') as f:
            toload = pickle.load(f)
        # pipeline
        self.pipeline = []
        self.steps = []
        for data in toload[0]:
            self.pipeline = [data[0]]
            self.steps.append(self.processing_steps[data[0]]())
            self.steps[-1].parameters = data[1]
        # nodegraph
        self.pipelineWindow.pipelinePanel.nodegraph.nodes = {}
        self.pipelineWindow.pipelinePanel.nodegraph.wires = []
        for data in toload[-2]:
            self.pipelineWindow.pipelinePanel.nodegraph.AddNode(data[0], data[1], data[2])
        for data in toload[-1]:
            src = self.pipelineWindow.pipelinePanel.nodegraph.nodes[data[0]].FindSocket(data[1])
            dst = self.pipelineWindow.pipelinePanel.nodegraph.nodes[data[2]].FindSocket(data[3])
            self.pipelineWindow.pipelinePanel.nodegraph.ConnectNodes(src, dst)
        self.pipelineWindow.pipelinePanel.nodegraph.Refresh()
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
    
    def on_button_step_processing(self, event):
        # if not self.processing:
        #     self.pipeline=self.retrievePipeline()
        #     self.steps = [self.processing_steps[step]() for step in self.pipeline]
        #     self.processing = True
        #     self.next = False
        #     self.button_terminate_processing.Enable()
        #     # self.button_terminate_processing.SetBitmap(self.bmpterminatecolor)

        #     thread = threading.Thread(target=self.processPipeline, args=())
        #     thread.start()
        #     # self.processPipeline()
        # else:
        #     self.next = True
        # if event is not None:event.Skip()
        self.button_step_processing.Disable()
        self.button_auto_processing.Disable()
        if 0<self.current_step:  #because if it is equal to zero(procesing haven't began) the button is disable anyway 
            self.button_terminate_processing.Disable()
        self.progress_bar.SetValue(0)
        self.progress_bar.Update(100, 15000)
        thread_processing = threading.Thread(target=self.processPipeline, args=())
        thread_processing.start()
        event.Skip()
        
    def on_autorun_processing(self, event):
        self.fast_processing = not self.fast_processing
        if not self.fast_processing:
            self.button_auto_processing.SetBitmap(self.bmp_autopro)
            self.log_error("Autorun Paused")
        else:
            self.button_auto_processing.SetBitmap(self.bmp_pause)
            self.button_step_processing.Disable()
            self.log_error("Autorun Activated")
            if 0<self.current_step:  #because if it is equal to zero(procesing haven't began) the button is disable anyway 
                self.button_terminate_processing.Disable()
            self.progress_bar.SetValue(0)
            self.progress_bar.Update(100, 15000)
            thread_processing = threading.Thread(target=self.autorun_pipeline_exe, args=())
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

    def PostStepProcessingGUIChanges(self):
        if self.current_step == len(self.steps) + 1:
            self.log_info("Processing completed, no further steps")
            self.progress_bar_LCModel_info.SetLabel("LCModel: (1/1)" )

        if self.proces_completion:
            # output_folder = os.path.join(self.rootPath, "output")
            # dirs = [d for d in os.listdir("output") if os.path.isdir(os.path.join("output", d))]
            # last_modified_folder = max(dirs, key=lambda d: os.path.getmtime(os.path.join("output", d)))
            # last_modified_folder_path = os.path.join("output", last_modified_folder)
            if self.current_step == len(self.steps) + 1:
                self.DDstepselection.AppendItems("lcmodel")
            else:
                self.DDstepselection.AppendItems(str(self.current_step) + self.steps[self.current_step-1].__class__.__name__)
            self.DDstepselection.SetSelection(self.current_step)
            
            # steppath = os.path.join(self.outputpath, str(self.current_step) + self.steps[self.current_step-1].__class__.__name__)
            # print(steppath)
            # dirs_steps_proc= [d for d in os.listdir(last_modified_folder_path) if os.path.isdir(os.path.join(last_modified_folder_path, d))]
            # last_modified_dir_steps_proc = max(dirs_steps_proc, key=lambda d: os.path.getmtime(os.path.join(last_modified_folder_path, d)))
            # print(last_modified_dir_steps_proc)
            # latest_file = max(list_of_files, key=os.path.getctime)
            # print(latest_file)

            if self.current_step==1:
                self.pipelineWindow.Hide()
                self.button_open_pipeline.Disable()

            
            self.progress_bar.Update(0,50)
            time.sleep(0.100)
            self.progress_bar.Update(100-self.progress_bar.GetValue(),200)
            if 0<=self.current_step and self.current_step<=(len(self.steps)):
                self.updateprogress(self.steps[self.current_step-1],self.current_step,len(self.steps))
        else:
            self.progress_bar.Update(1,50)
            time.sleep(0.100)
            self.progress_bar.SetValue(0)
            if 0==self.current_step:
                self.on_terminate_processing(None)

            
            
            
        if 0<=self.current_step and self.current_step<=(len(self.steps)) and self.fast_processing==False:
                self.button_step_processing.Enable()
                self.button_auto_processing.Enable()
                
        if 0<self.current_step and self.fast_processing==False:##Can't be with the condition above because if the loading of the file failed, the current step will be 0 and thus the button must be disabled
            self.button_terminate_processing.Enable()
           
        if self.current_step==(len(self.steps)):
            self.button_step_processing.SetBitmap(self.bmpRunLCModel)
            
        #After Fast Processing update
        if self.fast_processing==True and self.current_step<=(len(self.steps)):
            self.progress_bar.SetValue(0)
            self.progress_bar.Update(100, 10000)
        elif self.fast_processing==True and self.current_step==(len(self.steps)+1):#When the fast processing finish all the execution (LCMODEL)
            self.button_auto_processing.SetBitmap(self.bmp_autopro)
            self.button_auto_processing.Disable()
            self.button_terminate_processing.Enable()
            
        self.proces_completion=False

    def updateprogress(self,current_step,current_step_index,totalstep):
        self.progress_bar_info.SetLabel("Progress ("+str(current_step_index)+ "/"+str(totalstep)+"):" +  " " +current_step.__class__.__name__ )
        # self.progress_bar_info.SetLabel("Progress ("+str(current_step_index)+ "/"+str(totalstep)+"):"+"\n"+str(current_step_index)+" - "+ current_step.__class__.__name__ )



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
            plot_ima(flist, canvas.figure, title=filepath)
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

    def processPipeline(self):
        return processingPipeline.processPipeline(self)
    
    def autorun_pipeline_exe(self):
        return processingPipeline.autorun_pipeline_exe(self)
    
    def on_terminate_processing(self, event):
        # self.processing = False
        self.fast_processing = False
        self.button_terminate_processing.Disable()
        self.button_step_processing.Enable()
        self.button_auto_processing.Enable()
        self.button_open_pipeline.Enable()
        self.DDstepselection.Clear()
        self.DDstepselection.AppendItems("")
        self.DDstepselection
        if self.current_step >=(len(self.steps)):
            self.button_step_processing.SetBitmap(self.bmp_steppro)

        self.current_step=0 
        self.progress_bar_info.SetLabel("Progress (0/0):")
        self.progress_bar_LCModel_info.SetLabel("LCModel: (0/1)" )

        self.progress_bar.SetValue(0)
        self.button_auto_processing.SetBitmap(self.bmp_autopro)
        # self.matplotlib_canvas.clear()
        self.Layout()
        if event is not None: event.Skip()
        
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

    def retrievePipeline(self):
        current_node= self.pipelineWindow.pipelinePanel.nodegraph.GetInputNode()
        pipeline =[]
        steps=[]
        while current_node is not None:
            for socket in current_node.GetSockets():
                if socket.direction == 1:
                    if len(socket.GetWires())==0:
                        current_node=None
                    elif len(socket.GetWires())>1:
                        print("Error: Only allow serial pipeline for now (each node must be connected to only one another)")
                        current_node=None

                    else:
                        for wire in socket.GetWires():
                            current_node = wire.dstsocket.node
                            # pipeline.append(wxglade_out.get_node_type(wire.dstsocket.node))
                            pipeline.append(current_node.label)
                            current_node.EditParametersProcessing()
                            steps.append(current_node.processing_step)

        return pipeline,steps
    
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
        colour = constants.INFO_COLOR
        self.log_text(colour, *args)

    def log_error(self, *args):
        colour = constants.ERROR_COLOR
        self.log_text(colour, *args)

    def log_warning(self, *args):
        colour = constants.WARNING_COLOR
        self.log_text(colour, *args)

    def log_debug(self, *args):
        if not self.debug: return
        colour = constants.DEBUG_COLOR
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
        
    def OnResize(self,event):
        self.Layout()
        self.Refresh()

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True
    
    
def pad_string(input_str, desired_length):

    desired_length = int(desired_length)    
    return input_str.ljust(desired_length)