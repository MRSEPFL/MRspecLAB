# import matplotlib.pyplot as plt
# import wx

class ProcessingStep:
    def __init__(self, parameters = {}):
        self.parameters = parameters
        self.defaultParameters = parameters
        self.processedData = [] # might use a lot of memory
        self.plottedData = None
        self.exportNifti = False
        self.saveOutput = False

    def __str__(self):
        output = self.__name__ + ":\n"
        if self.parameters:
            for key, value in self.parameters:
                output += "- " + key + ": " + value + "\n"
        return output
    
    def process(self, data): # to overwrite
        if self.saveOutput:
            self.processedData = data
        return data

    def resetParameters(self):
        self.parameters = self.defaultParameters
    
    # plot to wx.panel
    # def plot(self, panel):
    #     self.plottedData = plt.figure()
    #     for spectrum in self.processedData:
    #         plt.plot(spectrum.wavelengths, spectrum.intensities)
    #     plt.show()