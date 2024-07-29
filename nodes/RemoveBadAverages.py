import processing.api as api
import numpy as np

class RemoveBadAverages(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Remove Bad Averages",
            "author": "CIBM",
            "description": "Removes bad quality data via z-test",
        }
        self.parameters = [
            api.IntegerProp(
                idname="stdDevThreshold",
                default=3,
                min_val=1,
                max_val=10,
                fpb_label="stddev threshold outside of which to remove the data"
            ),
            api.ChoiceProp(
                idname="domain",
                default="time",
                choices=["time", "freq"],
                fpb_label="Domain to perform the z-test on"
            ),
            api.FloatProp(
                idname="tmax",
                default=0.4,
                min_val=0.1,
                max_val=20.0,
                fpb_label="Time value up to which to perform the z-test (if domain is time)"
            )
        ]
        super().__init__(nodegraph, id)
        self.plotSpectrum = False

    def process(self, data):
        self.removed = []
        if len(data["input"]) <= 2:
            data["output"] = data["input"]
            return
        output = []
        metric = []
        if self.get_parameter("domain").lower() == "time":
            ref = np.mean(data["input"], axis=0)
            trange = data["input"][0].time_axis() <= self.get_parameter("tmax")
            for d in data["input"]: metric.append(np.sum((d[trange] - ref[trange])**2))
        elif self.get_parameter("domain").lower().startswith("freq"):
            specs = [np.abs(d.spectrum()) for d in data["input"]]
            ref = np.mean(specs, axis=0)
            for d in specs: metric.append(np.sum((d - ref)**2))
        self.zscores = (metric - np.mean(metric)) / np.std(metric)
        mask = np.abs(self.zscores) < self.get_parameter("stdDevThreshold")
        for i, d in enumerate(data["input"]):
            if mask[i]: output.append(d)
            else: self.removed.append(i)
        data["output"] = output

    def plot(self, figure, data):
        ax = figure.add_subplot(2, 1, 1)
        for i, d in enumerate(data["input"]):
            if i in self.removed: colour = "red"
            else: colour = (0, 0, 0, 1/len(data["input"]))
            ax.plot(d.time_axis(), np.real(d), c=colour)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Intensity')
        ax.set_title("Removed data: " + str(self.removed))
        ax = figure.add_subplot(2, 1, 2)
        for i, d in enumerate(data["input"]):
            if i in self.removed: colour = "red"
            else: colour = (0, 0, 0, 1/len(data["input"]))
            ax.plot(d.frequency_axis_ppm(), np.real(d.spectrum()), c=colour)
        ax.set_xlabel('Chemical shift (ppm)')
        ax.set_ylabel('Amplitude')
        ax.set_xlim((np.max(d.frequency_axis_ppm()), np.min(d.frequency_axis_ppm())))
        figure.suptitle(self.__class__.__name__ + " (domain: " + self.get_parameter("domain") + ")")
        figure.tight_layout()

api.RegisterNode(RemoveBadAverages, "RemoveBadAverages")