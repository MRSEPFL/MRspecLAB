import ProcessingStep as ps
import suspect
import numpy as np
import scipy

class FreqPhaseAlignment(ps.ProcessingStep):
    def __init__(self):
        super().__init__({"freqRange": (3., 3.2), "median": True, "target": 0})
        self.alignFreq = True
        self.alignPhase = True
    
    def process(self, data):
        if not self.alignFreq and not self.alignPhase: return data["input"]
        if not isinstance(self.parameters["freqRange"], tuple) or len(self.parameters["freqRange"]) != 2: freqRange = None
        else:
            freqRange = [data["input"][0].ppm_to_hertz(f) for f in self.parameters["freqRange"]]
            freqRange.sort()
            freqRange = tuple(freqRange)
        if self.parameters["median"]: target = data["input"][0].inherit(np.median(data["input"], axis=0))
        elif self.parameters["target"] in range(len(data["input"])): target = data["input"][self.parameters["target"]]
        else: target = data["input"][0]
        self.freqShifts = []
        self.phaseShifts = []
        output = []
        for i in range(len(data["input"])):
            # adapted from suspect.processing.frequency_correction.spectral_registration
            if type(freqRange) is not None:
                spectral_weights = np.logical_and(freqRange[0] < data["input"][i].frequency_axis(), freqRange[1] > data["input"][i].frequency_axis())
            else: spectral_weights = freqRange

            def residual(input_vector):
                transformed_data = data["input"][i]
                if self.alignFreq: transformed_data = transformed_data.adjust_frequency(-input_vector[0])
                if self.alignPhase: transformed_data = transformed_data.adjust_phase(-input_vector[1])
                residual_data = transformed_data - target
                if freqRange is not None:
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

    def plot(self, canvas, data):
        canvas.figure.suptitle(self.__class__.__name__)
        ax = canvas.figure.add_subplot(2, 2, 1)
        for d in data["input"]:
            ax.plot(d.frequency_axis_ppm(), d.spectrum())
        ax.set_xlabel('Frequency (ppm)')
        ax.set_ylabel('Amplitude')
        ax.set_title("Input")
        ax = canvas.figure.add_subplot(2, 2, 2)
        for d in data["output"]:
            ax.plot(d.frequency_axis_ppm(), d.spectrum())
        ax.set_xlabel('Frequency (ppm)')
        ax.set_ylabel('Amplitude')
        ax.set_title("Output")
        ax = canvas.figure.add_subplot(2, 2, 3)
        ax.plot(self.freqShifts)
        ax.set_xlabel('Index')
        ax.set_ylabel('Frequency shift (Hz)')
        ax.set_title("Frequency shifts")
        ax = canvas.figure.add_subplot(2, 2, 4)
        ax.plot(self.phaseShifts)
        ax.set_xlabel('Index')
        ax.set_ylabel('Phase shift (rad)')
        ax.set_title("Phase shifts")
        canvas.figure.tight_layout()
        canvas.draw()