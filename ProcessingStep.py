from suspect import MRSData
from matplotlib_canvas import MatplotlibCanvas

class ProcessingStep:
    def __init__(self, parameters = {}):
        self.parameters = parameters
        self.defaultParameters = parameters
        self.processedData: list[MRSData] = [] # might use a lot of memory
        self.exportNifti = False
        self.saveOutput = False
        self.plotSpectrum = False # set these if you don't override plot()
        self.plotPPM = False

    def __str__(self) -> str:
        output = self.__name__ + ":\n"
        if self.parameters:
            for key, value in self.parameters:
                output += "- " + key + ": " + value + "\n"
        return output
    
    def process(self, data: MRSData) -> list[MRSData]: # to override
        if self.saveOutput:
            self.processedData = data
        return data

    def resetParameters(self):
        self.parameters = self.defaultParameters
    
    def plot(self, canvas: MatplotlibCanvas): # can be overridden
        ax = canvas.figure.add_subplot(1, 1, 1) # create plot (necessary)
        if self.plotSpectrum:
            if self.plotPPM:
                for d in self.processedData:
                    ax.plot(d.frequency_axis_ppm(), d.spectrum())
                ax.set_xlabel('Frequency (ppm)')
            else:
                for d in self.processedData:
                    ax.plot(d.frequency_axis(), d.spectrum())
                ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Amplitude')
        else:
            for d in self.processedData:
                ax.plot(d.time_axis(), abs(d))
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Intensity')
        ax.set_title(self.__class__.__name__)
        canvas.draw() # draw plot (necessary)
        print("plotting done")