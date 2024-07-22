import wx
import wx.richtext
from .plot_canvas import MatplotlibCanvas
from .file_panel import FilePanel
from interface.colours import(BLACK_WX,XISLAND1,XISLAND2)
from resources import folder_img, pipeline_img

class ButtonNoBorder(wx.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnHover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnUnHover)
        self.SetWindowStyleFlag(wx.BORDER_NONE)

    def OnHover(self, event):
        self.SetWindowStyleFlag(wx.BORDER_SUNKEN)
        event.Skip()
        
    def OnUnHover(self, event):
        self.SetWindowStyleFlag(wx.BORDER_NONE)
        event.Skip()

class ToggleButtonNoBorder(wx.ToggleButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnHover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnUnHover)
        self.SetWindowStyleFlag(wx.BORDER_NONE)

    def OnHover(self, event):
        self.SetWindowStyleFlag(wx.BORDER_SUNKEN)
        event.Skip()
        
    def OnUnHover(self, event):
        self.SetWindowStyleFlag(wx.BORDER_NONE)
        event.Skip()

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

        main_splitter = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        right_splitter = wx.SplitterWindow(main_splitter, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        text_splitter = wx.SplitterWindow(right_splitter, wx.ID_ANY, style=wx.SP_3D | wx.SP_LIVE_UPDATE)

        main_splitter.SetMinimumPaneSize(100)
        right_splitter.SetMinimumPaneSize(100)

        self.left_panel = wx.Panel(main_splitter, wx.ID_ANY)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.left_panel.SetSizer(left_sizer)
        self.right_panel = wx.Panel(right_splitter, wx.ID_ANY)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.right_panel.SetSizer(right_sizer)

        self.MRSfiles = FilePanel(self.left_panel)
        self.MRSfiles.SetFont(font1)
        self.MRSfiles.label.SetLabel("Import MRS files here")
        self.MRSfiles.Layout()

        self.Waterfiles = FilePanel(self.left_panel)
        self.Waterfiles.SetFont(font1)
        self.Waterfiles.label.SetLabel("Import water reference file here (optional)")
        self.Waterfiles.list.SetMaxSize((-1, 50))
        self.Waterfiles.Layout()

        left_sizer.Add(self.MRSfiles, 1, wx.ALL | wx.EXPAND, 5)
        left_sizer.AddSpacer(20)
        left_sizer.Add(self.Waterfiles, 1, wx.ALL | wx.EXPAND, 5)
        
        ### WINDOW BUTTONS ###
        folder_bmp = folder_img.getBitmap().ConvertToImage().Rescale(50, 50).ConvertToBitmap()
        self.folder_button = BtmButtonNoBorder(self.right_panel, wx.ID_ANY, folder_bmp)
        self.folder_button.SetBackgroundColour(wx.Colour(XISLAND1))
        self.folder_button.SetMinSize((50, 50))
        self.folder_button.SetToolTip("Open output folder")

        pipeline_bmp = pipeline_img.getBitmap().ConvertToImage().Rescale(50, 50).ConvertToBitmap()
        self.pipeline_button = BtmButtonNoBorder(self.right_panel, wx.ID_ANY, pipeline_bmp)
        self.pipeline_button.SetBackgroundColour(wx.Colour(XISLAND1))
        self.pipeline_button.SetMinSize((50, 50))
        self.pipeline_button.SetToolTip("Open pipeline editor")
        
        bmp_sizer = wx.BoxSizer(wx.VERTICAL)
        bmp_sizer.Add(self.folder_button, 0, wx.ALL | wx.EXPAND, 2)
        bmp_sizer.Add(self.pipeline_button, 0, wx.ALL | wx.EXPAND, 2)

        # bmp_logo=wx.Bitmap("resources/logobig.png", wx.BITMAP_TYPE_PNG)
        # self.logo_image=wx.StaticBitmap(self.rightPanel, wx.ID_ANY, bitmap=bmp_logo)

        ### PLOT BUTTONS ###
        self.save_plots_button = wx.CheckBox(self.right_panel, wx.ID_ANY, "Save plots")
        self.save_plots_button.SetValue(True)
        self.save_plots_button.SetMinSize((-1, 25))
        self.save_plots_button.SetToolTip("Enable/Disable saving plots in the output folder")

        self.save_raw_button = wx.CheckBox(self.right_panel, wx.ID_ANY, "Save .raw files")
        self.save_raw_button.SetValue(False)
        self.save_raw_button.SetMinSize((-1, 25))
        self.save_raw_button.SetToolTip("Enable/Disable saving raw data in the output folder")
        
        plot_label =  wx.StaticText(self.right_panel, wx.ID_ANY, "Show plot of node:", style=wx.ALIGN_CENTRE_VERTICAL)
        plot_label.SetForegroundColour(wx.Colour(BLACK_WX))
        plot_label.SetMinSize((-1, 25))

        self.plot_box = wx.ComboBox(self.right_panel, value="", choices=[""], style=wx.CB_READONLY)
        self.plot_box.SetMinSize((150, 25))

        plot_sizer = wx.BoxSizer(wx.VERTICAL)
        plot_sizer.Add(self.save_plots_button, 0, wx.ALL | wx.EXPAND, 0)
        plot_sizer.Add(self.save_raw_button, 0, wx.ALL | wx.EXPAND, 0)
        plot_sizer.Add(plot_label, 0, wx.ALL | wx.EXPAND, 0)
        plot_sizer.Add(self.plot_box, 0, wx.ALL | wx.EXPAND, 0)

        ### CONFIG BUTTONS ###
        self.config_button = ToggleButtonNoBorder(self.right_panel, wx.ID_ANY, "Show fitting options", style=wx.BORDER_NONE | wx.BU_LEFT)
        self.config_button.SetBackgroundColour(wx.Colour(XISLAND1))
        self.config_button.SetValue(False)
        self.config_button.SetMinSize((-1, 25))
        self.config_button.SetToolTip("Show fitting options for LCModel")

        self.basis_button = ButtonNoBorder(self.right_panel, wx.ID_ANY, "Set .basis file", style=wx.BORDER_NONE | wx.BU_LEFT)
        self.basis_button.SetBackgroundColour(wx.Colour(XISLAND2))
        self.basis_button.SetMinSize((-1, 25))
        self.basis_button.SetToolTip("Override basis set detection for LCModel")

        self.control_button = ButtonNoBorder(self.right_panel, wx.ID_ANY, "Set .control file", style=wx.BORDER_NONE | wx.BU_LEFT)
        self.control_button.SetBackgroundColour(wx.Colour(XISLAND2))
        self.control_button.SetMinSize((-1, 25))
        self.control_button.SetToolTip("Override default control file from LCModel")

        self.segmentation_button = ButtonNoBorder(self.right_panel, wx.ID_ANY, "Set segmentation file", style=wx.BORDER_NONE | wx.BU_LEFT)
        self.segmentation_button.SetBackgroundColour(wx.Colour(XISLAND2))
        self.segmentation_button.SetMinSize((-1, 25))
        self.segmentation_button.SetToolTip("Override segmentation file for LCModel")

        config_sizer = wx.BoxSizer(wx.VERTICAL)
        config_sizer.Add(self.config_button, 0, wx.ALL | wx.EXPAND, 0)
        config_sizer.Add(self.basis_button, 0, wx.ALL | wx.EXPAND, 0)
        config_sizer.Add(self.control_button, 0, wx.ALL | wx.EXPAND, 0)
        config_sizer.Add(self.segmentation_button, 0, wx.ALL | wx.EXPAND, 0)

        ### PLAYER BUTTONS ###
        self.player_panel = wx.Panel(self.right_panel, wx.ID_ANY)
        self.player_panel.SetBackgroundColour(wx.Colour(XISLAND2)) 
        player_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.player_panel.SetSizer(player_sizer)
        
        self.bmp_steppro = wx.Bitmap("resources/run.png", wx.BITMAP_TYPE_PNG)  
        self.bmp_steppro_greyed= wx.Bitmap("resources/run_greyed.png", wx.BITMAP_TYPE_PNG) 
        self.button_step_processing = BtmButtonNoBorder(self.player_panel, wx.ID_ANY, self.bmp_steppro)
        self.button_step_processing.SetBackgroundColour(wx.Colour(XISLAND2))
        self.button_step_processing.SetMinSize((-1, 100))
        self.button_step_processing.SetToolTip("Run next step of the pipeline \nand show its results plot") 
        
        self.bmp_autopro = wx.Bitmap("resources/autorun.png", wx.BITMAP_TYPE_PNG)
        self.bmp_autopro_greyed = wx.Bitmap("resources/autorun_greyed.png", wx.BITMAP_TYPE_PNG)
        self.bmp_pause = wx.Bitmap("resources/pause.png", wx.BITMAP_TYPE_PNG) 
        self.button_auto_processing = BtmButtonNoBorder(self.player_panel, wx.ID_ANY, self.bmp_autopro)
        self.button_auto_processing.SetBackgroundColour(wx.Colour(XISLAND2))
        self.button_auto_processing.SetMinSize((-1, 100))
        self.button_auto_processing.SetToolTip("Run all the steps after one another until desactivation, \nshow only plot of the last step processed") 

        self.bmp_terminate = wx.Bitmap("resources/terminate.png", wx.BITMAP_TYPE_PNG)
        self.bmp_terminate_greyed = wx.Bitmap("resources/terminate_greyed.png", wx.BITMAP_TYPE_PNG)
        self.button_terminate_processing = BtmButtonNoBorder(self.player_panel, wx.ID_ANY, self.bmp_terminate)
        self.button_terminate_processing.SetBackgroundColour(wx.Colour(XISLAND2))
        self.button_terminate_processing.SetMinSize((-1, 100))
        self.button_terminate_processing.SetToolTip("Reset processing of the current pipeline")
        self.button_terminate_processing.Disable()

        player_sizer.Add(self.button_step_processing, 0, wx.ALL | wx.EXPAND, 5)
        player_sizer.Add(self.button_auto_processing, 0, wx.ALL | wx.EXPAND, 5)
        player_sizer.Add(self.button_terminate_processing, 0, wx.ALL | wx.EXPAND, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(bmp_sizer, 0, wx.ALL | wx.EXPAND, 0)
        button_sizer.Add(wx.StaticLine(self.right_panel, wx.ID_ANY, style=wx.LI_VERTICAL), 0, wx.ALL | wx.EXPAND, 5)
        button_sizer.Add(plot_sizer, 0, wx.ALL | wx.EXPAND, 0)
        button_sizer.Add(wx.StaticLine(self.right_panel, wx.ID_ANY, style=wx.LI_VERTICAL), 0, wx.ALL | wx.EXPAND, 5)
        button_sizer.Add(config_sizer, 0, wx.ALL | wx.EXPAND, 0)
        button_sizer.AddStretchSpacer(1)
        button_sizer.Add(self.player_panel, 0, wx.ALL | wx.EXPAND, 0)
        right_sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 0)
        
        self.matplotlib_canvas = MatplotlibCanvas(self.right_panel, wx.ID_ANY)
        self.info_text = wx.richtext.RichTextCtrl(text_splitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.file_text = wx.TextCtrl(text_splitter, wx.ID_ANY, "", style=wx.TE_READONLY | wx.TE_MULTILINE)
        font_fixed_width = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.file_text.SetFont(font_fixed_width)

        right_sizer.Add(self.matplotlib_canvas, 1, wx.ALL | wx.EXPAND, 0)
        right_sizer.Add(self.matplotlib_canvas.toolbar, 0, wx.EXPAND, 0)
        right_splitter.SplitHorizontally(self.right_panel, text_splitter, -150)
        right_splitter.SetSashGravity(1.)
        text_splitter.SplitVertically(self.info_text, self.file_text, 0)
        text_splitter.SetSashGravity(.5)
        main_splitter.SplitVertically(self.left_panel, right_splitter, 300)
        self.SetBackgroundColour(wx.Colour(XISLAND1)) 

        self.Layout()