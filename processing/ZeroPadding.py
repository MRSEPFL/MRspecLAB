import ProcessingStep as ps
import numpy as np
import parameter_changes_GUI

class ZeroPadding(ps.ProcessingStep):
    def __init__(self,parentpanel):
        super().__init__({"factor": 3})
        self.panelparameters = parameter_changes_GUI.CustomPanel(
            parentpanel,
            "Frequency Phase Alignement",
            [
                (
                    parameter_changes_GUI.NumericalParameterPanel,
                    self.parameters,
                    "factor",
                    "",
                    3,
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
        output = []
        for d in data["input"]:
            padding = np.zeros(int((np.floor(len(d) * self.parameters["factor"]))))
            output.append(d.inherit(np.concatenate((d, padding), axis=None)))
        data["output"] = output