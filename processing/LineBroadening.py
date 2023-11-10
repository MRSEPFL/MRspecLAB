import ProcessingStep as ps
import numpy as np
import parameter_changes_GUI

class LineBroadening(ps.ProcessingStep):
    def __init__(self,parentpanel):
        super().__init__({"factor": 5})
        self.panelparameters = parameter_changes_GUI.CustomPanel(
            parentpanel,
            "Frequency Phase Alignement",
            [
                (
                    parameter_changes_GUI.NumericalParameterPanel,
                    self.parameters,
                    "factor",
                    "",
                    5,
                    1,
                    10,
                    1,
                    "",
                )
                
            ],
        )
        self.plotSpectrum = False

    def process(self, data):
        if self.parameters["factor"] <= 0: return data
        self.exp = np.exp(-data["input"][0].time_axis() * np.pi * self.parameters["factor"])
        output = []
        self.dmax = 0
        for d in data["input"]:
            output.append(d.inherit(d * self.exp))
            self.dmax = max(self.dmax, np.max(d)) # for plotting exp
        data["output"] = output

    def plot(self, canvas, data):
        canvas.figure.suptitle(self.__class__.__name__)
        ax = canvas.figure.add_subplot(2, 1, 1)
        for d in data["input"]:
            ax.plot(d.time_axis(), d)
        ax.plot(d.time_axis(), self.exp * self.dmax, ':k')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Intensity')
        ax.set_title("Input and apodisation function")
        ax = canvas.figure.add_subplot(2, 1, 2)
        for d in data["output"]:
            ax.plot(d.time_axis(), d)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Intensity')
        ax.set_title("Output")
        canvas.figure.tight_layout()
        canvas.draw()