from processing.ProcessingStep import ProcessingStep
import gs.api as api
import numpy as np

class AverageBlock(ProcessingStep):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Block Averaging",
            "author": "CIBM",
            "description": "Averages every N spectra into one"
        }
        self.parameters = [
            api.IntegerProp(
                idname="Block length",
                default=16,
                min_val=1,
                max_val=100,
                show_p=True,
                exposed=False,
                fpb_label="Block length"
            )
        ]
        super().__init__(nodegraph, id)

    def process(self, data):
        block_length = self.get_parameter("Block length")
        output = []
        i = 0
        while i < len(data["input"]):
            block = data["input"][i:i+block_length]
            if len(block) == 0: break
            output.append(data["input"][i].inherit(np.mean(block, axis=0)))
            i += block_length
        data["output"] = output

api.RegisterNode(AverageBlock, "AverageBlock")