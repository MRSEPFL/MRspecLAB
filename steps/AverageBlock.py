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
                fpb_label="Number of measurements in an experimental block"
            ),
            api.IntegerProp(
                idname="Block averages",
                default=1,
                min_val=1,
                max_val=20,
                show_p=True,
                exposed=False,
                fpb_label="Number of averages to produce per block"
            ),
            api.IntegerProp(
                idname="Block types",
                default=2,
                min_val=1,
                max_val=10,
                show_p=True,
                exposed=False,
                fpb_label="Number of block types; assuming periodicity of the block sequence"
            )
        ]
        super().__init__(nodegraph, id)

    def process(self, data):
        block_length = self.get_parameter("Block length")
        block_averages = self.get_parameter("Block averages")
        block_types = self.get_parameter("Block types")
        step = block_length // block_averages
        output = []
        labels = []
        datain = np.array(data["input"])
        i = 0
        while i < len(data["input"]):
            to_average = datain[i:i+step]
            if len(to_average) == 0: break
            output.append(data["input"][i].inherit(np.mean(to_average, axis=0)))
            current_block = int(i // block_length)
            current_average = i // step
            labels.append(f"type{current_block % block_types}block{int(current_block // block_types)}average{current_average % block_averages}")
            i += step
        data["output"] = output
        data["labels"] = labels

api.RegisterNode(AverageBlock, "AverageBlock")