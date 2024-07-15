import wx
import wx.richtext
from .plot_canvas import MatplotlibCanvas
from .file_panel import FilePanel
from interface.colours import(BLACK_WX,XISLAND1,XISLAND2)

class BtmButtonNoBorder(wx.BitmapButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnHover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnUnHover)
        self.SetWindowStyleFlag(wx.NO_BORDER)

    def OnHover(self, event):
        self.SetWindowStyleFlag(wx.BORDER_SUNKEN)
        event.Skip()
        
    def OnUnHover(self, event):
        self.SetWindowStyleFlag(wx.NO_BORDER)
        event.Skip()

class LayoutFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        font1 = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.NORMAL,wx.FONTWEIGHT_NORMAL, False)
        self.SetSize((1200, 800))
        self.SetTitle("MRSprocessing")

        self.mainSplitter = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.rightSplitter = wx.SplitterWindow(self.mainSplitter, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.consoleinfoSplitter = wx.SplitterWindow(self.rightSplitter, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)

        self.mainSplitter.SetMinimumPaneSize(100)
        self.rightSplitter.SetMinimumPaneSize(100)

        self.leftPanel = wx.Panel(self.mainSplitter, wx.ID_ANY)
        self.leftSizer = wx.BoxSizer(wx.VERTICAL)
        self.leftPanel.SetSizer(self.leftSizer)
        self.rightPanel = wx.Panel(self.rightSplitter, wx.ID_ANY)
        self.rightSizer = wx.BoxSizer(wx.VERTICAL)
        self.rightPanel.SetSizer(self.rightSizer)

        self.MRSfiles = FilePanel(self.leftPanel)
        self.MRSfiles.SetFont(font1)
        self.MRSfiles.label.SetLabel("Import MRS files here")
        self.MRSfiles.Layout()

        self.Waterfiles = FilePanel(self.leftPanel)
        self.Waterfiles.SetFont(font1)
        self.Waterfiles.label.SetLabel("Import water reference here (optional)")
        self.Waterfiles.Layout()

        self.leftSizer.Add(self.MRSfiles, 1, wx.ALL | wx.EXPAND, 5)
        self.leftSizer.AddSpacer(20)
        self.leftSizer.Add(self.Waterfiles, 1, wx.ALL | wx.EXPAND, 5)
        
        ### RIGHT PANEL ###
        self.Processing_Sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.playerPanel = wx.Panel(self.rightPanel, wx.ID_ANY)
        self.playerPanel.SetBackgroundColour(wx.Colour(XISLAND2)) 
        self.player_Sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.playerPanel.SetSizer(self.player_Sizer)
        
        self.bmp_steppro = wx.Bitmap("resources/run.png", wx.BITMAP_TYPE_PNG)  
        self.bmp_steppro_greyed= wx.Bitmap("resources/run_greyed.png", wx.BITMAP_TYPE_PNG) 
        self.button_step_processing = BtmButtonNoBorder(self.playerPanel, wx.ID_ANY, self.bmp_steppro)
        self.button_step_processing.SetBackgroundColour(wx.Colour(XISLAND2))  # Set the background color (RGB values)
        self.button_step_processing.SetMinSize((-1, 100))
        self.button_step_processing.SetToolTip("Run next step of the pipeline \nand show its results plot") 
        
        self.bmp_autopro = wx.Bitmap("resources/autorun.png", wx.BITMAP_TYPE_PNG)  # Replace with your image path
        self.bmp_autopro_greyed = wx.Bitmap("resources/autorun_greyed.png", wx.BITMAP_TYPE_PNG)  # Replace with your image path
        self.bmp_pause = wx.Bitmap("resources/pause.png", wx.BITMAP_TYPE_PNG) 

        self.button_auto_processing = BtmButtonNoBorder(self.playerPanel, wx.ID_ANY, self.bmp_autopro)
        self.button_auto_processing.SetBackgroundColour(wx.Colour(XISLAND2))  # Set the background color (RGB values)
        self.button_auto_processing.SetMinSize((-1, 100))
        self.button_auto_processing.SetToolTip("Run all the steps after one another until desactivation, \nshow only plot of the last step processed") 

        
        self.bmp_terminate = wx.Bitmap("resources/terminate.png", wx.BITMAP_TYPE_PNG)
        self.bmp_terminate_greyed = wx.Bitmap("resources/terminate_greyed.png", wx.BITMAP_TYPE_PNG)  # Replace with your image path
        self.button_terminate_processing = BtmButtonNoBorder(self.playerPanel, wx.ID_ANY, self.bmp_terminate)
        self.button_terminate_processing.SetBackgroundColour(wx.Colour(XISLAND2))  # Set the background color (RGB values)
        self.button_terminate_processing.SetMinSize((-1, 100))
        self.button_terminate_processing.Disable()

        bmp_folder = wx.Bitmap("resources/open_folder.png", wx.BITMAP_TYPE_PNG)
        # bmp_folder.SetSize((100, 100))
        # bmp_folder.SetScaleFactor(8)
        self.button_open_output_folder = BtmButtonNoBorder(self.rightPanel, wx.ID_ANY, bmp_folder)
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
        self.button_set_control = BtmButtonNoBorder(self.rightPanel, wx.ID_ANY, bmp_control)
        self.button_set_control.SetBackgroundColour(wx.Colour(XISLAND1))  # Set the background color (RGB values)
        self.button_set_control.SetMinSize((-1, 100))
        self.button_set_control.SetToolTip("Open control file in an editor of the \nto be able to modify it and load it\nas wanted") 


        self.bmp_pipeline= wx.Bitmap("resources/Open_Pipeline.png", wx.BITMAP_TYPE_PNG)
        self.button_open_pipeline = BtmButtonNoBorder(self.rightPanel, wx.ID_ANY, self.bmp_pipeline)
        self.button_open_pipeline.SetBackgroundColour(wx.Colour(XISLAND1))  # Set the background color (RGB values)
        self.button_open_pipeline.SetMinSize((-1, 100))
        self.button_open_pipeline.SetToolTip("Open editor of the \npipeline to modify it") 
        
        # bmp_logo=wx.Bitmap("resources/logobig.png", wx.BITMAP_TYPE_PNG)
        # self.logo_image=wx.StaticBitmap(self.rightPanel, wx.ID_ANY, bitmap=bmp_logo)
             
        self.StepSelectionSizer= wx.BoxSizer(wx.VERTICAL)
        
        self.textdropdown =  wx.StaticText(self.rightPanel, wx.ID_ANY, "Show Processed Step :", style=wx.ALIGN_CENTRE_VERTICAL)
        self.textdropdown.SetForegroundColour(wx.Colour(BLACK_WX)) 
        
        self.DDstepselection = wx.ComboBox(self.rightPanel,value ="", choices=[""], style=wx.CB_READONLY )

        self.Bind(wx.EVT_COMBOBOX, self.on_DDstepselection_select)
        
        self.StepSelectionSizer.AddSpacer(16)
        self.StepSelectionSizer.Add(self.textdropdown, 0, wx.ALL | wx.EXPAND, 5)
        self.StepSelectionSizer.Add(self.DDstepselection, 0, wx.ALL | wx.EXPAND, 5)

        self.Processing_Sizer.Add(self.button_open_output_folder, 0, wx.ALL | wx.EXPAND, 5)
        self.Processing_Sizer.Add(self.button_toggle_save_raw, 0, wx.ALL | wx.EXPAND, 5)
        self.Processing_Sizer.Add(self.button_set_control, 0, wx.ALL | wx.EXPAND, 5)
        self.Processing_Sizer.Add(self.button_open_pipeline, 0, wx.ALL | wx.EXPAND, 5)
        self.Processing_Sizer.AddSpacer(20)
        self.Processing_Sizer.Add(self.StepSelectionSizer, 0, wx.ALL | wx.EXPAND, 5)
        
        self.player_Sizer.Add(self.button_step_processing, 0, wx.ALL | wx.EXPAND, 5)
        self.player_Sizer.Add(self.button_auto_processing, 0, wx.ALL | wx.EXPAND, 5)
        self.player_Sizer.Add(self.button_terminate_processing, 0, wx.ALL | wx.EXPAND, 5)
        
        self.Processing_Sizer.Add(self.playerPanel, 0, wx.ALL | wx.EXPAND, 5)

        self.rightSizer.Add(self.Processing_Sizer, 0, wx.ALL | wx.EXPAND, 0)
        
        self.matplotlib_canvas = MatplotlibCanvas(self.rightPanel, wx.ID_ANY)
        self.infotext = wx.TextCtrl(self.consoleinfoSplitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        # self.infotext.SetFont(font1)
        font_fixed_width = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.infotext.SetFont(font_fixed_width)
        
        self.consoltext = wx.richtext.RichTextCtrl(self.consoleinfoSplitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        # self.infotext.SetFont(font1)

        self.Bind(wx.EVT_BUTTON, self.reset, self.button_terminate_processing)
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