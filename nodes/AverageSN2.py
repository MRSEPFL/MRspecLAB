import processing.api as api
import numpy as np

class AverageSN2(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "S/N² Averaging",
            "author": "CIBM",
            "description": "Averages every N spectra into one following the S/N² criterion"
        }
        self.parameters = [
            api.IntegerProp(
                idname="Repetition length",
                default=16,
                min_val=1,
                max_val=100,
                fpb_label="Number of measurements in a repetition"
            ),
            api.FloatProp(
                idname="Noise proportion",
                default=0.25,
                min_val=0,
                max_val=1,
                fpb_label="Proportion from the end of the FID to use as noise"
            )
        ]
        super().__init__(nodegraph, id)

    def process(self, data):
        step = self.get_parameter("Repetition length")
        noise_prop = int(self.get_parameter("Noise proportion") * len(data["input"][0]))
        output = []
        i = 0
        while i < len(data["input"]):
            to_average = data["input"][i:i+step]
            if len(to_average) == 0: break
            to_average = [x for x in to_average if x is not None]
            weights = [d[1] / np.std(d[-noise_prop:])**2 for d in to_average]
            weights /= np.sum(weights)
            output.append(to_average[0].inherit(np.average(to_average, axis=0, weights=weights)))
            i += step
        data["output"] = output

api.RegisterNode(AverageSN2, "AverageSN2")