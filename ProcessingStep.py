from interface.matplotlib_canvas import MatplotlibCanvas
import numpy as np

class ProcessingStep:
    def __init__(self, parameters = {}):
        self.parameters = parameters
        self.defaultParameters = parameters
        self.plotSpectrum = False # set these if you don't override plot()
        self.plotPPM = False

    def __str__(self) -> str:
        output = self.__name__ + ":\n"
        if self.parameters:
            for key, value in self.parameters:
                output += "- " + key + ": " + value + "\n"
        return output
    
    def process(self, data: dict) -> None: # to override
        data["output"] = data["input"]
        data["wref"] = None # already was None
    
    def resetParameters(self):
        self.parameters = self.defaultParameters
    
    def plot(self, canvas: MatplotlibCanvas, data: dict) -> None: # can be overridden
        ax = canvas.figure.add_subplot(2, 1, 1)
        self.plotData(ax, data["input"])
        ax = canvas.figure.add_subplot(2, 1, 2)
        self.plotData(ax, data["output"])
        canvas.figure.suptitle(self.__class__.__name__)
        canvas.figure.tight_layout()
        canvas.draw()

    def plotData(self, ax, data): # helper for plotting time, freq or ppm
        if self.plotSpectrum:
            if self.plotPPM:
                for d in data:
                    ax.plot(d.frequency_axis_ppm(), d.spectrum())
                ax.set_xlabel('Chemical shift (ppm)')
                ax.set_xlim((np.max(d.frequency_axis_ppm()), np.min(d.frequency_axis_ppm())))
            else:
                for d in data:
                    ax.plot(d.frequency_axis(), d.spectrum())
                ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Amplitude')
        else:
            for d in data:
                ax.plot(d.time_axis(), d)
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Intensity')