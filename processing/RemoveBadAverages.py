import ProcessingStep as ps
import numpy as np

class RemoveBadAverages(ps.ProcessingStep):
    def __init__(self):
        super().__init__({"stdDevThreshold": 3, "domain": "time", "tmax": 0.4})
        self.plotSpectrum = False

    def process(self, data):
        if len(data["input"]) <= 2: return data["input"]
        output = []
        metric = []
        if self.parameters["domain"].lower() == "time":
            ref = np.mean(data["input"], axis=0)
            trange = data["input"][0].time_axis() <= self.parameters["tmax"]
            for d in data["input"]: metric.append(np.sum((d[trange] - ref[trange])**2))
        elif self.parameters["domain"].lower().startswith("freq"):
            specs = [d.spectrum() for d in data["input"]]
            ref = np.mean(specs, axis=0)
            for d in data["input"]: metric = np.sum((s - ref)**2 for s in specs)
        self.zscores = (metric - np.mean(metric)) / np.std(metric)
        mask = np.abs(self.zscores) < self.parameters["stdDevThreshold"]
        self.removed = []
        for i, d in enumerate(data["input"]):
            if mask[i]: output.append(d)
            else: self.removed.append(i)
        data["output"] = output

    def plot(self, canvas, data):
        ax = canvas.figure.add_subplot(2, 1, 1)
        for i, d in enumerate(data["input"]):
            if i in self.removed: colour = "red"
            else: colour = (0, 0, 0, 1/len(data["input"]))
            ax.plot(d.time_axis(), d, c=colour)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Intensity')
        ax.set_title("Removed data: " + str(self.removed))
        ax = canvas.figure.add_subplot(2, 1, 2)
        for i, d in enumerate(data["input"]):
            if i in self.removed: colour = "red"
            else: colour = (0, 0, 0, 1/len(data["input"]))
            ax.plot(d.frequency_axis_ppm(), d.spectrum(), c=colour)
        ax.set_xlabel('Chemical shift (ppm)')
        ax.set_ylabel('Amplitude')
        ax.set_xlim((np.max(d.frequency_axis_ppm()), np.min(d.frequency_axis_ppm())))
        canvas.figure.suptitle(self.__class__.__name__ + " (domain: " + self.parameters["domain"] + ")")
        canvas.figure.tight_layout()
        canvas.draw()