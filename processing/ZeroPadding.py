import ProcessingStep as ps
import numpy as np

class ZeroPadding(ps.ProcessingStep):
    def __init__(self):
        super().__init__({"factor": 3})
        self.plotSpectrum = False

    def process(self, data):
        if self.parameters["factor"] <= 0: return data
        output = []
        for d in data:
            padding = np.zeros(int((np.floor(len(d) * self.parameters["factor"]))))
            output.append(d.inherit(np.concatenate((d, padding), axis=None)))
        return output