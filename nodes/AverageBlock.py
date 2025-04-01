import processing.api as api
import numpy as np

class AverageBlock(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Block Averaging",
            "author": "CIBM",
            "description": "Averages every N spectra into one and labels them according to block type and number"
        }
        self.parameters = [
            api.StringProp(
                idname="Block length",
                default="16",
                fpb_label="Number of measurements in an experimental block"
            ),
            api.IntegerProp(
                idname="Block averages",
                default=1,
                min_val=1,
                max_val=20,
                fpb_label="Number of averages to produce per block"
            ),
            api.IntegerProp(
                idname="Block types",
                default=2,
                min_val=1,
                max_val=10,
                fpb_label="Number of block types; assuming periodicity of the block sequence"
            )
        ]
        super().__init__(nodegraph, id)

    def process(self, data):
        block_length = int(self.get_parameter("Block length"))
        block_averages = self.get_parameter("Block averages")
        block_types = self.get_parameter("Block types")
        step = block_length // block_averages
        output = []
        labels = []
        i = 0
        while i < len(data["input"]):
            to_average = data["input"][i:i+step]
            if len(to_average) == 0: break
            to_average = [x for x in to_average if x is not None]
            output.append(to_average[0].inherit(np.mean(to_average, axis=0)))
            current_block = int(i // block_length)
            current_average = i // step

            block_num = (i // block_length) + 1
            start_in_block = i + 1
            end_in_block = i + step
            labels.append(f"Block{block_num}_av{start_in_block}-{end_in_block}")
            i += step
        if len(output) == 0:
            output = [data["input"][0].inherit(np.mean(data["input"], axis=0))]
            return
        data["output"] = output
        data["labels"] = labels

api.RegisterNode(AverageBlock, "AverageBlock")