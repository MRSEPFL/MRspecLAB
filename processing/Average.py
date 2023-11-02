import ProcessingStep as ps
import numpy as np

class Average(ps.ProcessingStep):
    def __init__(self):
        super().__init__()
        self.plotSpectrum = False # use plot() from ProcessingStep.py

    def process(self, data):
        if len(data["input"]) == 1: return data["input"]
        return [data["input"][0].inherit(np.mean(data["input"], axis=0))] # retrieve metadata; we want a list of MRSData objects