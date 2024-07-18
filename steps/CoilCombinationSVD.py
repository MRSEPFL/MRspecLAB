from processing.ProcessingStep import ProcessingStep
import gs.api as api
from suspect.processing.channel_combination import combine_channels
from processing.processing_helpers import zero_phase_flip

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
        if len(data["input"][0].shape) == 1: # single coil data
            data["output"] = data["input"]
            return
        data["output"] = [combine_channels(d) for d in data["input"]]
        zero_phase_flip(data["output"])
        if data["wref"] is not None:
            data["wref_output"] = combine_channels(data["wref"])
    
    # default plotter doesn't handle multi-coil data
    def plot(self, figure, data):
        if len(data["input"][0].shape) == 1:
            self.plotData(figure.add_subplot(2, 1, 1), data["input"], False)
            self.plotData(figure.add_subplot(2, 1, 2), data["output"], True)
            figure.suptitle(self.__class__.__name__ + " (nothing done)")
            return
        datain = data["input"][0]
        coils = [datain.inherit(datain[_]) for _ in range(datain.shape[0])]
        # time
        ax = figure.add_subplot(2, 2, 1)
        self.plotData(ax, coils, False)
        ax.set_title("Coils of first input")
        ax = figure.add_subplot(2, 2, 2)
        self.plotData(ax, data["output"], False)
        ax.set_title("Output")
        # freq
        ax = figure.add_subplot(2, 2, 3)
        self.plotData(ax, coils, True)
        ax.set_title("Coils of first input")
        ax = figure.add_subplot(2, 2, 4)
        self.plotData(ax, data["output"], True)
        ax.set_title("Output")
        figure.suptitle(self.__class__.__name__)
        figure.tight_layout()

api.RegisterNode(CoilCombinationSVD, "CoilCombinationSVD")