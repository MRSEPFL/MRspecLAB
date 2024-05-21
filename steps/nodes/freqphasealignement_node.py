import api
from ..FreqPhaseAlignment import FreqPhaseAlignment

class FrequencyPhaseAlignementNode(api.Node):
    def __init__(self, nodegraph, id):
        api.Node.__init__(self, nodegraph, id)
        self.label = "Frequency and Phase Alignement"
        self.processing_step=FreqPhaseAlignment()
    
    def EditParametersProcessing(self):
        for key, value in self.properties.items():
            if key == "freqRange":
               self.processing_step.parameters[key] = self.properties[key].value[:-1]
            elif key in self.processing_step.parameters:
                self.processing_step.parameters[key] = self.properties[key].value