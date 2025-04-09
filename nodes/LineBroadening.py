import processing.api as api
import numpy as np

class LineBroadening(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Line Broadening",
            "author": "CIBM",
            "description": "Applies either exponential (Lorentzian) or Gaussian apodization."
        }
        self.parameters = [
            api.IntegerProp(
                idname="factor",
                default=5,
                min_val=1,
                max_val=50,
                fpb_label="Factor (Hz)"
            ),
            api.ChoiceProp(
                idname="apod_type",
                default="exponential",
                choices=["exponential", "gaussian"],
                fpb_label="Apodization Type"
            )
        ]
        super().__init__(nodegraph, id)
        self.plotSpectrum = False

    def process(self, data):
        apod_type = self.get_parameter("apod_type")
        factor = self.get_parameter("factor")
        time_axis = data["input"][0].time_axis() 

        if apod_type == "exponential":
            self.apod = np.exp(-time_axis * np.pi * factor)
        elif apod_type == "gaussian":
            self.apod = np.exp(
                - (np.pi * factor * time_axis)**2 / (4.0 * np.log(2))
            )

        output = []
        self.dmax = 0 
        for d in data["input"]:
            apodized_data = d * self.apod
            output.append(d.inherit(apodized_data))
            self.dmax = max(self.dmax, np.max(d))

        data["output"] = output

    """def plot(self, figure, data):
        figure.suptitle(self.__class__.__name__)
        ax = figure.add_subplot(2, 1, 1)
        for d in data["input"]:
            ax.plot(d.time_axis(), np.real(d), label="Input")
        ax.plot(data["input"][0].time_axis(), self.apod * self.dmax, ":k", label="Apod. Func.")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Intensity")
        ax.set_title("Input and Apodization Function")
        #ax.legend()
        ax = figure.add_subplot(2, 1, 2)
        for d in data["output"]:
            ax.plot(d.time_axis(), np.real(d), label="Output")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Intensity")
        ax.set_title("Apodized Output")
        figure.tight_layout()"""
    
    def plot(self, figure, data):
        figure.suptitle(self.__class__.__name__)
        
        # --- Change 1: Determine frequency axis limits using the ppm axis ---
        xlim = (
            np.max(data["input"][0].frequency_axis_ppm()),
            np.min(data["input"][0].frequency_axis_ppm())
        )
        
        # --- Change 2: Plot the input spectrum in the frequency domain ---
        ax = figure.add_subplot(2, 1, 1)
        for d in data["input"]:
            # Originally used d.time_axis() and np.real(d)
            # Now using d.frequency_axis_ppm() and np.real(d.spectrum())
            ax.plot(d.frequency_axis_ppm(), np.real(d.spectrum()), label="Input")
        ax.set_xlim(xlim)
        # --- Change 3: Adjust axis labels to reflect frequency domain (ppm) ---
        ax.set_xlabel("Chemical shift (ppm)")
        ax.set_ylabel("Intensity")
        ax.set_title("Input Spectrum")
        
        # --- Change 4: Plot the output (apodized) spectrum in the frequency domain ---
        ax2 = figure.add_subplot(2, 1, 2)
        for d in data["output"]:
            # Again use frequency-domain values
            ax2.plot(d.frequency_axis_ppm(), np.real(d.spectrum()), label="Output")
        ax2.set_xlim(xlim)
        ax2.set_xlabel("Chemical shift (ppm)")
        ax2.set_ylabel("Intensity")
        ax2.set_title("Line Broadened Spectrum")
        
        figure.tight_layout()

api.RegisterNode(LineBroadening, "LineBroadening")

"""class LineBroadening(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Line Broadening",
            "author": "CIBM",

            "description": "Shifts spectra in the frequency domain by factor * pi",
        }
        self.parameters = [
            api.IntegerProp(
                idname="factor",
                default=5,
                min_val=1,
                max_val=50,
                fpb_label="Factor"
            )
        ]
        super().__init__(nodegraph, id)
        self.plotSpectrum = False

    def process(self, data):
        self.exp = np.exp(-data["input"][0].time_axis() * np.pi * self.get_parameter("factor"))
        output = []
        self.dmax = 0
        for d in data["input"]:
            output.append(d.inherit(d * self.exp))
            self.dmax = max(self.dmax, np.max(d)) # for plotting exp
        data["output"] = output

    def plot(self, figure, data):
        figure.suptitle(self.__class__.__name__)
        ax = figure.add_subplot(2, 1, 1)
        for d in data["input"]:
            ax.plot(d.time_axis(), np.real(d))
        ax.plot(d.time_axis(), self.exp * self.dmax, ':k')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Intensity')
        ax.set_title("Input and apodisation function")
        ax = figure.add_subplot(2, 1, 2)
        for d in data["output"]:
            ax.plot(d.time_axis(), np.real(d))
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Intensity')
        ax.set_title("Output")
        figure.tight_layout()


api.RegisterNode(LineBroadening, "LineBroadening")"""
