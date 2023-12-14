from processing.ProcessingStep import ProcessingStep
import numpy as np
from scipy.optimize import curve_fit

def gaussian(x, a, x0, sigma):
    return a * np.exp(-(x - x0)**2 / (2 * sigma**2))

class QualityMatrix(ProcessingStep):
    def __init__(self):
        super().__init__()

    def process(self, data):
        self.snr = []
        for d in data["input"]:
            ppms = d.frequency_axis_ppm()
            spec = d.spectrum()
            naapeak = np.max(np.real(spec[np.where(np.logical_and(ppms > 1.8, ppms < 2.2))]))
            noise = np.real(spec[np.where(np.logical_and(ppms > 0, ppms < 0.5))])
            poly = np.polynomial.polynomial.Polynomial.fit(range(len(noise)), noise, 5)
            noise -= poly(range(len(noise)))
            noisestd = np.std(noise)
            self.snr.append(naapeak / noisestd)

        water = data["wref"]
        # wphase = np.angle(water)
        # poly = np.polynomial.polynomial.Polynomial.fit(water.time_axis(), wphase, 1)
        # wphase = poly.convert().coef[1] * water.time_axis() + poly.convert().coef[0]
        # water = water.adjust_phase(2 * wphase) # idk

        self.wspec = np.real(water.spectrum())
        self.gaussparams, _ = curve_fit(gaussian, water.frequency_axis_ppm(), self.wspec, p0=[np.max(self.wspec), 4.7, 0.01])
        self.fwhm = np.abs(2 * np.sqrt(2 * np.log(2)) * self.gaussparams[2])
        self.fwhmhz = self.fwhm * data["input"][0].f0
        data["output"] = data["input"] # no change
        data["wref_output"] = data["wref"] # same

    def plot(self, figure, data):
        figure.suptitle(self.__class__.__name__)
        ax = figure.add_subplot(2, 1, 1)
        ax.plot(range(len(self.snr)), self.snr, "-k")
        ax.plot(range(len(self.snr)), np.mean(self.snr) * np.ones(len(self.snr)), "--r")
        ax.text(0, np.mean(self.snr), f"mean = {np.mean(self.snr):.2f}\nstd = {np.std(self.snr):.2f}", ha="left", va="center")
        ax.fill_between(range(len(self.snr)), np.mean(self.snr) - np.std(self.snr), np.mean(self.snr) + np.std(self.snr), alpha=0.2)
        ax.set_xlabel('Index')
        ax.set_ylabel('SNR')
        ax.set_title("Signal-to-noise ratio")

        ax = figure.add_subplot(2, 1, 2)
        gauss = gaussian(data["wref_output"].frequency_axis_ppm(), *self.gaussparams)
        ax.plot(data["wref"].frequency_axis_ppm(), np.real(data["wref"].spectrum()), "-k", label="original")
        ax.plot(data["wref"].frequency_axis_ppm(), self.wspec, "-b", label="corrected")
        ax.plot(data["wref"].frequency_axis_ppm(), gauss, ":r", label="gaussian fit")
        ax.text(self.gaussparams[1], self.gaussparams[0] / 2, f"FWHM = {self.fwhm:.2f} ppm\n= {self.fwhmhz:.2f} Hz", ha="center", va="center")
        ax.set_xlabel('Chemical shift (ppm)')
        ax.set_ylabel('Amplitude')
        ax.legend()
        ax.set_xlim(self.gaussparams[1] + 5 * self.gaussparams[2], self.gaussparams[1] - 5 * self.gaussparams[2])
        ax.set_title("Water reference")
        figure.tight_layout()
