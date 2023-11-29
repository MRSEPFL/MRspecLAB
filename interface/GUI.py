import wx
import os
import glob
import inspect
import importlib.util
import threading
import suspect
import pickle

from . import wxglade_out
from .plots import plot_ima, plot_coord
from readcoord import ReadlcmCoord
import processingPipeline

from constants import(DARK_BEIGE_COLOR_WX,DARK_BEIGE_COLOR_WX_PUSHED,LIGHT_BEIGE_COLOR_WX)


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
        
        self.pipeline = self.retrievePipeline()
        self.steps = [self.processing_steps[step]() for step in self.pipeline]
        self.supported_files = ["ima", "dcm", "dat", "coord"]
        self.CreateStatusBar(1)
        self.SetStatusText("Current pipeline: " + " → ".join(self.pipeline))
        
        self.processing = False
        self.fast_processing = False
        self.next = False
        self.show_editor = True
        self.debug = True
        
        self.Bind(EVT_LOG, self.on_log)
        self.Bind(wx.EVT_CLOSE, self.on_close) # save last files on close
        filepath = os.path.join(self.rootPath, "lastfiles.pickle") # load last files on open
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                filepaths, wrefindex = pickle.load(f)
            self.dt.OnDropFiles(None, None, filepaths)
            if wrefindex is not None:
                self.dt.on_water_ref(None, wrefindex)

        self.on_toggle_editor(None)
        
        self.bmpterminatecolor= wx.Bitmap("resources/terminate.png")

    def on_read_mrs(self, event):
        self.import_to_list("MRS files (*.ima, *.dcm, *.dat)|*.ima;*.dcm;*.dat")
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
        tosave = [[(step.__class__.__name__, step.parameters) for step in self.steps]]
        nodes = dict(self.pipelineWindow.pipelinePanel.nodegraph.nodes)
        tosave.append([[nodes[n].idname, nodes[n].id, nodes[n].pos] for n in nodes.keys()])
        wires = list(self.pipelineWindow.pipelinePanel.nodegraph.wires)
        tosave.append([[w.srcsocket.node.id, w.srcsocket.idname, w.dstsocket.node.id, w.dstsocket.idname] for w in wires])
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
        if self.show_editor:
            # self.pipelineplotSplitter.SplitVertically(self.pipelineWindow.pipelinePanel, self.rightPanel)
            self.pipelineWindow.Show()
            self.toggle_editor.SetItemLabel("Hide Editor")
        else:
            self.pipelineWindow.Hide()
            # self.pipelineplotSplitter.Unsplit(self.pipelineplotSplitter.GetWindow1())
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
        
    # def OnDeleteClick(self, event):
    #     selected_item = self.list_ctrl.GetFirstSelected()
    #     if selected_item >= 0:
    #         self.list_ctrl.DeleteItem(selected_item)
    #         self.pipeline.pop(selected_item)
    #         self.steps.pop(selected_item)
            
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
    

        
    # def OnRightClickList(self, event):
    #     pos = event.GetPosition()
    #     pos = self.list_ctrl.ScreenToClient(pos)
    #     item, flags = self.list_ctrl.HitTest(pos)
        
    #     if item != -1:
    #         self.list_ctrl.Select(item)  # Select the item that was right-clicked
    #         self.PopupMenu(self.context_menu_pipeline)
            
    # def OnAddStep(self, event):
    #     # Get the label text to add it to the list
    #     label = event.GetEventObject()
    #     new_item_text = label.GetLabel()
    #     selected_item_index = self.list_ctrl.GetFirstSelected()
    #     if selected_item_index >= 0:
    #         self.list_ctrl.InsertItem(selected_item_index+1, new_item_text)
    #         self.pipeline.insert(selected_item_index+1, new_item_text)
    #         self.steps.insert(selected_item_index+1, self.processing_steps[new_item_text]())
            
        

    def on_button_step_processing(self, event):
        if not self.processing:
            self.pipeline=self.retrievePipeline()
            self.steps = [self.processing_steps[step]() for step in self.pipeline]
            self.processing = True
            self.next = False
            self.button_terminate_processing.Enable()
            # self.button_terminate_processing.SetBitmap(self.bmpterminatecolor)

            thread = threading.Thread(target=self.processPipeline, args=())
            thread.start()
        else:
            self.next = True
        if event is not None:event.Skip()

    def read_file(self, event, filepath=None): # file double-clicked in list
        if filepath is None:
            index = self.drag_and_drop_list.GetSelection()
            if index == wx.NOT_FOUND:
                return
            filepath = self.dt.dropped_file_paths[index]
        if filepath == "" or not os.path.exists(filepath):
            print("File not found")
            return
        if not any([filepath.lower().endswith(ext) for ext in self.supported_files]):
            self.log_error("Invalid file type")
            return
        if filepath.lower().endswith(".coord"):
            f = ReadlcmCoord(filepath)
            self.matplotlib_canvas.clear()
            plot_coord(f, self.matplotlib_canvas.figure, title=filepath)
            self.matplotlib_canvas.draw()
            dtab = '\n\t\t'
            self.infotext.SetValue("")
            self.infotext.WriteText(f"File: {filepath}\n\tNumber of points: {len(f['ppm'])}\n\tNumber of metabolites: {len(f['conc'])} ({f['nfit']} fitted)\n"
                                    + f"\t0th-order phase: {f['ph0']}\n\t1st-order phase: {f['ph1']}\n\tFWHM: {f['linewidth']}\n\tSNR: {f['SNR']}\n\tData shift: {f['datashift']}\n"
                                    + f"""\tMetabolites:\n\t\t{dtab.join([f"{c['name']}: {c['c']} (±{c['SD']}%, Cr: {c['c_cr']})" for c in f['conc']])}\n""")
            if event is not None: event.Skip()
            return
        
        else:
            f = None
            if filepath.lower().endswith((".ima", ".dcm")):
                f = suspect.io.load_siemens_dicom(filepath)
            elif filepath.lower().endswith(".dat"):
                f = suspect.io.load_twix(filepath)
                f = suspect.processing.channel_combination.combine_channels(f)
            if len(f.shape) == 1: flist = [f]
            else: flist = [f.inherit(d) for d in f]
            self.matplotlib_canvas.clear()
            plot_ima(flist, self.matplotlib_canvas.figure, title=filepath)
            self.matplotlib_canvas.draw()
            self.infotext.SetValue("")
            self.infotext.WriteText(f"File: {filepath}\n\tNumber of points: {f.np}\n\tScanner frequency (MHz): {f.f0}\n\tDwell time (s): {f.dt}\n\tFrequency delta (Hz): {f.df}\n"
                                + f"\tSpectral Width (Hz): {f.sw}\n\tEcho time (ms): {f.te}\n\tRepetition time (ms): {f.tr}\n"
                                + f"\tPPM range: {[f.hertz_to_ppm(-f.sw / 2.0), f.hertz_to_ppm(f.sw / 2.0)]}\n\tCentre: {f.centre}\n"
                                + "\tMetadata: " + "\n\t\t".join([f"{k}: {v}" for k, v in f.metadata.items()]))
        if event is not None: event.Skip()
        return

    def processPipeline(self):
        return processingPipeline.processPipeline(self)
    
    def on_autorun_processing(self, event):
        self.fast_processing = not self.fast_processing
        if not self.fast_processing:
            self.button_auto_processing.SetBitmap(self.bmp_autopro)
        else:
            self.button_auto_processing.SetBitmap(self.bmp_pause)

        if self.fast_processing: self.on_button_step_processing(None)
        event.Skip()
    
    def on_terminate_processing(self, event):
        self.processing = False
        self.fast_processing = False
        self.button_terminate_processing.Disable()        
        self.progress_bar_info.SetLabel("Progress(0/0):")
        self.button_auto_processing.SetBitmap(self.bmp_autopro)
        self.matplotlib_canvas.clear()
        event.Skip()
        
        
    def OnDropdownProcessingStep(self, event):
        print("->", event.value)

    def retrievePipeline(self):
        current_node= self.pipelineWindow.pipelinePanel.nodegraph.GetInputNode()
        pipeline =[]
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
                            pipeline.append(wxglade_out.get_node_type(wire.dstsocket.node))
        
        return pipeline
    
    def log_text(self, colour, *args):
        text = ""
        for arg in args: text += str(arg)
        evt = LogEvent(myEVT_LOG, -1, text=text, colour=colour)
        wx.PostEvent(self, evt)

    def on_log(self, event):
        text = event.GetText()
        colour = event.GetColour()
        self.consoltext.BeginTextColour(colour)
        self.consoltext.WriteText(text)
        self.consoltext.EndTextColour()
        self.consoltext.Newline()
        self.consoltext.SetScrollPos(wx.VERTICAL, self.consoltext.GetScrollRange(wx.VERTICAL))
        self.consoltext.ShowPosition(self.consoltext.GetLastPosition())
        event.Skip()

    def log_info(self, *args):
        colour = (100, 100, 255)
        self.log_text(colour, *args)

    def log_error(self, *args):
        colour = (255, 0, 0)
        self.log_text(colour, *args)

    def log_warning(self, *args):
        colour = (255, 255, 0)
        self.log_text(colour, *args)

    def log_debug(self, *args):
        if not self.debug: return
        colour = (0, 255, 0)
        self.log_text(colour, *args)

    def on_close(self, event):
        filepaths = self.dt.dropped_file_paths
        if len(filepaths) > 0:
            wrefindex = self.dt.wrefindex
            tosave = [filepaths, wrefindex]
            filepath = os.path.join(self.rootPath, "lastfiles.pickle")
            with open(filepath, 'wb') as f:
                pickle.dump(tosave, f)
        self.Destroy()

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True