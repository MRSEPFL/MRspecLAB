import ProcessingStep as ps
import numpy as np

class Average(ps.ProcessingStep):
    def process(self, data):
        if not isinstance(data, list):
            data = [data]
        if len(data) == 1:
            self.processedData = data[0]
            return data[0]
        temp = data[0]
        output = np.mean(data, axis=0)
        output = temp.inherit(output) # retrieve suspect metadata
        self.processedData = [output]
        return self.processedData