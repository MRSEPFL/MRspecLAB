import processing.api as api
import numpy as np

class Average(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Averaging",
            "author": "CIBM",
            "description": "Averages all input spectra into one"
        }
        super().__init__(nodegraph, id)

    def process(self, data):
        if len(data["input"]) == 1:
            data["output"] = data["input"]
            return
        temp = [i for i in data["input"] if i is not None]
        data["output"] = [temp[0].inherit(np.mean(temp, axis=0))] # retrieve metadata; we want a list of MRSData objects

api.RegisterNode(Average, "Average")