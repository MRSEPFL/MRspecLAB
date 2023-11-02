import ProcessingStep as ps
import suspect
import numpy as np

class EddyCurrentCorrection(ps.ProcessingStep):
    def __init__(self):
        super().__init__({ "gaussian_width": 32 })

    # https://suspect.readthedocs.io/en/latest/notebooks/consensus_playground.html#Eddy-Current-Correction
    def process(self, data):
        if data["wref"] is None: return data["input"]
        # adapted from suspect.processing.denoising.sliding_gaussian
        w = self.parameters["gaussian_width"]
        window = np.linspace(-3, 3, w)
        window = np.exp(-window**2)
        window /= np.sum(window)
        self.eddysmooth = np.convolve(np.unwrap(np.angle(data["wref"])), window, mode="same")
        self.ecc = np.exp(-1j * self.eddysmooth)
        output = []
        for d in data["input"]:
            output.append(d * self.ecc)
        self.ecwref = data["wref"] * self.ecc
        return output
    
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
        ax.plot(data["wref"].time_axis(), data["wref"], ":b", label="original")
        ax.plot(data["wref"].time_axis(), self.ecwref, "-b", label="corrected")
        ax2 = ax.twinx()
        ax2.plot(data["wref"].time_axis(), self.eddysmooth, ":r", label="original phase")
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Signal Intensity')
        ax2.set_ylabel('Phase (rad)')
        handles, labels = ax.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(handles + handles2, labels + labels2)
        ax.set_title("Water reference over time")
        ax = canvas.figure.add_subplot(2, 2, 4)
        ax.plot(data["wref"].frequency_axis_ppm(), data["wref"].spectrum(), ":b", label="original")
        ax.plot(data["wref"].frequency_axis_ppm(), self.ecwref.spectrum(), "-b", label="corrected")
        ax.set_xlabel('Frequency (ppm)')
        ax.set_ylabel('Amplitude')
        ax.legend()
        ax.set_title("Water reference")
        canvas.figure.tight_layout()
        canvas.draw()