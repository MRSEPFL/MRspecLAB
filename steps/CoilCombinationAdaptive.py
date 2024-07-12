from processing.ProcessingStep import ProcessingStep
import gs.api as api
import numpy as np
from processing.processing_helpers import zero_phase_flip

# translated from FID-A code
def estimate_csm(data):
    ncoils = data.shape[0]
    s_raw = data / np.sqrt(np.sum(data * np.conj(data), 0))
    Rs = np.zeros((ncoils, ncoils), dtype=complex)
    for i in range(0, ncoils):
        for j in range(0, i):
            Rs[i, j] = s_raw[i] * np.conj(s_raw[j])
            Rs[j, i] = np.conj(Rs[i, j])
        Rs[i, i] = s_raw[i] * np.conj(s_raw[i])
    csm, _ = eig_power(Rs)
    return csm

def eig_power(R):
    R = np.array([[R]])
    rows, cols, ncoils = R.shape[0], R.shape[1], R.shape[2]
    N_iterations = 2
    v = np.ones((rows, cols, ncoils), dtype=complex)
    d = np.zeros((rows, cols))
    for i in range(0, N_iterations):
        v = np.sum(R * np.tile(v[..., None], (1, 1, 1, ncoils)), 2)
        d = np.sqrt(np.sum(np.abs(v) ** 2, 2))
        d[d <= np.finfo(float).eps] = np.finfo(float).eps
        v = v / np.tile(d[..., None], (1, 1, ncoils))
    p1 = np.angle(np.conj(v[:, :, 0]))
    v = v * np.tile(np.exp(1j * p1)[..., None], (1, 1, ncoils))
    v = np.conj(v)
    return v, d

def combine_channels(data):
        ref = data[:, 0]
        phase = np.exp(-1j*np.angle(ref))
        ref = ref * phase
        csm = estimate_csm(ref)
        csm = np.array(csm[0][0])
        csmsq = np.sum(csm * np.conj(csm), 0)
        csm[csm < np.finfo(float).eps] = 1
        output = []
        for i in range(0, data.shape[-1]):
            ref = data[:, i] * phase
            output.append(np.sum(np.conj(csm) * ref, 0) / csmsq)
        return data.inherit(np.array(output))

class CoilCombinationAdaptive(ProcessingStep):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Adaptive Coil Combination",
            "author": "CIBM",
            "description": "Performs adaptive coil combination",
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
        data["original"] = data["output"] # very illegal but prevents problems in FreqPhaseAlignment
        data["wref_original"] = data["wref_output"]
    
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