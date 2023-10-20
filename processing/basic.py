import ProcessingStep as ps
import suspect
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

class FreqAlignment(ps.ProcessingStep):
    def process(self, data):
        output = [data[0]]
        for d in data:
            output.append(suspect.processing.frequency_correction.correct_frequency_and_phase(d, data[0]))
        self.processedData = output
        return self.processedData
    
    def plot(self, canvas):
        ax = canvas.figure.add_subplot(1, 2, 1)
        ax.plot(self.processedData[0].time_axis(), abs(self.processedData[0]))
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Signal Intensity')
        ax.set_title("Reference")
        ax = canvas.figure.add_subplot(1, 2, 2)
        ax.plot(self.processedData[1].time_axis(), abs(self.processedData[1]))
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Signal Intensity')
        ax.set_title("Aligned")
        canvas.draw()
