from processing.ProcessingStep import ProcessingStep
import gs.api as api
import numpy as np

class CoilCombinationSN2(ProcessingStep):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "S/N² Coil Combination",
            "author": "CIBM",
            "description": "Performs S/N² coil combination",
            "category": "COIL_COMBINATION" # important
        }
        self.parameters = [
            api.IntegerProp(
                idname="Shots per measurement",
                default=0,
                min_val=0,
                max_val=16,
                show_p=True,
                exposed=False,
                fpb_label="Number of shots per measurement; 0 uses header data"
            ),
            api.FloatProp(
                idname="Noise proportion",
                default=0.25,
                min_val=0,
                max_val=1,
                show_p=True,
                exposed=False,
                fpb_label="Proportion from the end of the FID to use as noise"
            )
        ]
        super().__init__(nodegraph, id)

    def process(self, data):
        if len(data["input"][0].shape) == 1: # single coil data
            data["output"] = data["input"]
            return
        if len(data["wref"]) == 0: # no water reference
            data["output"] = data["input"]
            return
        ncoils = len(data["input"][0])

        # phase correction
        wref = np.average(np.array(data["wref"]), 0)
        phases = np.zeros(ncoils)
        for i in range(ncoils):
            maxindex = np.argmax(np.abs(wref[i]))
            phases[i] = np.angle(wref[i][maxindex])
        output = []
        for d in data["input"]:
            temp = []
            for j in range(ncoils):
                temp.append(d[j] * np.exp(-1j * phases[j]))
            output.append(d.inherit(np.array(temp)))
        woutput = []
        for d in data["wref"]:
            temp = []
            for j in range(ncoils):
                temp.append(d[j] * np.exp(-1j * phases[j]))
            woutput.append(d.inherit(np.array(temp)))

        # noise weighting
        datain = np.average(np.array(output), 0)
        weights = np.zeros(ncoils)
        noise_prop = int(self.get_parameter("Noise proportion") * len(data["input"][0]))
        for i in range(0, ncoils):
            noisestd = np.std(datain[i][-noise_prop:])
            rmax = np.max(np.real(datain[i]))
            weights[i] = rmax / noisestd**2
        output = np.average(np.array(output), 1, weights=weights)
        woutput = np.average(np.array(woutput), 1, weights=weights)
        
        p = self.get_parameter("Shots per measurement")
        if p == 0: p = data["input"][0].metadata["ave_per_rep"]
        data["output"] = [data["input"][0].inherit(np.mean(output[i:i+p], 0)) for i in range(0, len(output), p)]
        data["wref_output"] = [data["wref"][0].inherit(np.mean(woutput[i:i+p], 0)) for i in range(0, len(woutput), p)]
    
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

api.RegisterNode(CoilCombinationSN2, "CoilCombinationSN2")