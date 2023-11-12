import ProcessingStep as ps
import numpy as np
from scipy.optimize import curve_fit

def gaussian(x, a, x0, sigma):
    return a * np.exp(-(x - x0)**2 / (2 * sigma**2))

class EddyCurrentCorrection(ps.ProcessingStep):
    def __init__(self):
        super().__init__({ "gaussian_width": 32 })

    # https://suspect.readthedocs.io/en/latest/notebooks/consensus_playground.html#Eddy-Current-Correction
    def process(self, data):
        if data["wref"] is None:
            data["output"] = data["input"]
            return
        # adapted from suspect.processing.denoising.sliding_gaussian
        w = self.parameters["gaussian_width"]
        window = np.linspace(-3, 3, w)
        window = np.exp(-window**2)
        window /= np.sum(window)
        self.wphase = np.unwrap(np.angle(data["wref"]))
        self.wphasesmooth = np.convolve(self.wphase, window, mode="same")
        ecc = np.exp(-1j * (self.wphasesmooth))
        output = []
        for d in data["input"]:
            output.append(d * ecc)
        ecwref = data["wref"] * ecc
        self.gaussparams, _ = curve_fit(gaussian, ecwref.frequency_axis_ppm(), ecwref.spectrum(), p0=[np.abs(np.max(ecwref.spectrum())), 4.7, 1])
        data["output"] = output
        data["wref_output"] = ecwref
    
    def plot(self, canvas, data):
        canvas.figure.suptitle(self.__class__.__name__)
        if data["wref"] is None:
            ax = canvas.figure.add_subplot(1, 1, 1)
            for d in data["output"]:
                ax.plot(d.frequency_axis_ppm()[::-1], d.spectrum())
            ax.set_xlabel('Chemical shift (ppm)')
            ax.set_ylabel('Amplitude')
            ax.set_title("Output (no water reference given)")
            return
        # input
        ax = canvas.figure.add_subplot(2, 2, 1)
        for d in data["input"]:
            ax.plot(d.frequency_axis_ppm()[::-1], d.spectrum())
        ax.set_xlabel('Chemical shift (ppm)')
        ax.set_ylabel('Amplitude')
        ax.set_title("Input")
        # output
        ax = canvas.figure.add_subplot(2, 2, 2)
        for d in data["output"]:
            ax.plot(d.frequency_axis_ppm()[::-1], d.spectrum())
        ax.set_xlabel('Chemical shift (ppm)')
        ax.set_ylabel('Amplitude')
        ax.set_title("Output")
        # water reference phase
        ax = canvas.figure.add_subplot(2, 2, 3)
        ax.plot(data["wref"].time_axis(), self.wphase, "-k", label="original phase")
        ax.plot(data["wref"].time_axis(), self.wphasesmooth, ":r", label="smoothed phase")
        ax.plot(data["wref_output"].time_axis(), np.unwrap(np.angle(data["wref_output"])), "-b", label="corrected phase")
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Phase (rad)')
        ax.legend()
        ax.set_title("Water reference phase")
        # water reference
        ax = canvas.figure.add_subplot(2, 2, 4)
        fwhm = np.abs(2 * np.sqrt(2 * np.log(2)) * self.gaussparams[2])
        fwhmhz = data["wref_output"].ppm_to_hertz(fwhm)
        gauss = gaussian(data["wref_output"].frequency_axis_ppm(), *self.gaussparams)
        ax.plot(data["wref"].frequency_axis_ppm()[::-1], data["wref"].spectrum(), "-k", label="original")
        ax.plot(data["wref"].frequency_axis_ppm()[::-1], data["wref_output"].spectrum(), "-b", label="corrected")
        ax.plot(data["wref"].frequency_axis_ppm()[::-1], gauss, ":r", label="gaussian fit")
        ax.text(self.gaussparams[1], self.gaussparams[0] / 2, f"FWHM = {fwhm:.2f} ppm / {fwhmhz:.2f} Hz", ha="center", va="center")
        ax.set_xlabel('Chemical shift (ppm)')
        ax.set_ylabel('Amplitude')
        ax.legend()
        ax.set_xlim(self.gaussparams[1] - 5 * self.gaussparams[2], self.gaussparams[1] + 5 * self.gaussparams[2])
        ax.set_title("Water reference")
        canvas.figure.tight_layout()
        canvas.draw()