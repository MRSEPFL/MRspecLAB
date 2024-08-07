import processing.api as api
import numpy as np

class AverageMoving(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Moving Average",
            "author": "CIBM",
            "description": "Averages spectra with a moving window of a given length"
        }
        self.parameters = [
            api.IntegerProp(
                idname="Window length",
                default=16,
                min_val=1,
                max_val=100,
                fpb_label="Window length"
            )
        ]
        super().__init__(nodegraph, id)

    def process(self, data):
        window_length = self.get_parameter("Window length")
        output = []
        labels = []
        i = 0
        while i < len(data["input"]):
            window = data["input"][i:i+window_length]
            if len(window) < window_length: break
            output.append(data["input"][i].inherit(np.mean(window, axis=0)))
            labels.append(f"averages{i+1}to{i+window_length}")
            i += 1
        if len(output) == 0:
            data["output"] = [data["input"][0].inherit(np.mean(data["input"], axis=0))]
            return
        data["output"] = output
        data["labels"] = labels

api.RegisterNode(AverageMoving, "AverageMoving")