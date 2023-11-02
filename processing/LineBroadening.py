import ProcessingStep as ps
import numpy as np

class LineBroadening(ps.ProcessingStep):
    def __init__(self):
        super().__init__({"factor": 5})
        self.plotSpectrum = False

    def process(self, data):
        if self.parameters["factor"] <= 0: return data
        output = []
        for d in data["input"]:
            output.append(d.inherit(d * np.exp(-d.time_axis() * np.pi * self.parameters["factor"])))
        return output