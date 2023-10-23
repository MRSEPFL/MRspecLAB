from suspect import MRSData
from matplotlib_canvas import MatplotlibCanvas

class ProcessingStep:
    def __init__(self, parameters = {}):
        self.parameters = parameters
        self.defaultParameters = parameters
        self.inputData: list[MRSData] = [] # might use a lot of memory
        self.outputData: list[MRSData] = []
        self.saveInput = False # set these according to plotting needs
        self.saveOutput = False
        self.plotSpectrum = False # set these if you don't override plot()
        self.plotPPM = False
        # self.exportNifti = False

    def __str__(self) -> str:
        output = self.__name__ + ":\n"
        if self.parameters:
            for key, value in self.parameters:
                output += "- " + key + ": " + value + "\n"
        return output
    
    def _process(self, data: list[MRSData]) -> list[MRSData]: # handles saving output
        if self.saveInput: self.inputData = data
        output = self.process(data)
        if self.saveOutput: self.outputData = output
        return output
    
    def process(self, data: list[MRSData]) -> list[MRSData]: # to override
        return data
    
    def resetParameters(self):
        self.parameters = self.defaultParameters
    
    def plot(self, canvas: MatplotlibCanvas): # can be overridden
        if not (self.saveInput or self.saveOutput): return
        if not (self.saveInput or self.saveOutput):
            ax = canvas.figure.add_subplot(1, 1, 1)
            if self.saveInput:
                self.plotData(ax, self.inputData)
                canvas.figure.suptitle(self.__class__.__name__ + " (input)")
            else:
                self.plotData(ax, self.outputData)
                canvas.figure.suptitle(self.__class__.__name__ + " (output)")
        else:
            ax = canvas.figure.add_subplot(2, 1, 1)
            self.plotData(ax, self.inputData)
            ax = canvas.figure.add_subplot(2, 1, 2)
            self.plotData(ax, self.outputData)
            canvas.figure.suptitle(self.__class__.__name__)
        canvas.figure.tight_layout()
        canvas.draw()

    def plotData(self, ax, data):
        if self.plotSpectrum:
            if self.plotPPM:
                for d in data:
                    ax.plot(d.frequency_axis_ppm(), d.spectrum())
                ax.set_xlabel('Frequency (ppm)')
            else:
                for d in data:
                    ax.plot(d.frequency_axis(), d.spectrum())
                ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Amplitude')
        else:
            for d in data:
                ax.plot(d.time_axis(), abs(d))
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Intensity')