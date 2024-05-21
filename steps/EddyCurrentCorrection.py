from processing.ProcessingStep import ProcessingStep
import gs.api as api
import numpy as np

class EddyCurrentCorrection(ProcessingStep):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Eddy Current Correction",
            "author": "CIBM",
            "version": (0, 0, 0),
            "category": "QUALITY CONTROL",
            "description": "Performs Eddy Current Correction",
        }
        self.parameters = [
            api.IntegerProp(
                idname="gaussian_width",
                default=32,
                min_val=0,
                max_val=100,
                show_p=True,
                exposed=False,
                fpb_label="Gaussian width of the phase smoothing window"
            )
        ]
        super().__init__(nodegraph, id)

    def process(self, data):
        if data["wref"] is None:
            data["output"] = data["input"]
            return
        w = self.get_parameter("gaussian_width")
        window = np.linspace(-3, 3, w)
        window = np.exp(-window**2)
        window /= np.sum(window)
        self.wphase = np.unwrap(np.angle(data["wref"]))
        self.wphasesmooth = np.convolve(self.wphase, window, mode="same")
        window = len(self.wphase) // 10
        poly = np.polynomial.polynomial.Polynomial.fit(data["wref"].time_axis()[:window], self.wphasesmooth[:window], 1)
        coef = poly.convert().coef
        self.wphasefit = coef[1] * data["wref"].time_axis() + coef[0]
        ecc = np.exp(-1j * (self.wphasesmooth - self.wphasefit))
        output = []
        for d in data["input"]: output.append(d * ecc)
        ecwref = data["wref"] * ecc
        data["output"] = output
        data["wref_output"] = ecwref
    
    def plot(self, figure, data):
        figure.suptitle(self.__class__.__name__)
        if data["wref"] is None:
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
        ax.plot(data["wref"].time_axis(), self.wphase, "-k", label="original phase")
        ax.plot(data["wref"].time_axis(), self.wphasesmooth, ":r", label="smoothed phase")
        ax.plot(data["wref"].time_axis(), self.wphasefit, ":k", label="linear fit to smoothed phase")
        ax.plot(data["wref_output"].time_axis(), np.unwrap(np.angle(data["wref_output"])), "-b", label="corrected phase\n= original - (smoothed - fit)")
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Phase (rad)')
        ax.legend()
        ax.set_title("Water reference phase")
        figure.tight_layout()

api.RegisterNode(EddyCurrentCorrection, "EddyCurrentCorrection")