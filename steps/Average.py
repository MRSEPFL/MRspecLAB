from processing.ProcessingStep import ProcessingStep
import gs.api as api
import numpy as np

class Average(ProcessingStep):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Averaging",
            "author": "CIBM",
            "version": (0, 0, 0),
            "category": "QUALITY CONTROL",
            "description": "Averages all input spectra into one"
        }
        super().__init__(nodegraph, id)
        self.plotSpectrum = False # use plot() from ProcessingStep.py

    def process(self, data):
        if len(data["input"]) == 1:
            data["output"] = data["input"]
            return
        data["output"] = [ data["input"][0].inherit(np.mean(data["input"], axis=0)) ] # retrieve metadata; we want a list of MRSData objects

api.RegisterNode(Average, "Average")