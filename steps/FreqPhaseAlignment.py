from processing.ProcessingStep import ProcessingStep
import api
import numpy as np
import scipy

class FreqPhaseAlignment(ProcessingStep):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Frequency and Phase Alignment",
            "author": "CIBM",
            "version": (0, 0, 0),
            "category": "QUALITY CONTROL",
            "description": "Performs frequency and phase alignment"
        }
        self.parameters = [
            api.ChoiceProp(
                idname="alignFreq",
                default="True",
                choices=["True", "False"],
                exposed=False,
                fpb_label="Perform frequency alignment"
            ),
            api.ChoiceProp(
                idname="alignPhase",
                default="True",
                choices=["True", "False"],
                exposed=False,
                fpb_label="Perform phase alignment"
            ),
            api.VectorProp( # tuple of length 3
                idname="freqRange", 
                default=(3, 3.2, 0), 
                labels=("Lower Bound", "Higher Bound"),
                min_vals=(0, 0, 0), 
                max_vals=(6, 6, 0),
                exposed=False,
                show_p=False, 
                fpb_label="Frequency range to optimise alignment on (in ppm)"
            ),
            api.ChoiceProp(
                idname="median",
                default="True",
                choices=["True", "False"],
                exposed=False,
                fpb_label="Set target to median of input data"
            ),
            api.IntegerProp(
                idname="target",
                default=0,
                min_val=0,
                max_val=1000,
                show_p=True,
                exposed=False,
                fpb_label="Set target to index of input data (if not median)"
            )
        ]
        super().__init__(nodegraph, id)
    
    def process(self, data):
        if not self.get_parameter("alignFreq") and not self.get_parameter("alignPhase"):
            data["output"] = data["input"]
            return
        freqRange = self.get_parameter("freqRange")[:-1]
        freqRange = [data["input"][0].ppm_to_hertz(f) for f in freqRange]
        freqRange.sort()
        freqRange = tuple(freqRange)
        if self.get_parameter("median"): target = data["input"][0].inherit(np.median(data["input"], axis=0))
        elif self.get_parameter("target") in range(len(data["input"])): target = data["input"][self.get_parameter("target")]
        else: target = data["input"][0]
        self.freqShifts = []
        self.phaseShifts = []
        output = []
        for i in range(len(data["input"])):
            # adapted from suspect.processing.frequency_correction.spectral_registration
            spectral_weights = np.logical_and(freqRange[0] < data["input"][i].frequency_axis(), freqRange[1] > data["input"][i].frequency_axis())

            def residual(input_vector):
                transformed_data = data["input"][i]
                if self.get_parameter("alignFreq"): transformed_data = transformed_data.adjust_frequency(-input_vector[0])
                if self.get_parameter("alignPhase"): transformed_data = transformed_data.adjust_phase(-input_vector[1])
                residual_data = transformed_data - target
                spectrum = residual_data.spectrum()
                weighted_spectrum = spectrum * spectral_weights
                weighted_spectrum = weighted_spectrum[weighted_spectrum != 0]
                residual_data = np.fft.ifft(np.fft.ifftshift(weighted_spectrum))
                return_vector = np.zeros(len(residual_data) * 2)
                return_vector[:len(residual_data)] = residual_data.real
                return_vector[len(residual_data):] = residual_data.imag
                return return_vector
            
            out = scipy.optimize.leastsq(residual, (0, 0))
            [freqShift, phaseShift] = out[0][:2]

            self.freqShifts.append(freqShift)
            self.phaseShifts.append(phaseShift)
            output.append(data["original"][i].adjust_frequency(-freqShift).adjust_phase(-phaseShift))
        data["output"] = output

    def plot(self, figure, data):
        figure.suptitle(self.__class__.__name__)
        ax = figure.add_subplot(2, 6, (1, 3))
        for d in data["input"]:
            ax.plot(d.frequency_axis_ppm(), np.real(d.spectrum()))
        ax.set_xlabel('Chemical shift (ppm)')
        ax.set_ylabel('Amplitude')
        ax.set_title("Input")
        ax.set_xlim((np.max(d.frequency_axis_ppm()), np.min(d.frequency_axis_ppm())))
        ax = figure.add_subplot(2, 6, (4, 6))
        for d in data["output"]:
            ax.plot(d.frequency_axis_ppm(), np.real(d.spectrum()))
        ax.set_xlabel('Chemical shift (ppm)')
        ax.set_ylabel('Amplitude')
        ax.set_title("Shifts applied to original data (output)")
        ax.set_xlim((np.max(d.frequency_axis_ppm()), np.min(d.frequency_axis_ppm())))
        ax = figure.add_subplot(2, 6, (7, 8))
        for i, d in enumerate(data["input"]):
            d = d.adjust_frequency(-self.freqShifts[i]).adjust_phase(-self.phaseShifts[i])
            ax.plot(d.frequency_axis_ppm(), np.real(d.spectrum()))
        ax.set_xlabel('Chemical shift (ppm)')
        ax.set_ylabel('Amplitude')
        ax.set_title("Shifts applied to input data")
        ax.set_xlim((np.max(d.frequency_axis_ppm()), np.min(d.frequency_axis_ppm())))
        ax = figure.add_subplot(2, 6, (9, 10))
        ax.plot(self.freqShifts)
        ax.set_xlabel('Index')
        ax.set_ylabel('Frequency shift (Hz)')
        ax.set_title("Frequency shifts" + (" (not used)" if self.get_parameter("alignFreq") is False else ""))
        ax = figure.add_subplot(2, 6, (11, 12))
        ax.plot(self.phaseShifts)
        ax.set_xlabel('Index')
        ax.set_ylabel('Phase shift (rad)')
        ax.set_title("Phase shifts" + (" (not used)" if self.get_parameter("alignPhase") is False else ""))
        figure.tight_layout()

api.RegisterNode(FreqPhaseAlignment, "FreqPhaseAlignment")