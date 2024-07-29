import processing.api as api
from nodes._CoilCombinationAdaptive import coil_combination_adaptive

class CoilCombinationAdaptive(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Adaptive Coil Combination",
            "author": "CIBM",
            "description": "Performs adaptive coil combination",
            "category": "COIL_COMBINATION" # important
        }
        self.parameters = [
            api.IntegerProp(
                idname="Shots per measurement",
                default=0,
                min_val=0,
                max_val=16,
                fpb_label="Number of shots per measurement; 0 uses header data"
            )
        ]
        super().__init__(nodegraph, id)

    def process(self, data):
        if len(data["input"][0].shape) == 1: # single coil data
            data["output"] = data["input"]
            return
        p = self.get_parameter("Shots per measurement")
        coil_combination_adaptive(data, p)
    
    # default plotter doesn't handle multi-coil data
    def plot(self, figure, data):
        if len(data["input"][0].shape) == 1: # single coil data
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

api.RegisterNode(CoilCombinationAdaptive, "CoilCombinationAdaptive")