from processing.ProcessingStep import ProcessingStep
import gs.api as api
import numpy as np

class LineBroadening(ProcessingStep):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Line Broadening",
            "author": "CIBM",
            "description": "Shifts spectra in the frequency domain by factor * pi",
        }
        self.parameters = [
            api.IntegerProp(
                idname="factor",
                default=5,
                min_val=1,
                max_val=50,
                show_p=True,
                exposed=False,
                fpb_label="Factor"
            )
        ]
        super().__init__(nodegraph, id)
        self.plotSpectrum = False

    def process(self, data):
        self.exp = np.exp(-data["input"][0].time_axis() * np.pi * self.get_parameter("factor"))
        output = []
        self.dmax = 0
        for d in data["input"]:
            output.append(d.inherit(d * self.exp))
            self.dmax = max(self.dmax, np.max(d)) # for plotting exp
        data["output"] = output

    def plot(self, figure, data):
        figure.suptitle(self.__class__.__name__)
        ax = figure.add_subplot(2, 1, 1)
        for d in data["input"]:
            ax.plot(d.time_axis(), np.real(d))
        ax.plot(d.time_axis(), self.exp * self.dmax, ':k')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Intensity')
        ax.set_title("Input and apodisation function")
        ax = figure.add_subplot(2, 1, 2)
        for d in data["output"]:
            ax.plot(d.time_axis(), np.real(d))
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Intensity')
        ax.set_title("Output")
        figure.tight_layout()

api.RegisterNode(LineBroadening, "LineBroadening")