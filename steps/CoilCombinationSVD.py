from processing.ProcessingStep import ProcessingStep
import gs.api as api
import numpy as np
from suspect.processing.channel_combination import combine_channels

class CoilCombinationSVD(ProcessingStep):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "SVD Coil Combination",
            "author": "CIBM",
            "description": "Performs basic SVD coil combination",
            "category": "COIL_COMBINATION" # important
        }
        super().__init__(nodegraph, id)

    def process(self, data):
        data["output"] = [combine_channels(d) for d in data["input"]]
        if data["wref"] is not None:
            data["wref_output"] = combine_channels(data["wref"])
        data["original"] = data["output"] # very illegal but prevents problems in FreqPhaseAlignment
    
    # default plotter doesn't handle multi-coil data
    def plot(self, figure, data):
        datain = np.array(data["input"]).transpose(1, 0, 2) # from (rep, coil, col) to (coil, rep, col)
        datain = [data["input"][0].inherit(d) for d in datain] # turn back into MRSData objects
        coils = []
        for d in datain:
            coils += [d.inherit(d[_]) for _ in range(0, d.shape[0])]
        sx, sy = 2, 2
        index = 1
        # time
        ax = figure.add_subplot(sx, sy, index)
        self.plotData(ax, coils, False)
        ax.set_title("Input")
        ax = figure.add_subplot(sx, sy, index + sy)
        self.plotData(ax, data["output"], False)
        ax.set_title("Output")
        index += 1
        # freq
        ax = figure.add_subplot(sx, sy, index)
        self.plotData(ax, coils, True)
        ax.set_title("Input")
        ax = figure.add_subplot(sx, sy, index + sy)
        self.plotData(ax, data["output"], True)
        ax.set_title("Output")
        figure.suptitle(self.__class__.__name__)
        figure.tight_layout()

api.RegisterNode(CoilCombinationSVD, "CoilCombinationSVD")