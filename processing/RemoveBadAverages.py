import ProcessingStep as ps
import numpy as np

class RemoveBadAverages(ps.ProcessingStep):
    def __init__(self):
        super().__init__({"stdDevThreshold": 3, "domain": "time", "tmax": 0.4})
        self.plotSpectrum = False

    def process(self, data):
        if len(data) <= 2: return data
        output = []
        metric = []
        if self.parameters["domain"].lower() == "time":
            ref = np.mean(data, axis=0)
            trange = data[0].time_axis() <= self.parameters["tmax"]
            for d in data: metric.append(np.sum((d[trange] - ref[trange])**2))
        elif self.parameters["domain"].lower().startswith("freq"):
            specs = [d.spectrum() for d in data]
            ref = np.mean(specs, axis=0)
            for d in data: metric = np.sum((s - ref)**2 for s in specs)
        self.zscores = (metric - np.mean(metric)) / np.std(metric)
        mask = np.abs(self.zscores) < self.parameters["stdDevThreshold"]
        for i, d in enumerate(data):
            if mask[i]: output.append(d)
        return output