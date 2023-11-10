import ProcessingStep as ps
import numpy as np
import parameter_changes_GUI

class RemoveBadAverages(ps.ProcessingStep):
    def __init__(self,parentpanel):
        super().__init__({"stdDevThreshold": 3, "domain": "time", "tmax": 0.4})
        self.panelparameters = parameter_changes_GUI.CustomPanel(
            parentpanel,
            "Frequency Phase Alignement",
            [
                (
                    parameter_changes_GUI.NumericalParameterPanel,
                    self.parameters,
                    "stdDevThreshold",
                    "",
                    3,
                    1,
                    10,
                    1,
                    "",
                ),
                (
                    parameter_changes_GUI.ChoiceParameterPanel,
                    "domain",
                    [("time"), ("frequency")],
                    0,
                ),
                (
                    parameter_changes_GUI.SpinDoubleValueParameterPanel, 
                    "tmax", 
                    0.4, 
                    0,2
                ),
               
                
            ],
        )   
        
        self.plotSpectrum = False

    def process(self, data):
        if len(data["input"]) <= 2: return data["input"]
        output = []
        metric = []
        if self.parameters["domain"].lower() == "time":
            ref = np.mean(data["input"], axis=0)
            trange = data["input"][0].time_axis() <= self.parameters["tmax"]
            for d in data["input"]: metric.append(np.sum((d[trange] - ref[trange])**2))
        elif self.parameters["domain"].lower().startswith("freq"):
            specs = [d.spectrum() for d in data["input"]]
            ref = np.mean(specs, axis=0)
            for d in data["input"]: metric = np.sum((s - ref)**2 for s in specs)
        self.zscores = (metric - np.mean(metric)) / np.std(metric)
        mask = np.abs(self.zscores) < self.parameters["stdDevThreshold"]
        for i, d in enumerate(data["input"]):
            if mask[i]: output.append(d)
        data["output"] = output