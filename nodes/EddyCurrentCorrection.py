import processing.api as api
import numpy as np

class EddyCurrentCorrection(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Eddy Current Correction",
            "author": "CIBM",
            "description": "Performs Eddy Current Correction",
        }
        self.parameters = [
            api.IntegerProp(
                idname="gaussian_width",
                default=32,
                min_val=0,
                max_val=100,
                fpb_label="Gaussian width of the phase smoothing window"
            )
        ]
        super().__init__(nodegraph, id)

    def process(self, data):
        try:
            if len(data["wref"]) == 0:
                data["output"] = data["input"]
                return
        except:
            from interface import utils
            utils.log_info("No Water Reference. Skipping Eddy Current Correction.")
            data["output"] = data["input"]
            return
        w = self.get_parameter("gaussian_width")
        window = np.linspace(-3, 3, w)
        window = np.exp(-window**2)
        window /= np.sum(window)
        self.wphase = np.unwrap(np.angle(data["wref"][0]))
        self.wphasesmooth = np.convolve(self.wphase, window, mode="same")
        window = len(self.wphase) // 10
        poly = np.polynomial.polynomial.Polynomial.fit(data["wref"][0].time_axis()[:window], self.wphasesmooth[:window], 1)
        coef = poly.convert().coef
        self.wphasefit = coef[1] * data["wref"][0].time_axis() + coef[0]
        ecc = np.exp(-1j * (self.wphasesmooth - self.wphasefit))
        output = []
        for d in data["input"]: output.append(d * ecc)
        ecwref = data["wref"][0] * ecc
        data["output"] = output
        data["wref_output"] = [ecwref]
    
    def plot(self, figure, data):
        try:
            figure.suptitle(self.__class__.__name__)
            if len(data["wref"]) == 0:
                ax = figure.add_subplot(1, 1, 1)
                for d in data["output"]:
                    ax.plot(d.frequency_axis_ppm(), np.real(d.spectrum()))
                ax.set_xlabel('Chemical shift (ppm)')
                ax.set_ylabel('Amplitude')
                ax.set_title("Output (no water reference given)")
                ax.set_xlim((np.max(d.frequency_axis_ppm()), np.min(d.frequency_axis_ppm())))
                return
            ax = figure.add_subplot(2, 2, 1)
            for d in data["input"]:
                ax.plot(d.frequency_axis_ppm(), np.real(d.spectrum()))
            ax.set_xlabel('Chemical shift (ppm)')
            ax.set_ylabel('Amplitude')
            ax.set_title("Input")
            ax.set_xlim((np.max(d.frequency_axis_ppm()), np.min(d.frequency_axis_ppm())))
            ax = figure.add_subplot(2, 2, 2)
            for d in data["output"]:
                ax.plot(d.frequency_axis_ppm(), np.real(d.spectrum()))
            ax.set_xlabel('Chemical shift (ppm)')
            ax.set_ylabel('Amplitude')
            ax.set_title("Output")
            ax.set_xlim((np.max(d.frequency_axis_ppm()), np.min(d.frequency_axis_ppm())))
            ax = figure.add_subplot(2, 2, (3, 4))
            ax.plot(data["wref"][0].time_axis(), self.wphase, "-k", label="original phase")
            ax.plot(data["wref"][0].time_axis(), self.wphasesmooth, ":r", label="smoothed phase")
            ax.plot(data["wref"][0].time_axis(), self.wphasefit, ":k", label="linear fit to smoothed phase")
            ax.plot(data["wref_output"][0].time_axis(), np.unwrap(np.angle(data["wref_output"][0])), "-b", label="corrected phase\n= original - (smoothed - fit)")
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Phase (rad)')
            ax.legend()
            ax.set_title("Water reference phase")
            figure.tight_layout()
        except:
            return

api.RegisterNode(EddyCurrentCorrection, "EddyCurrentCorrection")