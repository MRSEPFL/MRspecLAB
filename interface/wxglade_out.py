import os
import wx
import wx.richtext
import wx.lib.agw.pygauge as pygauge
# import wx.lib.throbber as throbber
from . import matplotlib_canvas, custom_wxwidgets
from constants import(BLACK_WX,ORANGE_WX,XISLAND1,XISLAND2,XISLAND3,XISLAND4,XISLAND5,XISLAND6)

class FileDrop(wx.FileDropTarget):
    def __init__(self, parent, listbox: wx.ListBox, label):
        wx.FileDropTarget.__init__(self)
        self.parent = parent
        self.list = listbox
        self.label = label
        self.filepaths = []
        self.root = ""
        self.list.Bind(wx.EVT_LISTBOX, self.on_select)
        self.list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_dclick)

    def OnDropFiles(self, x, y, filenames):
        if len(filenames) == 0:
            if len(self.filepaths) == 0:
                self.on_clear(wx.CommandEvent())
            return False
        self.filepaths.extend(filenames)
        self.list.Set([])
        if len(self.filepaths) > 1: # find common root folder
            root = ""
            if all([f[0] == self.filepaths[0][0] for f in self.filepaths]):
                root = os.path.commonpath(self.filepaths)
            if root != "": self.list.Append([f.replace(root, "") for f in self.filepaths])
            else: self.list.Append([f for f in self.filepaths])
        else: self.list.Append([f for f in self.filepaths])
        _sorted = sorted(enumerate(self.filepaths), key=lambda x: x[1])
        self.filepaths = [f[1] for f in _sorted]
        order = [f[0] for f in _sorted]
        temp = self.list.GetStrings()
        self.list.Set([temp[i] for i in order])  # sort filepaths and list in the same order
        self.label.SetLabel(str(len(self.filepaths)) +" files") # + (("\n" + "Root folder: " + self.root) if len(self.root) > 0 else ""))
        self.label.Parent.Layout()
        self.clear_button.Enable()
        self.minus_button.Enable()
        return True
    
    def on_clear(self, event):
        self.filepaths = []
        self.list.Set([])
        self.clear_button.Disable()
        self.minus_button.Disable()
        self.label.SetLabel("0 files")
        self.label.Parent.Layout()
        self.parent.log_info("Filepaths cleared")
        event.Skip()
        
    def on_plus(self, event):
        wildcard = "MRS files ("
        for ext in self.parent.supported_files: wildcard += f"*.{ext}, "
        wildcard = wildcard[:-2] + ")|"
        for ext in self.parent.supported_files: wildcard += f"*.{ext};"
        wildcard = wildcard[:-1]
        if hasattr(self.parent, "last_directory") and os.path.exists(self.parent.last_directory):
            defaultDir = self.parent.last_directory
        else: defaultDir = self.parent.rootPath
        fileDialog = wx.FileDialog(self.parent, "Choose a file", wildcard=wildcard, defaultDir=defaultDir, style=wx.FD_OPEN | wx.FD_MULTIPLE)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepaths = fileDialog.GetPaths()
        self.parent.last_directory = fileDialog.GetDirectory()
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
        if deleted_item != wx.NOT_FOUND:
            new_paths = self.filepaths
            new_paths.pop(deleted_item)
            self.filepaths = []
            self.list.Set([])
            self.OnDropFiles(0, 0, new_paths)
        event.Skip()

    def on_select(self, event):
        filename = self.filepaths[self.list.GetSelection()]
        self.parent.read_file(event, filename, new_window=True)
        event.Skip()

    def on_dclick(self, event):
        self.list.Deselect(self.list.GetSelection())
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
        menuBar = wx.MenuBar()
        menuBar.SetBackgroundColour(wx.Colour(XISLAND1))
        menuBar.Append(fileMenu, "&File")
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
        self.inputwref_drag_and_drop_list.SetBackgroundColour(wx.Colour(XISLAND4)) 
        
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
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.read_file, self.inputMRSfiles_drag_and_drop_list)

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
        
        self.playerPanel = wx.Panel(self.rightPanel, wx.ID_ANY)
        self.playerPanel.SetBackgroundColour(wx.Colour(XISLAND2)) 
        self.player_Sizer= wx.BoxSizer(wx.HORIZONTAL)
        self.playerPanel.SetSizer(self.player_Sizer)
        
        
        self.bmp_steppro = wx.Bitmap("resources/run.png", wx.BITMAP_TYPE_PNG)  
        self.bmp_steppro_greyed= wx.Bitmap("resources/run_greyed.png", wx.BITMAP_TYPE_PNG) 
        self.button_step_processing = custom_wxwidgets.BtmButtonNoBorder(self.playerPanel, wx.ID_ANY, self.bmp_steppro)
        self.button_step_processing.SetBackgroundColour(wx.Colour(XISLAND2))  # Set the background color (RGB values)
        self.button_step_processing.SetMinSize((-1, 100))
        self.button_step_processing.SetToolTip("Run next step of the pipeline \nand show its results plot") 
        
        self.bmp_autopro = wx.Bitmap("resources/autorun.png", wx.BITMAP_TYPE_PNG)  # Replace with your image path
        self.bmp_autopro_greyed = wx.Bitmap("resources/autorun_greyed.png", wx.BITMAP_TYPE_PNG)  # Replace with your image path
        self.bmp_pause = wx.Bitmap("resources/pause.png", wx.BITMAP_TYPE_PNG) 

        self.button_auto_processing = custom_wxwidgets.BtmButtonNoBorder(self.playerPanel, wx.ID_ANY, self.bmp_autopro)
        self.button_auto_processing.SetBackgroundColour(wx.Colour(XISLAND2))  # Set the background color (RGB values)
        self.button_auto_processing.SetMinSize((-1, 100))
        self.button_auto_processing.SetToolTip("Run all the steps after one another until desactivation, \nshow only plot of the last step processed") 

        
        self.bmp_terminate= wx.Bitmap("resources/terminate.png", wx.BITMAP_TYPE_PNG)
        self.bmp_terminate_greyed = wx.Bitmap("resources/terminate_greyed.png", wx.BITMAP_TYPE_PNG)  # Replace with your image path
        self.button_terminate_processing = custom_wxwidgets.BtmButtonNoBorder(self.playerPanel, wx.ID_ANY, self.bmp_terminate)
        self.button_terminate_processing.SetBackgroundColour(wx.Colour(XISLAND2))  # Set the background color (RGB values)
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
        self.button_toggle_save_raw.SetToolTip("Enable/Disable saving raw data\nin the output folder")
        self.button_toggle_save_raw.SetWindowStyleFlag(wx.NO_BORDER)   
        
        self.button_terminate_processing.SetToolTip("Stop the current processing of the Pipeline  \nand come back to the initial state") 


        bmp_control= wx.Bitmap("resources/open_ctrl_file.png", wx.BITMAP_TYPE_PNG)
        self.button_set_control = custom_wxwidgets.BtmButtonNoBorder(self.rightPanel, wx.ID_ANY, bmp_control)
        self.button_set_control.SetBackgroundColour(wx.Colour(XISLAND1))  # Set the background color (RGB values)
        self.button_set_control.SetMinSize((-1, 100))
        self.button_set_control.SetToolTip("Open control file in an editor of the \nto be able to modify it and load it\nas wanted") 


        self.bmp_pipeline= wx.Bitmap("resources/Open_Pipeline.png", wx.BITMAP_TYPE_PNG)
        self.button_open_pipeline = custom_wxwidgets.BtmButtonNoBorder(self.rightPanel, wx.ID_ANY, self.bmp_pipeline)
        self.button_open_pipeline.SetBackgroundColour(wx.Colour(XISLAND1))  # Set the background color (RGB values)
        self.button_open_pipeline.SetMinSize((-1, 100))
        self.button_open_pipeline.SetToolTip("Open editor of the \npipeline to modify it") 

        
        
        self.ProgressBar_Sizer= wx.BoxSizer(wx.VERTICAL)

        self.progress_bar= pygauge.PyGauge(self.playerPanel, -1, size=(300, 35), style=wx.GA_HORIZONTAL)
        self.progress_bar.SetValue(0)
        self.progress_bar.SetBorderPadding(5)
        self.progress_bar.SetBarColor(wx.Colour(XISLAND3))
        self.progress_bar.SetBackgroundColour(wx.WHITE)
        self.progress_bar.SetBorderColor(wx.BLACK)
        
        self.ProgressBar_text_Sizer= wx.BoxSizer(wx.VERTICAL)
        
        
        self.progress_bar_info =  wx.StaticText(self.playerPanel, wx.ID_ANY, "Progress (0/0):", style=wx.ALIGN_CENTRE_VERTICAL)
        self.progress_bar_info.SetForegroundColour(wx.Colour(BLACK_WX)) 
        self.progress_bar_info.SetFont(font1)
        
        self.progress_bar_LCModel_info =  wx.StaticText(self.playerPanel, wx.ID_ANY, "LCModel: (0/1)", style=wx.ALIGN_CENTRE_VERTICAL)
        self.progress_bar_LCModel_info.SetForegroundColour(wx.Colour(BLACK_WX)) 
        self.progress_bar_LCModel_info.SetFont(font1)


        self.ProgressBar_text_Sizer.Add(self.progress_bar_info, 0, wx.ALL | wx.EXPAND, 5)
        self.ProgressBar_text_Sizer.Add(self.progress_bar_LCModel_info, 0, wx.ALL | wx.EXPAND, 5)


        self.ProgressBar_Sizer.Add(self.progress_bar, 0, wx.ALL | wx.EXPAND, 5)
        self.ProgressBar_Sizer.Add(self.ProgressBar_text_Sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        # bmp_logo=wx.Bitmap("resources/logobig.png", wx.BITMAP_TYPE_PNG)
        # self.logo_image=wx.StaticBitmap(self.rightPanel, wx.ID_ANY, bitmap=bmp_logo)
             
        self.StepSelectionSizer= wx.BoxSizer(wx.VERTICAL)
        
        self.textdropdown =  wx.StaticText(self.rightPanel, wx.ID_ANY, "Show Processed Step :", style=wx.ALIGN_CENTRE_VERTICAL)
        self.textdropdown.SetForegroundColour(wx.Colour(BLACK_WX)) 
        
        self.DDstepselection = wx.ComboBox(self.rightPanel,value ="", choices=[""], style=wx.CB_READONLY )

        self.Bind(wx.EVT_COMBOBOX, self.on_DDstepselection_select)        
        # self.DDstepselection =custom_wxwidgets.DropDown(self.rightPanel,items=["0-Initial state"],default="0-Initial state")
        # self.Bind(custom_wxwidgets.EVT_DROPDOWN, self.OnDropdownProcessingStep, self.DDstepselection)
        
        self.StepSelectionSizer.AddSpacer(16)
        self.StepSelectionSizer.Add(self.textdropdown, 0, wx.ALL | wx.EXPAND, 5)
        self.StepSelectionSizer.Add(self.DDstepselection, 0, wx.ALL | wx.EXPAND, 5)
        
   
        # bmp= wx.Bitmap("resources/throbber1.png", wx.BITMAP_TYPE_PNG)
        # bmp2= wx.Bitmap("resources/throbber2.png", wx.BITMAP_TYPE_PNG)
        # bmp3= wx.Bitmap("resources/throbber3.png", wx.BITMAP_TYPE_PNG)
        # bmp4= wx.Bitmap("resources/throbber4.png", wx.BITMAP_TYPE_PNG)


        # self.processing_throbber = throbber.Throbber(self.rightPanel,-1,[bmp,bmp2,bmp3,bmp4], size=(100, 100), style=wx.NO_BORDER)
        # self.processing_throbber.Hide()
        self.Processing_Sizer.Add(self.button_open_output_folder, 0, wx.ALL | wx.EXPAND, 5)
        self.Processing_Sizer.Add(self.button_toggle_save_raw, 0, wx.ALL | wx.EXPAND, 5)
        self.Processing_Sizer.Add(self.button_set_control, 0, wx.ALL | wx.EXPAND, 5)

        self.Processing_Sizer.Add(self.button_open_pipeline, 0, wx.ALL | wx.EXPAND, 5)
        self.Processing_Sizer.AddSpacer(20)

        self.Processing_Sizer.Add(self.StepSelectionSizer, 0, wx.ALL | wx.EXPAND, 5)
        
        
        self.player_Sizer.Add(self.button_step_processing, 0, wx.ALL | wx.EXPAND, 5)
        self.player_Sizer.Add(self.button_auto_processing, 0, wx.ALL | wx.EXPAND, 5)
        self.player_Sizer.Add(self.button_terminate_processing, 0, wx.ALL | wx.EXPAND, 5)
        # self.Processing_Sizer.Add(self.ProgressBar_Sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.player_Sizer.Add(self.ProgressBar_Sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        self.Processing_Sizer.Add(self.playerPanel, 0, wx.ALL | wx.EXPAND, 5)

        self.rightSizer.Add(self.Processing_Sizer, 0, wx.ALL | wx.EXPAND, 0)
        
        self.matplotlib_canvas = matplotlib_canvas.MatplotlibCanvas(self.rightPanel, wx.ID_ANY)
        self.infotext = wx.TextCtrl(self.consoleinfoSplitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        # self.infotext.SetFont(font1)
        font_fixed_width = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.infotext.SetFont(font_fixed_width)
        
        self.consoltext = wx.richtext.RichTextCtrl(self.consoleinfoSplitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        # self.infotext.SetFont(font1)

        self.Bind(wx.EVT_BUTTON, self.on_terminate_processing, self.button_terminate_processing)
        self.Bind(wx.EVT_BUTTON, self.on_autorun_processing, self.button_auto_processing)
        self.Bind(wx.EVT_BUTTON, self.on_open_output_folder, self.button_open_output_folder)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_save_raw, self.button_toggle_save_raw)
        self.Bind(wx.EVT_BUTTON, self.on_open_pipeline, self.button_open_pipeline)
        self.Bind(wx.EVT_BUTTON, self.on_set_control, self.button_set_control)
        self.Bind(wx.EVT_SIZE,self.OnResize)
        self.Bind(wx.EVT_BUTTON, self.on_button_step_processing, self.button_step_processing)

        self.rightSizer.Add(self.matplotlib_canvas, 1, wx.ALL | wx.EXPAND, 0)
        self.rightSizer.Add(self.matplotlib_canvas.toolbar, 0, wx.EXPAND, 0)
        self.rightSplitter.SplitHorizontally(self.rightPanel, self.consoleinfoSplitter, -150)
        self.rightSplitter.SetSashGravity(1.)
        self.consoleinfoSplitter.SplitVertically(self.consoltext, self.infotext, 0)
        self.consoleinfoSplitter.SetSashGravity(.5)
        self.mainSplitter.SplitVertically(self.leftPanel, self.rightSplitter, 300)
        self.SetBackgroundColour(wx.Colour(XISLAND1)) 

        self.Layout()

    def on_button_processing(self, event): # wxGlade: MyFrame.<event_handler>
        print("Event handler 'on_button_processing' not implemented!")
        event.Skip()

class PlotFrame(wx.Frame):
    def __init__(self, title):
        super().__init__(None)
        self.SetTitle(title)
        self.SetIcon(wx.Icon("resources/icon_32p.png"))
        self.SetBackgroundColour(wx.Colour(XISLAND1)) 
        self.SetSize((1200, 800))
        self.Show(True)

        self.splitter = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.panel = wx.Panel(self.splitter, wx.ID_ANY)
        self.canvas = matplotlib_canvas.MatplotlibCanvas(self.panel, wx.ID_ANY)
        self.text = wx.TextCtrl(self.splitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.text.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.NORMAL,wx.FONTWEIGHT_NORMAL, False))
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND, 0)
        self.sizer.Add(self.canvas.toolbar, 0, wx.EXPAND, 0)
        self.panel.SetSizer(self.sizer)
        
        self.splitter.SetMinimumPaneSize(200)
        self.splitter.SplitVertically(self.panel, self.text, -150)
        self.splitter.SetSashGravity(1.)

        self.Layout()