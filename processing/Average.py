import ProcessingStep as ps
import numpy as np

class Average(ps.ProcessingStep):
    def __init__(self):
        super().__init__()
        self.plotSpectrum = False # use plot() from ProcessingStep.py

    def process(self, data):
        if len(data) == 1: return data
        output = np.mean(data, axis=0)
        output = data[0].inherit(output) # retrieve suspect metadata
        return [output] # return a list of MRSData objects