import wx
import os
import wx.lib.agw.pygauge as PG
import wx.lib.throbber as throbber


# import matplotlib_canvas
from . import matplotlib_canvas  # Use a relative import to import wxglade_out
from . import DragList
import wx.richtext
from GimelStudio.nodegraph_dnd import NodeGraphDropTarget

from constants import(BLACK_WX,XISLAND1,ORANGE_WX,XISLAND3,XISLAND3)
from constants import(XISLAND1,XISLAND2,XISLAND3,XISLAND4,XISLAND5,XISLAND6)

from . import custom_wxwidgets
# import sys
# import wx
# import ctypes
# try:
#     ctypes.windll.shcore.SetProcessDpiAwareness(True)
# except Exception:
#     pass

from gsnodegraph.gsnodegraph import EVT_GSNODEGRAPH_ADDNODEBTN
# from gsnodegraph.nodes import OutputNode, MixNode, ImageNode, BlurNode, BlendNode, ValueNode, FrequencyPhaseAlignementNode,AverageNode,RemoveBadAveragesNode,LineBroadeningNode,ZeroPaddingNode,EddyCurrentCorrectionNode,InputNode
# from gsnodegraph.nodegraph import NodeGraph
import gsnodegraph.nodes


# # Install a custom displayhook to keep Python from setting the global
# # _ (underscore) to the value of the last evaluated expression.
# # If we don't do this, our mapping of _ to gettext can get overwritten.
# # This is useful/needed in interactive debugging with PyShell.
# def _displayHook(obj):
#     """ Custom display hook to prevent Python stealing '_'. """

#     if obj is not None:
#         print(repr(obj))
        
def get_node_type(node):
    if isinstance(node, gsnodegraph.nodes.nodes.ZeroPaddingNode):
        return "ZeroPadding"
    elif isinstance(node, gsnodegraph.nodes.nodes.RemoveBadAveragesNode):
        return "RemoveBadAverages"
    elif isinstance(node, gsnodegraph.nodes.nodes.FrequencyPhaseAlignementNode):
        return "FreqPhaseAlignment"
    elif isinstance(node, gsnodegraph.nodes.nodes.AverageNode):
        return "Average"
    elif isinstance(node, gsnodegraph.nodes.nodes.EddyCurrentCorrectionNode):
        return "EddyCurrentCorrection"
    elif isinstance(node, gsnodegraph.nodes.nodes.LineBroadeningNode):
        return "LineBroadening"
    else:
        return "Unknown steps"


# # Add translation macro to builtin similar to what gettext does.
# import builtins
# builtins.__dict__['_'] = wx.GetTranslation

from . import PipelineNodeGraph

from . import pipeline_window


class FileDrop(wx.FileDropTarget):

    def __init__(self, parent, listbox: wx.ListBox, label):
        wx.FileDropTarget.__init__(self)
        self.parent = parent
        self.list = listbox
        self.label = label
        self.dropped_file_paths = []
        self.root = ""

    def OnDropFiles(self, x, y, filenames):
        if len(filenames) == 0:
            if len(self.dropped_file_paths) == 0:
                self.on_clear(wx.CommandEvent())
            return False
        self.dropped_file_paths.extend(filenames)
        roots = [f.rsplit(os.path.sep, 1)[0] for f in self.dropped_file_paths]
        if len(set(roots)) == 1 and len(self.dropped_file_paths) > 1:
            self.root = roots[0]
            self.list.Append([f.rsplit(os.path.sep, 1)[1] for f in filenames])
        else:
            self.root = ""
            self.list.Append([f for f in filenames])
        self.dropped_file_paths.sort()
        temp = self.list.GetStrings()
        temp.sort()
        self.list.Set(temp)
        self.label.SetLabel(str(len(self.dropped_file_paths)) +" files"
                            + (("\n" + "Root folder: " + self.root) if len(self.root) > 0 else ""))
        self.label.Parent.Layout()
        self.clear_button.Enable()
        self.minus_button.Enable()
        return True
    
    def on_clear(self, event):
        self.dropped_file_paths = []
        self.list.Set([])
        self.clear_button.Disable()
        self.minus_button.Disable()
        self.label.SetLabel("0 files")
        self.label.Parent.Layout()
        self.parent.log_info("Filepaths cleared")
        event.Skip()
        
    def on_plus(self, event):
        fileDialog = wx.FileDialog(self.parent, "Choose a file", wildcard="MRS files (*.ima, *.dcm, *.dat)|*.ima;*.dcm;*.dat",
                                   defaultDir=self.parent.rootPath, style=wx.FD_OPEN | wx.FD_MULTIPLE)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepaths = fileDialog.GetPaths()
        files = []
        for filepath in filepaths:
            if filepath == "" or not os.path.exists(filepath):
                self.parent.log_warning(f"File not found:\n\t{filepath}")
            else: files.append(filepath)
        ext = filepaths[0].rsplit(os.path.sep, 1)[1].rsplit(".", 1)[1]
        if not all([f.endswith(ext) for f in filepaths]):
            self.parent.log_error("Inconsistent file types")
            return False
        if ext.lower().strip() not in self.parent.supported_files:
            self.parent.log_error("Invalid file type")
            return False
        self.OnDropFiles(None, None, files)
        event.Skip()

    def on_minus(self, event):
        deleted_item = self.list.GetSelection()
        print(self.dropped_file_paths[deleted_item])
        new_paths = self.dropped_file_paths
        new_paths.pop(deleted_item)
        self.dropped_file_paths = []
        self.list.Set([])
        self.OnDropFiles(0, 0, new_paths)
        event.Skip()
     
class MyFrame(wx.Frame):

    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        WIDTH = 1200
        HEIGHT = 800
        
        font1 = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.NORMAL,wx.FONTWEIGHT_NORMAL, False)

        
        self.SetSize((WIDTH, HEIGHT))
        self.SetTitle("MRSprocessing")

        fileMenu = wx.Menu()
        viewMenu = wx.Menu()
        menuBar = wx.MenuBar()
        menuBar.SetBackgroundColour(wx.Colour(XISLAND1))
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(viewMenu, "&View")
        self.SetMenuBar(menuBar)

        open_coord = wx.MenuItem(fileMenu, wx.ID_ANY, "&Open COORD file", "Open .coord file")
        load_pipeline = wx.MenuItem(fileMenu, wx.ID_ANY, "&Load Pipeline", "Load .pipe file")
        save_pipeline = wx.MenuItem(fileMenu, wx.ID_ANY, "&Save Pipeline", "Save .pipe file")
        fileMenu.Append(open_coord)
        fileMenu.AppendSeparator()
        fileMenu.Append(load_pipeline)
        fileMenu.Append(save_pipeline)
        self.Bind(wx.EVT_MENU, self.on_read_coord, open_coord)
        self.Bind(wx.EVT_MENU, self.on_load_pipeline, load_pipeline)
        self.Bind(wx.EVT_MENU, self.on_save_pipeline, save_pipeline)

        self.toggle_editor = wx.MenuItem(viewMenu, wx.ID_ANY, "&Hide Editor", "Toggle Editor")
        viewMenu.Append(self.toggle_editor)
        self.Bind(wx.EVT_MENU, self.on_toggle_editor, self.toggle_editor)
        
        

        self.mainSplitter = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.rightSplitter = wx.SplitterWindow(self.mainSplitter, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)       
        # self.leftSplitter = wx.SplitterWindow(self.mainSplitter, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        # self.pipelineplotSplitter = wx.SplitterWindow(self.rightSplitter, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.consoleinfoSplitter = wx.SplitterWindow(self.rightSplitter, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)

        self.mainSplitter.SetMinimumPaneSize(100)
        self.rightSplitter.SetMinimumPaneSize(100)  
        # self.leftSplitter.SetMinimumPaneSize(100)


        self.leftPanel = wx.Panel(self.mainSplitter, wx.ID_ANY)
        self.leftSizer = wx.BoxSizer(wx.VERTICAL)
        self.leftPanel.SetSizer(self.leftSizer)
        self.rightPanel = wx.Panel(self.rightSplitter, wx.ID_ANY)
        self.rightSizer = wx.BoxSizer(wx.VERTICAL)
        self.rightPanel.SetSizer(self.rightSizer)
        
        

        #New input panel
        #MRS files
        
        self.inputMRSfiles_drag_and_drop_label = wx.StaticText(self.leftPanel, wx.ID_ANY, "Import MRS files here", style=wx.ALIGN_CENTRE_VERTICAL)
        self.inputMRSfiles_drag_and_drop_label.SetForegroundColour(wx.Colour(BLACK_WX))
        self.inputMRSfiles_drag_and_drop_label.SetFont(font1)

        
        
        self.inputMRSfilesButtonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.inputMRSfilesclear_button = wx.Button(self.leftPanel, wx.ID_ANY, "Clear")
        self.inputMRSfilesplus_button = wx.Button(self.leftPanel, wx.ID_ANY, "+")
        self.inputMRSfilesminus_button = wx.Button(self.leftPanel, wx.ID_ANY, "-")
        
        self.inputMRSfilesclear_button.SetFont(font1)
        self.inputMRSfilesplus_button.SetFont(font1)
        self.inputMRSfilesminus_button.SetFont(font1)

        
        self.inputMRSfilesButtonSizer.Add(self.inputMRSfilesplus_button, 0, wx.ALL | wx.EXPAND, 5)
        self.inputMRSfilesButtonSizer.Add(self.inputMRSfilesminus_button, 0, wx.ALL | wx.EXPAND, 5)
        self.inputMRSfilesButtonSizer.Add(self.inputMRSfilesclear_button, 0, wx.ALL | wx.EXPAND, 5)

        
        self.inputMRSfiles_drag_and_drop_list = wx.ListBox(self.leftPanel, wx.ID_ANY, choices=[], style=wx.LB_SINGLE | wx.LB_NEEDED_SB | wx.HSCROLL | wx.LB_OWNERDRAW)
        self.inputMRSfiles_drag_and_drop_list.SetBackgroundColour(wx.Colour(XISLAND4)) 
        
        self.inputMRSfiles_number_label = wx.StaticText(self.leftPanel, wx.ID_ANY, "0 Files imported", style=wx.ALIGN_TOP|wx.ALIGN_RIGHT)
        self.inputMRSfiles_number_label.SetForegroundColour(wx.Colour(BLACK_WX))
        self.inputMRSfiles_number_label.SetFont(font1)

        # self.inputMRSfiles_number_label.SetLabel("2 Files imported")


        
        self.inputMRSfiles_dt = FileDrop(self, self.inputMRSfiles_drag_and_drop_list, self.inputMRSfiles_number_label)
        self.inputMRSfiles_drag_and_drop_list.SetDropTarget(self.inputMRSfiles_dt)
        self.inputMRSfiles_dt.clear_button = self.inputMRSfilesclear_button
        self.inputMRSfiles_dt.minus_button = self.inputMRSfilesminus_button
        self.Bind(wx.EVT_BUTTON, self.inputMRSfiles_dt.on_clear, self.inputMRSfilesclear_button)
        self.Bind(wx.EVT_BUTTON, self.inputMRSfiles_dt.on_plus, self.inputMRSfilesplus_button)
        self.Bind(wx.EVT_BUTTON, self.inputMRSfiles_dt.on_minus, self.inputMRSfilesminus_button)
        
        



        
    
        #wref

        self.inputwref_drag_and_drop_label = wx.StaticText(self.leftPanel, wx.ID_ANY, "Import water reference here (optional)", style=wx.ALIGN_CENTRE_VERTICAL)
        self.inputwref_drag_and_drop_label.SetForegroundColour(wx.Colour(BLACK_WX))
        self.inputwref_drag_and_drop_label.SetFont(font1)

        
        self.inputwrefButtonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.inputwrefclear_button = wx.Button(self.leftPanel, wx.ID_ANY, "Clear")
        self.inputwrefplus_button = wx.Button(self.leftPanel, wx.ID_ANY, "+")
        self.inputwrefminus_button = wx.Button(self.leftPanel, wx.ID_ANY, "-")
        
        self.inputwrefclear_button.SetFont(font1)
        self.inputwrefplus_button.SetFont(font1)
        self.inputwrefminus_button.SetFont(font1)
        
        self.inputwrefButtonSizer.Add(self.inputwrefplus_button, 0, wx.ALL | wx.EXPAND, 5)
        self.inputwrefButtonSizer.Add(self.inputwrefminus_button, 0, wx.ALL | wx.EXPAND, 5)
        self.inputwrefButtonSizer.Add(self.inputwrefclear_button, 0, wx.ALL | wx.EXPAND, 5)
  
        
        self.inputwref_drag_and_drop_list = wx.ListBox(self.leftPanel, wx.ID_ANY, choices=[], style=wx.LB_SINGLE | wx.LB_NEEDED_SB | wx.HSCROLL | wx.LB_OWNERDRAW)
        self.inputwref_drag_and_drop_list.SetBackgroundColour(wx.Colour(BLACK_WX)) 
        
        self.inputwref_number_label = wx.StaticText(self.leftPanel, wx.ID_ANY, "0 Files imported", style=wx.ALIGN_TOP|wx.ALIGN_RIGHT)
        self.inputwref_number_label.SetForegroundColour(wx.Colour(BLACK_WX))
        self.inputwref_number_label.SetFont(font1)
        
        
        self.inputwref_dt = FileDrop(self, self.inputwref_drag_and_drop_list, self.inputwref_number_label)
        self.inputwref_drag_and_drop_list.SetDropTarget(self.inputwref_dt)
        self.inputwref_dt.clear_button = self.inputwrefclear_button
        self.inputwref_dt.minus_button = self.inputwrefminus_button

        self.Bind(wx.EVT_BUTTON, self.inputwref_dt.on_clear, self.inputwrefclear_button)
        self.Bind(wx.EVT_BUTTON, self.inputwref_dt.on_plus, self.inputwrefplus_button)
        self.Bind(wx.EVT_BUTTON, self.inputwref_dt.on_minus, self.inputwrefminus_button)
        


        
        ###################################################
        
        
        # self.clear_button = wx.Button(self.leftPanel, wx.ID_ANY, "Clear Inputs")
        # self.water_ref_button = wx.Button(self.leftPanel, wx.ID_ANY, "Toggle Water Reference")
        # self.clear_button.SetBackgroundColour(wx.Colour(BLACK_WX))  # Set the background color (RGB values)
        # self.water_ref_button.SetBackgroundColour(wx.Colour(BLACK_WX))  # Set the background color (RGB values)
        # self.clear_button.SetForegroundColour(wx.Colour(BLACK_WX))
        # self.water_ref_button.SetForegroundColour(wx.Colour(BLACK_WX))
        

        
        
        # self.leftSizer.Add(self.clear_button, 0, wx.ALL | wx.EXPAND, 5)
        # self.leftSizer.Add(self.water_ref_button, 0, wx.ALL | wx.EXPAND, 5)
        # self.clear_button.Disable()
        # self.water_ref_button.Disable()

        # self.drag_and_drop_list = wx.ListBox(self.leftPanel, wx.ID_ANY, choices=[], style=wx.LB_SINGLE | wx.LB_NEEDED_SB | wx.HSCROLL | wx.LB_SORT | wx.LB_OWNERDRAW)
        # self.drag_and_drop_list.SetBackgroundColour(wx.Colour(BLACK_WX))  # Set the background color (RGB values)

        # self.drag_and_drop_label = wx.StaticText(self.leftPanel, wx.ID_ANY, "Drop Inputs Files Here", style=wx.ALIGN_CENTRE_VERTICAL)
        # self.drag_and_drop_label.SetForegroundColour(wx.Colour(BLACK_WX))

        self.Bind(wx.EVT_LISTBOX_DCLICK, self.read_file, self.inputMRSfiles_drag_and_drop_list)

        # self.leftSizer.Add(self.drag_and_drop_label, 0, wx.ALL | wx.EXPAND, 5)
        # self.leftSizer.Add(self.drag_and_drop_list, 1, wx.ALL | wx.EXPAND, 5)


        self.leftSizer.Add(self.inputMRSfiles_drag_and_drop_label, 0, wx.ALL | wx.EXPAND, 5)
        self.leftSizer.Add(self.inputMRSfilesButtonSizer, 0, wx.ALL | wx.EXPAND, 5)
        self.leftSizer.Add(self.inputMRSfiles_drag_and_drop_list, 1, wx.ALL | wx.EXPAND, 5)
        self.leftSizer.Add(self.inputMRSfiles_number_label, 0, wx.ALL | wx.EXPAND, 5)

        self.leftSizer.AddSpacer(20) 

        
        self.leftSizer.Add(self.inputwref_drag_and_drop_label, 0, wx.ALL | wx.EXPAND, 5)
        self.leftSizer.Add(self.inputwrefButtonSizer, 0, wx.ALL | wx.EXPAND, 5)
        self.leftSizer.Add(self.inputwref_drag_and_drop_list, 0, wx.ALL | wx.EXPAND, 5)
        self.leftSizer.Add(self.inputwref_number_label, 0, wx.ALL | wx.EXPAND, 5)


        
        ### RIGHT PANEL ###
        self.Processing_Sizer= wx.BoxSizer(wx.HORIZONTAL)
        
        self.bmp_steppro = wx.Bitmap("resources/run.png", wx.BITMAP_TYPE_PNG)  
        self.bmp_steppro_greyed= wx.Bitmap("resources/run_greyed.png", wx.BITMAP_TYPE_PNG) 
        self.button_step_processing = custom_wxwidgets.BtmButtonNoBorder(self.rightPanel, wx.ID_ANY, self.bmp_steppro)
        self.button_step_processing.SetBackgroundColour(wx.Colour(XISLAND1))  # Set the background color (RGB values)
        self.button_step_processing.SetMinSize((-1, 100))
        self.button_step_processing.SetToolTip("Run next step of the pipeline \nand show its results plot") 
        
        self.bmp_autopro = wx.Bitmap("resources/autorun.png", wx.BITMAP_TYPE_PNG)  # Replace with your image path
        self.bmp_autopro_greyed = wx.Bitmap("resources/autorun_greyed.png", wx.BITMAP_TYPE_PNG)  # Replace with your image path
        self.bmp_pause = wx.Bitmap("resources/pause.png", wx.BITMAP_TYPE_PNG) 

        self.button_auto_processing = custom_wxwidgets.BtmButtonNoBorder(self.rightPanel, wx.ID_ANY, self.bmp_autopro)
        self.button_auto_processing.SetBackgroundColour(wx.Colour(XISLAND1))  # Set the background color (RGB values)
        self.button_auto_processing.SetMinSize((-1, 100))
        self.button_auto_processing.SetToolTip("Run all the steps after one another until desactivation, \nshow only plot of the last step processed") 

        
        self.bmp_terminate= wx.Bitmap("resources/terminate.png", wx.BITMAP_TYPE_PNG)
        self.bmp_terminate_greyed = wx.Bitmap("resources/terminate_greyed.png", wx.BITMAP_TYPE_PNG)  # Replace with your image path
        self.button_terminate_processing = custom_wxwidgets.BtmButtonNoBorder(self.rightPanel, wx.ID_ANY, self.bmp_terminate)
        self.button_terminate_processing.SetBackgroundColour(wx.Colour(XISLAND1))  # Set the background color (RGB values)
        self.button_terminate_processing.SetMinSize((-1, 100))
        self.button_terminate_processing.Disable()

        bmp_folder = wx.Bitmap("resources/open_folder.png", wx.BITMAP_TYPE_PNG)
        # bmp_folder.SetSize((100, 100))
        # bmp_folder.SetScaleFactor(8)
        self.button_open_output_folder = custom_wxwidgets.BtmButtonNoBorder(self.rightPanel, wx.ID_ANY, bmp_folder)
        self.button_open_output_folder.SetBackgroundColour(wx.Colour(XISLAND1))
        self.button_open_output_folder.SetMinSize((-1, 100))
        self.button_open_output_folder.SetMaxSize((-1, 100))
        self.button_terminate_processing.SetToolTip("Open folder of the results figures") 


        bmp_raw = wx.Bitmap("resources/save_raw_data.png", wx.BITMAP_TYPE_PNG)
        self.button_toggle_save_raw = wx.BitmapToggleButton(self.rightPanel, wx.ID_ANY, bmp_raw)
        self.button_toggle_save_raw.SetBackgroundColour(wx.Colour(XISLAND1))
        self.button_toggle_save_raw.SetMinSize((-1, 100))
        self.button_toggle_save_raw.SetValue(False)
        self.button_toggle_save_raw.SetToolTip("Save raw data in the output folder")
        self.button_toggle_save_raw.SetWindowStyleFlag(wx.NO_BORDER)   
        
        self.button_terminate_processing.SetToolTip("Stop the current processing of the Pipeline  \nand come back to the initial state") 



        self.bmp_pipeline= wx.Bitmap("resources/Open_Pipeline.png", wx.BITMAP_TYPE_PNG)
        self.button_open_pipeline = custom_wxwidgets.BtmButtonNoBorder(self.rightPanel, wx.ID_ANY, self.bmp_pipeline)
        self.button_open_pipeline.SetBackgroundColour(wx.Colour(XISLAND1))  # Set the background color (RGB values)
        self.button_open_pipeline.SetMinSize((-1, 100))
        self.button_open_pipeline.SetToolTip("Open editor of the \npipeline to modify it") 

        
        
        self.ProgressBar_Sizer= wx.BoxSizer(wx.VERTICAL)

        self.progress_bar= PG.PyGauge(self.rightPanel, -1, size=(300, 35), style=wx.GA_HORIZONTAL)
        self.progress_bar.SetValue(0)
        self.progress_bar.SetBorderPadding(5)
        self.progress_bar.SetBarColor(wx.Colour(XISLAND3))
        self.progress_bar.SetBackgroundColour(wx.WHITE)
        self.progress_bar.SetBorderColor(wx.BLACK)
        
        self.ProgressBar_text_Sizer= wx.BoxSizer(wx.VERTICAL)
        
        
        self.progress_bar_info =  wx.StaticText(self.rightPanel, wx.ID_ANY, "Progress (0/0):", style=wx.ALIGN_CENTRE_VERTICAL)
        self.progress_bar_info.SetForegroundColour(wx.Colour(BLACK_WX)) 
        self.progress_bar_info.SetFont(font1)
        
        self.progress_bar_LCModel_info =  wx.StaticText(self.rightPanel, wx.ID_ANY, "LCModel: (0/1)", style=wx.ALIGN_CENTRE_VERTICAL)
        self.progress_bar_LCModel_info.SetForegroundColour(wx.Colour(BLACK_WX)) 
        self.progress_bar_LCModel_info.SetFont(font1)


        self.ProgressBar_text_Sizer.Add(self.progress_bar_info, 0, wx.ALL | wx.EXPAND, 5)
        self.ProgressBar_text_Sizer.Add(self.progress_bar_LCModel_info, 0, wx.ALL | wx.EXPAND, 5)


        self.ProgressBar_Sizer.Add(self.progress_bar, 0, wx.ALL | wx.EXPAND, 5)
        self.ProgressBar_Sizer.Add(self.ProgressBar_text_Sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        
        # self.StepSelectionSizer= wx.BoxSizer(wx.VERTICAL)
        
        # self.textdropdown =  wx.StaticText(self.rightPanel, wx.ID_ANY, "Current Processed Step :", style=wx.ALIGN_CENTRE_VERTICAL)
        # self.textdropdown.SetForegroundColour(wx.Colour(BLACK_WX)) 
        
        # self.DDstepselection =custom_wxwidgets.DropDown(self.rightPanel,items=["0-Initial state"],default="0-Initial state")
        # self.Bind(custom_wxwidgets.EVT_DROPDOWN, self.OnDropdownProcessingStep, self.DDstepselection)
        
        
        # self.StepSelectionSizer.Add(self.textdropdown, 0, wx.ALL | wx.EXPAND, 5)
        # self.StepSelectionSizer.Add(self.DDstepselection, 0, wx.ALL | wx.EXPAND, 5)
        
   
        # bmp= wx.Bitmap("resources/throbber1.png", wx.BITMAP_TYPE_PNG)
        # bmp2= wx.Bitmap("resources/throbber2.png", wx.BITMAP_TYPE_PNG)
        # bmp3= wx.Bitmap("resources/throbber3.png", wx.BITMAP_TYPE_PNG)
        # bmp4= wx.Bitmap("resources/throbber4.png", wx.BITMAP_TYPE_PNG)


        # self.processing_throbber = throbber.Throbber(self.rightPanel,-1,[bmp,bmp2,bmp3,bmp4], size=(100, 100), style=wx.NO_BORDER)
        # self.processing_throbber.Hide()
        self.Processing_Sizer.Add(self.button_open_output_folder, 0, wx.ALL | wx.EXPAND, 5)
        self.Processing_Sizer.Add(self.button_toggle_save_raw, 0, wx.ALL | wx.EXPAND, 5)
        self.Processing_Sizer.AddSpacer(10)
        self.Processing_Sizer.Add(self.button_open_pipeline, 0, wx.ALL | wx.EXPAND, 5)
        # self.Processing_Sizer.Add(self.StepSelectionSizer, 0, wx.ALL | wx.EXPAND, 5)
        self.Processing_Sizer.Add(self.button_step_processing, 0, wx.ALL | wx.EXPAND, 5)
        self.Processing_Sizer.Add(self.button_auto_processing, 0, wx.ALL | wx.EXPAND, 5)
        self.Processing_Sizer.Add(self.button_terminate_processing, 0, wx.ALL | wx.EXPAND, 5)
        # self.Processing_Sizer.Add(self.ProgressBar_Sizer, 0, wx.ALL | wx.EXPAND, 5)

        self.Processing_Sizer.Add(self.ProgressBar_Sizer, 0, wx.ALL | wx.EXPAND, 5)
        # self.Processing_Sizer.Add(self.processing_throbber, 0, wx.ALL | wx.EXPAND, 5)
        
        
        




        self.rightSizer.Add(self.Processing_Sizer, 0, wx.ALL | wx.EXPAND, 0)
        
        self.matplotlib_canvas = matplotlib_canvas.MatplotlibCanvas(self.rightPanel, wx.ID_ANY)
        self.infotext = wx.TextCtrl(self.consoleinfoSplitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.infotext.SetFont(font1)
        
        # self.consoltext = wx.TextCtrl(self.consoleinfoSplitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.consoltext = wx.richtext.RichTextCtrl(self.consoleinfoSplitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        # self.infotext.SetFont(font1)




        self.Bind(wx.EVT_BUTTON, self.on_terminate_processing, self.button_terminate_processing)
        self.Bind(wx.EVT_BUTTON, self.on_autorun_processing, self.button_auto_processing)
        self.Bind(wx.EVT_BUTTON, self.on_open_output_folder, self.button_open_output_folder)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_save_raw, self.button_toggle_save_raw)
        self.Bind(wx.EVT_BUTTON, self.on_open_pipeline, self.button_open_pipeline)


        self.rightSizer.Add(self.matplotlib_canvas, 1, wx.ALL | wx.EXPAND, 0)
        self.rightSizer.Add(self.matplotlib_canvas.toolbar, 0, wx.EXPAND, 0)
        


        # self.pipelinePanel  = PipelineNodeGraph.NodeGraphPanel(parent=self.pipelineplotSplitter, size=(100, 100))
        # self.pipelinePanel.SetDropTarget(NodeGraphDropTarget(self.pipelinePanel))
        
        self.pipelineWindow=pipeline_window.PipelineWindow(parent=self)
        # self.mgr.AddPane(self.nodegraph_pnl,
        #                   aui.AuiPaneInfo()
        #                   .Name("NODE_EDITOR")
        #                   .CaptionVisible(False)
        #                   .CenterPane()
        #                   .CloseButton(visible=False)
        #                   .BestSize(500, 300))


        ## pipelinepart ##
        # self.pipelinePanel = wx.Panel(self.pipelineplotSplitter, wx.ID_ANY)
        # self.pipelineSizer = wx.BoxSizer(wx.HORIZONTAL)
        # self.pipelinePanel.SetSizer(self.pipelineSizer)
        
        #pipeline node graph directly imported from a modified version of the main  of gsnodegraph
        # node_registry = {
        #     "image_nodeid": ImageNode,
        #     "mix_nodeid": MixNode,
        #     "blur_nodeid": BlurNode,
        #     "blend_nodeid": BlendNode,
        #     "value_nodeid": ValueNode,
        #     "output_nodeid": OutputNode,
        #     ##All the line below are added for MRS software
        #     "freqphasealignement_nodeid": FrequencyPhaseAlignementNode,
        #     "average_nodeid":AverageNode,
        #     "removebadaverages_nodeid":RemoveBadAveragesNode,
        #     "linebroadening_nodeid":LineBroadeningNode,
        #     "zeropadding_nodeid":ZeroPaddingNode,
        #     "eddyccurentcorrection_nodeid":EddyCurrentCorrectionNode,
        #     "input_nodeid":InputNode

        # }
        # # Setup the config with datatypes and node categories
        # config = {
        #     "image_datatype": "IMAGE",
        #     "node_datatypes": {
        #         "IMAGE": "#C6C62D",  # Yellow
        #         "INTEGER": "#A0A0A0",  # Grey
        #         "FLOAT": "#A0A0A0",  # Grey
        #         "VALUE": "#A0A0A0",  # Depreciated!
        #         "TRANSIENTS": "#B33641", 
        #     },
        #     "input_nodes_categories": ["INPUT"],
        #     "node_categories": {
        #         "INPUT": "#008000",  # Burgendy
        #         "DRAW": "#AF4467",  # Pink
        #         "MASK": "#084D4D",  # Blue-green
        #         "CONVERT": "#564B7C",  # Purple
        #         "FILTER": "#558333",  # Green
        #         "BLEND": "#498DB8",  # Light blue
        #         "QUALITY CONTROL": "#B33641",  # Light blue

        #         "COLOR": "#C2AF3A",  # Yellow
        #         "TRANSFORM": "#6B8B8B", # Blue-grey
        #         "OUTPUT": "#B33641"  # Red
        #     }
        # }

        # # Init the nodegraph
        # self.pipelinePanel = NodeGraph(self.pipelineplotSplitter, registry=node_registry, config=config)

        # # Add nodes to the node graph
        # node1 = self.pipelinePanel.AddNode("input_nodeid", nodeid= 'input0', pos=wx.Point(200, 100))
        # node2 = self.pipelinePanel.AddNode("zeropadding_nodeid",nodeid='zeropadding_node0', pos=wx.Point(400, 120))
        # node3 = self.pipelinePanel.AddNode("linebroadening_nodeid", nodeid='linebroadening0',pos=wx.Point(600, 100))
        # node4 = self.pipelinePanel.AddNode("freqphasealignement_nodeid",nodeid='freqphasealignement0', pos=wx.Point(800, 120))
        # node5 = self.pipelinePanel.AddNode("eddyccurentcorrection_nodeid",nodeid='eddyccurentcorrection0', pos=wx.Point(1000, 100))
        # node6 = self.pipelinePanel.AddNode("removebadaverages_nodeid",nodeid='removebadaverages0', pos=wx.Point(1200, 120))
        # node7 = self.pipelinePanel.AddNode("average_nodeid", nodeid='average0', pos=wx.Point(1400, 100))
        # self.pipelinePanel.ConnectNodes(self.pipelinePanel.nodes['input0'].GetSockets()[0],self.pipelinePanel.nodes['zeropadding_node0'].GetSockets()[1])
        # self.pipelinePanel.ConnectNodes(self.pipelinePanel.nodes['zeropadding_node0'].GetSockets()[0],self.pipelinePanel.nodes['linebroadening0'].GetSockets()[1])
        # self.pipelinePanel.ConnectNodes(self.pipelinePanel.nodes['linebroadening0'].GetSockets()[0],self.pipelinePanel.nodes['freqphasealignement0'].GetSockets()[1])
        # self.pipelinePanel.ConnectNodes(self.pipelinePanel.nodes['freqphasealignement0'].GetSockets()[0],self.pipelinePanel.nodes['eddyccurentcorrection0'].GetSockets()[1])
        # self.pipelinePanel.ConnectNodes(self.pipelinePanel.nodes['eddyccurentcorrection0'].GetSockets()[0],self.pipelinePanel.nodes['removebadaverages0'].GetSockets()[1])
        # self.pipelinePanel.ConnectNodes(self.pipelinePanel.nodes['removebadaverages0'].GetSockets()[0],self.pipelinePanel.nodes['average0'].GetSockets()[1])



        # # Maximize the window
        # self.Maximize(True)

        # # Bind events
        # self.pipelinePanel.nodegraph.Bind(EVT_GSNODEGRAPH_ADDNODEBTN, self.OnAddNodeMenuBtn)

        
        
        # self.list_ctrl = DragList.MyDragList(self.pipelinePanel,style=wx.BORDER_SUNKEN|wx.LC_REPORT)
        # self.list_ctrl.InsertColumn(0, "Pipeline Steps", width = 100)

        # self.list_ctrl.InsertItem(0, "ZeroPadding")
        # self.list_ctrl.InsertItem(1, "LineBroadening")
        # self.list_ctrl.InsertItem(2, "FreqPhaseAlignment")
        # self.list_ctrl.InsertItem(3, "EddyCurrentCorrection")
        # self.list_ctrl.InsertItem(4, "RemoveBadAverages")
        # self.list_ctrl.InsertItem(5, "Average")




        # self.pipelineparameters = wx.TextCtrl(self.pipelinePanel, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        # self.pipelineparameters.SetBackgroundColour(wx.Colour(200, 200, 200))  # Set the background color to black
        
        # self.context_menu_pipeline = wx.Menu()
        # self.context_menu_pipeline.Append(1, "Delete step")
        # self.context_menu_pipeline.Append(2, "Plot step Results")

        
        # self.Bind(wx.EVT_MENU, self.OnDeleteClick, id=1)
        # self.Bind(wx.EVT_MENU, self.OnPlotClick, id=2)

        # self.list_ctrl.Bind(wx.EVT_CONTEXT_MENU, self.OnRightClickList)

        
        # self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)


        
        # self.pipelineSizer.Add(self.list_ctrl, 0, wx.EXPAND, 0)
        # self.pipelineSizer.Add(self.pipelineparameters, 1, wx.EXPAND, 0)

        
        
        self.rightSplitter.SplitHorizontally(self.rightPanel, self.consoleinfoSplitter, -150)
        self.rightSplitter.SetSashGravity(1.)
        
        self.consoleinfoSplitter.SplitVertically(self.consoltext, self.infotext, 0)
        self.consoleinfoSplitter.SetSashGravity(.5)
        
        

        
        # self.pipelineplotSplitter.SplitVertically(self.pipelinePanel,self.rightPanel , -150)
        # self.pipelineplotSplitter.SetSashGravity(1.)
        
        
        self.SetBackgroundColour(wx.Colour(XISLAND1)) 



        self.mainSplitter.SplitVertically(self.leftPanel, self.rightSplitter, 300)
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.on_button_step_processing, self.button_step_processing)
        # self.dt = FileDrop(self, self.drag_and_drop_list, self.drag_and_drop_label)
        # self.leftPanel.SetDropTarget(self.dt)
        # self.dt.clear_button = self.clear_button
        # self.dt.water_ref_button = self.water_ref_button
        # self.Bind(wx.EVT_BUTTON, self.dt.on_clear, self.clear_button)
        # self.Bind(wx.EVT_BUTTON, self.dt.on_water_ref, self.water_ref_button)
        self.leftPanel.Disable()
        self.leftPanel.Enable()

        
        self.SetIcon(wx.Icon("resources/icon_32p.png"))

    def on_button_processing(self, event): # wxGlade: MyFrame.<event_handler>
        print("Event handler 'on_button_processing' not implemented!")
        event.Skip()
        
    # def OnAddNodeMenuBtn(self, event):
    #     # print(self.ng.nodes['lol'].GetSockets().GetWires())
    #     current_node= self.pipelinePanel.nodegraph.GetInputNode()
    #     pipeline =[]
    #     while current_node is not None:
    #         for socket in current_node.GetSockets():
    #             if socket.direction == 1:
    #                 if len(socket.GetWires())==0:
    #                     current_node=None
    #                 elif len(socket.GetWires())>1:
    #                     print("Error: Only allow serial pipeline for now (each node must be connected to only one another)")
    #                     current_node=None

    #                 else:
    #                     for wire in socket.GetWires():
    #                         current_node = wire.dstsocket.node
    #                         pipeline.append(get_node_type(wire.dstsocket.node))
                        
    #     print (pipeline)
    #     pos = (8, self.pipelinePanel.nodegraph.GetRect()[3]-310)
    #     self.pipelinePanel.PopupAddNodeMenu(pos)
        # print(self.ng.GetInputNode())
        # print()
        # print(self.ng.nodes['lol'].GetSockets()[0].GetWires()[0].dstsocket.node)
        # print(len(self.ng.nodes['lol'].GetSockets()[1].GetWires()))

        




    
    
