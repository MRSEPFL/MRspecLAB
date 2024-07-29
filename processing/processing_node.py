import matplotlib.figure
import numpy as np
import matplotlib
from processing.api.node import Node, Output
from processing.api.property import TransientsProp

class ProcessingNode(Node):
    def __init__(self, nodegraph, id):
        if self.meta_info is None: self.meta_info = {}
        if "label" not in self.meta_info: self.meta_info["label"] = self.__class__.__name__
        if "author" not in self.meta_info: self.meta_info["author"] = ""
        if "version" not in self.meta_info: self.meta_info["version"] = (0, 0, 0)
        if "category" not in self.meta_info: self.meta_info["category"] = "PROCESSING"
        if "description" not in self.meta_info: self.meta_info["description"] = ""
        if nodegraph is not None:
            Node.__init__(self, nodegraph, id)
        self.defaultParameters = {}
        if hasattr(self, "parameters"):
            for p in self.parameters:
                p.exposed = False
                p.show_p = False
                self.defaultParameters[p.idname] = p.value
        else: self.parameters = []
        self.plotTime = True # set these if you don't override plot()
        self.plotSpectrum = True
        self.plotPPM = True

    def __str__(self) -> str:
        output = self.__class__.__name__ + ":\n"
        if not hasattr(self, "parameters"): return output
        for p in self.parameters:
            output += "- " + p.idname + ": " + str(p.value) + "\n"
        return output
    
    @property
    def NodeMeta(self):
        return self.meta_info

    def NodeInitProps(self):
        transients = TransientsProp(
            idname="in_transients"
        )
        self.NodeAddProp(transients)
        if not hasattr(self, "parameters"): return
        for p in self.parameters: self.NodeAddProp(p)

    def NodeInitOutputs(self):
        self.outputs = {
            "transients": Output(idname="Output", datatype="TRANSIENTS", label="Output")
        }

    def get_parameter(self, key: str):
        return self.properties[key].value
    
    def resetParameters(self):
        if not hasattr(self, "parameters"): return
        for k in self.defaultParameters.keys():
            self.properties[k].value = self.defaultParameters[k]
    
    def process(self, data: dict) -> None: # to override
        data["output"] = data["input"]
        data["wref"] = None # already was None
    
    def plot(self, figure: matplotlib.figure, data: dict) -> None: # can be overridden
        if not self.plotTime and not self.plotSpectrum: return
        if self.plotTime and self.plotSpectrum: sx, sy = 2, 2
        else: sx, sy = 2, 1
        index = 1
        if self.plotTime:
            ax = figure.add_subplot(sx, sy, index)
            self.plotData(ax, data["input"], False)
            ax.set_title("Input")
            ax = figure.add_subplot(sx, sy, index + sy)
            self.plotData(ax, data["output"], False)
            ax.set_title("Output")
            index += 1
        if self.plotSpectrum:
            ax = figure.add_subplot(sx, sy, index)
            self.plotData(ax, data["input"], True)
            ax.set_title("Input")
            ax = figure.add_subplot(sx, sy, index + sy)
            self.plotData(ax, data["output"], True)
            ax.set_title("Output")
        figure.suptitle(self.__class__.__name__)
        figure.tight_layout()

    def plotData(self, ax, data, plotfreq): # helper plotting function
        '''Plot a list of MRSData on axes in time or frequency domain.'''
        if plotfreq:
            if self.plotPPM:
                for d in data:
                    ax.plot(d.frequency_axis_ppm(), np.real(d.spectrum()))
                ax.set_xlabel('Chemical shift (ppm)')
                ax.set_xlim((np.max(d.frequency_axis_ppm()), np.min(d.frequency_axis_ppm())))
            else:
                for d in data:
                    ax.plot(d.frequency_axis(), np.real(d.spectrum()))
                ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Amplitude')
        else:
            for d in data:
                ax.plot(d.time_axis(), np.real(d))
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Intensity')