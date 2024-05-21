from processing.ProcessingStep import ProcessingStep
import gs.api as api
import numpy as np

class ZeroPadding(ProcessingStep):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Zero padding",
            "author": "MRSoftware",
            "version": (0, 0, 0),
            "category": "QUALITY CONTROL",
            "description": "Adds factor times the length of the data with zeros",
        }
        self.parameters = [
            api.IntegerProp(
                idname="factor",
                default=3,
                min_val=1,
                max_val=10,
                show_p=True,
                exposed=False,
                fpb_label="Factor"
            )
        ]
        super().__init__(nodegraph, id)
        self.plotSpectrum = False

    def process(self, data):
        if self.get_parameter("factor") <= 0: return data
        output = []
        for d in data["input"]:
            padding = np.zeros(int((np.floor(len(d) * self.get_parameter("factor")))))
            output.append(d.inherit(np.concatenate((d, padding), axis=None)))
        data["output"] = output

api.RegisterNode(ZeroPadding, "ZeroPadding")