import wx
#https://rodolfotech.blogspot.com/2015/04/wxpython-double-slider-widget-to-enter.html
class RangeSlider(wx.Panel):

    def __init__(self, parent,min_value_range,max_value_range,initial_min_value,initial_max_value,step_value):
        #min_value_range,max_value_range,initial_min_valueinitial_max_value divided by step_value has to be an integer
        super(RangeSlider, self).__init__(parent, wx.ID_ANY)
        ##Wxpythonslider can't have decimal steps so we divide by the incremental steps
        self.step_value=step_value
        self.min_value_range=min_value_range
        self.max_value_range=max_value_range
        sizer = wx.FlexGridSizer(rows=2, cols=3, vgap=5, hgap=5)
        self.sldMax = wx.Slider(self, value=int(initial_max_value/step_value), minValue=int(min_value_range/step_value),
            maxValue=int(max_value_range/step_value),
            style=wx.SL_HORIZONTAL)
        self.sldMin = wx.Slider(self, value=int(initial_min_value/step_value), minValue=int(min_value_range/step_value),
            maxValue=int(max_value_range/step_value),
            style=wx.SL_HORIZONTAL)
        
        self.param_min= initial_min_value
        self.param_max=initial_max_value

        self.sldMax.Bind(wx.EVT_SCROLL, self.OnSliderScroll)
        self.sldMin.Bind(wx.EVT_SCROLL, self.OnSliderScroll2)
        
        self.txtMax = wx.TextCtrl(self, value=str(initial_max_value), style=wx.TE_PROCESS_ENTER)
        self.txtMin = wx.TextCtrl(self, value=str(initial_min_value), style=wx.TE_PROCESS_ENTER)
        


        lab1 = wx.StaticText(self, label="Min "+ str(min_value_range))
        lab2 = wx.StaticText(self, label="Max " + str(max_value_range))

        sizer.Add(lab1, 0, wx.LEFT, 10)
        sizer.Add(self.sldMax, 1, wx.EXPAND)
        sizer.Add(lab2, 0, wx.RIGHT, 10)
        sizer.Add(self.txtMin, 0, wx.ALIGN_CENTER)
        sizer.Add(self.sldMin, 1, wx.EXPAND)
        sizer.Add(self.txtMax, 0, wx.ALIGN_CENTER)
        sizer.AddGrowableCol(1, 1)
        
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEnterMin, self.txtMin)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEnterMax, self.txtMax)


        self.SetSizer(sizer)

    def OnSliderScroll(self, e):
        self.param_max = self.sldMax.GetValue()*self.step_value
        self.param_min = self.sldMin.GetValue()*self.step_value
        if self.param_min > self.param_max:
            self.sldMin.SetValue(int(self.param_max/self.step_value))
            self.txtMin.SetLabel(str(round(self.param_max,len(str(self.step_value).split('.')[1]) if '.' in str(self.step_value) else 0)))
        self.txtMax.SetLabel(str(round(self.param_max,len(str(self.step_value).split('.')[1]) if '.' in str(self.step_value) else 0)))


    def OnSliderScroll2(self, e):
        self.param_min  = self.sldMin.GetValue()*self.step_value
        self.param_max = self.sldMax.GetValue()*self.step_value
        if self.param_max < self.param_min:
            self.sldMax.SetValue(int(self.param_min/self.step_value))
            self.txtMax.SetLabel(str(round(self.param_min,len(str(self.step_value).split('.')[1]) if '.' in str(self.step_value) else 0)))
        self.txtMin.SetLabel(str(round(self.param_min,len(str(self.step_value).split('.')[1]) if '.' in str(self.step_value) else 0)))
        
    def OnTextEnterMin(self, event):

        self.param_min = round(float(self.txtMin.GetValue()),len(str(self.step_value).split('.')[1]) if '.' in str(self.step_value) else 0)
        
        self.param_min = max(self.min_value_range, min(self.max_value_range, self.param_min))  # Ensure value is between 0 and 100
        self.txtMin.SetValue(str(self.param_min))
        self.sldMin.SetValue(int(self.param_min/self.step_value))
        if self.param_max < self.param_min:
            self.sldMax.SetValue(int(self.param_min/self.step_value))
            self.txtMax.SetLabel(str(round(self.param_min,len(str(self.step_value).split('.')[1]) if '.' in str(self.step_value) else 0)))
        self.txtMin.SetLabel(str(round(self.param_min,len(str(self.step_value).split('.')[1]) if '.' in str(self.step_value) else 0)))
        
    def OnTextEnterMax(self, event):

        self.param_max = round(float(self.txtMax.GetValue()),len(str(self.step_value).split('.')[1]) if '.' in str(self.step_value) else 0)
        
        self.param_max = max(self.min_value_range, min(self.max_value_range, self.param_max))  # Ensure value is between 0 and 100
        self.txtMax.SetValue(str(self.param_max))
        self.sldMax.SetValue(int(self.param_max/self.step_value))
        if self.param_min > self.param_max:
            self.sldMin.SetValue(int(self.param_max/self.step_value))
            self.txtMin.SetLabel(str(round(self.param_max,len(str(self.step_value).split('.')[1]) if '.' in str(self.step_value) else 0)))
        self.txtMax.SetLabel(str(round(self.param_max,len(str(self.step_value).split('.')[1]) if '.' in str(self.step_value) else 0)))


class NumericalParameterPanel(wx.Panel):
    def __init__(self, parent, name, value_name, initial_value,min_value,max_value,step_value=1.0,unit_name=""):
        #name: name of the parameter that will be displayed
        #value_name: name of the parameter in the backend
        #initial_value: default value of the parameter
        #min_value: minimum value of the parameter
        #max_value: maximum value of the parameter
        # step_value: incremental step of the slider

        self.min_value=min_value
        self.max_value=max_value
        #unit_name: string of the name of the unit of the parameter(e.g. [Hz])
        super().__init__(parent)
        
        # Create a vertical sizer for each parameter
        parameter_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create a static text for the parameter name
        parameter_name_label = wx.StaticText(self, label=name, style=wx.ALIGN_LEFT)
        parameter_sizer.Add(parameter_name_label, 0, wx.EXPAND | wx.ALL, 5)
        
        # Create a horizontal sizer for the value control
        value_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Create a TextControl to display and edit the parameter value
        self.value_textctrl = wx.TextCtrl(self, value=str(initial_value), style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEnter, self.value_textctrl)
        value_sizer.Add(self.value_textctrl, 1, wx.EXPAND | wx.ALL, 5)
        
        # Create a static text for "[un]"
        value_sizer.Add(wx.StaticText(self, label=unit_name, style=wx.ALIGN_LEFT), 0, wx.EXPAND | wx.ALL, 5)
        
        # Create a vertical spacer
        value_sizer.AddSpacer(20)
        
        # Create a slider to control the parameter value
        self.slider = wx.Slider(self, minValue=min_value, maxValue=max_value, value=initial_value)
        self.slider.SetTickFreq(step_value)  # Set the tick frequency to control the step

        self.Bind(wx.EVT_SLIDER, self.OnSliderChange, self.slider)
        value_sizer.Add(self.slider, 1, wx.EXPAND | wx.ALL, 5)
        
        parameter_sizer.Add(value_sizer, 0, wx.EXPAND)
        
        # Create a horizontal spacer
        parameter_sizer.AddSpacer(10)
        
        self.SetSizerAndFit(parameter_sizer)
        


    def OnTextEnter(self, event):
        value = int(self.value_textctrl.GetValue())
        value = max(self.min_value,  min(self.max_value, value))  #ensure the value entered is in the correct range
        self.value_textctrl.SetValue(str(value))
        self.slider.SetValue(value)

    def OnSliderChange(self, event):
        value = self.slider.GetValue()
        self.value_textctrl.SetValue(str(value))

class BoolParameterPanel(wx.Panel):
    def __init__(self, parent, name, label_button, default_active=False):
        super().__init__(parent)

        parameter_sizer = wx.BoxSizer(wx.VERTICAL)

        parameter_name_label = wx.StaticText(self, label=name, style=wx.ALIGN_LEFT)
        parameter_sizer.Add(parameter_name_label, 0, wx.EXPAND | wx.ALL, 5)

        value_sizer = wx.BoxSizer(wx.HORIZONTAL)


        self.parameter_active_button = wx.ToggleButton(self, label=label_button)
        self.parameter_active_button.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggleParameterActive)
        self.parameter_active_button.SetValue(default_active)
        self.parameter_active_button.SetMinSize((100, 40))
        self.parameter_active_button.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        
        value_sizer.Add(self.parameter_active_button, 1, wx.EXPAND | wx.ALL, 5)

        
        parameter_sizer.Add(value_sizer, 1, wx.EXPAND)
        parameter_sizer.AddSpacer(10)

        self.SetSizerAndFit(parameter_sizer)

    def OnToggleParameterActive(self, event):
        # You can use self.parameter_active_button.GetValue() to get the state (True or False)
        parameter_active = self.parameter_active_button.GetValue()
        print("toggle active")
        

class ChoiceParameterPanel(wx.Panel):
    def __init__(self, parent, name, choices, default_index=0):
        super().__init__(parent)

        parameter_sizer = wx.BoxSizer(wx.VERTICAL)

        value_sizer = wx.BoxSizer(wx.HORIZONTAL)

        parameter_name_label = wx.StaticText(self, label=name, style=wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)
        value_sizer.Add(parameter_name_label, 0, wx.EXPAND | wx.ALL, 5)


        self.parameter_choice = wx.Choice(self, choices=choices)
        self.parameter_choice.SetSelection(default_index)
        self.parameter_choice.SetMinSize((100, 30))
        self.parameter_choice.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        value_sizer.Add(self.parameter_choice, 1, wx.EXPAND | wx.ALL, 5)

        parameter_sizer.Add(value_sizer, 1, wx.EXPAND)
        parameter_sizer.AddSpacer(10)

        self.SetSizerAndFit(parameter_sizer)
        
        self.parameter_choice.Bind(wx.EVT_CHOICE, self.on_choice)

    def on_choice(self, event):
        selected_index = self.parameter_choice.GetSelection()
        selected_value = self.parameter_choice.GetString(selected_index)
        print(f"Choice selected: {selected_value} (index {selected_index})")



class SpinDoubleValueParameterPanel(wx.Panel):
    def __init__(self, parent, name, initial_value,min_value,max_value,step_value=0.1):
        super().__init__(parent)

        parameter_sizer = wx.BoxSizer(wx.VERTICAL)

        value_sizer = wx.BoxSizer(wx.HORIZONTAL)

        parameter_name_label = wx.StaticText(self, label=name, style=wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM)
        value_sizer.Add(parameter_name_label, 0, wx.EXPAND | wx.ALL, 5)

        # Replace wx.Choice with wx.SpinControlDouble
        self.parameter_spin = wx.SpinCtrlDouble(self, initial=initial_value, min=min_value, max=max_value)
        self.parameter_spin.SetDigits(len(str(step_value).split('.')[1]) if '.' in str(step_value) else 0)  # Adjust the number of decimal places if needed
        self.parameter_spin.SetIncrement(step_value)  # Set the increment step if needed
        self.parameter_spin.SetMinSize((100, 30))
        self.parameter_spin.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        value_sizer.Add(self.parameter_spin, 1, wx.EXPAND | wx.ALL, 5)

        parameter_sizer.Add(value_sizer, 1, wx.EXPAND)
        parameter_sizer.AddSpacer(10)

        self.SetSizerAndFit(parameter_sizer)
        
        self.parameter_spin.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_spin)

    def on_spin(self, event):
        selected_value = self.parameter_spin.GetValue()
        selected_index = int(selected_value)  # Convert the double value to an integer index
        print(f"Choice selected: {selected_value} (index {selected_index})")


class RangeParameterPanel(wx.Panel):
    def __init__(self, parent, name):
        super().__init__(parent)

        parameter_sizer = wx.BoxSizer(wx.VERTICAL)

        parameter_name_label = wx.StaticText(self, label=name, style=wx.ALIGN_LEFT)
        parameter_sizer.Add(parameter_name_label, 0, wx.EXPAND | wx.ALL, 5)

        # Create an instance of the RangeSlider class
        range_slider = RangeSlider(self, 0, 20, 2, 15, 0.1)
        parameter_sizer.Add(range_slider, 0, wx.EXPAND | wx.ALL, 5)  # Add the RangeSlider to the sizer

        self.SetSizerAndFit(parameter_sizer)
        
class CustomPanel(wx.Panel):
    def __init__(self, parent, panel_name, parameter_classes):
        super(CustomPanel, self).__init__(parent)

        # Create a vertical sizer for the parameters
        parameter_sizer = wx.BoxSizer(wx.VERTICAL)

        parameter_label = wx.StaticText(self, label=panel_name)
        font = parameter_label.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        parameter_label.SetFont(font)
        parameter_label.SetWindowStyleFlag(wx.ALIGN_CENTER_HORIZONTAL)

        # Add the StaticText widget to the first slot
        parameter_sizer.Add(parameter_label, 0, wx.EXPAND | wx.ALL, 10)

        # Add a spacer to the second slot
        parameter_sizer.AddSpacer(10)

        # Create parameter panels based on the provided classes and arguments
        for param_class, *args in parameter_classes:
            parameter_panel = param_class(self, *args)
            parameter_sizer.Add(parameter_panel, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(parameter_sizer)
        
    