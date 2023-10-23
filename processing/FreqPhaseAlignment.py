import ProcessingStep as ps
import suspect
import numpy as np

class FreqPhaseAlignment(ps.ProcessingStep):
    def __init__(self):
        super().__init__({"freqRange": None, "median": True})
        self.saveInput = True # necessary for plotting
        self.saveOutput = True
    
    def process(self, data):
        if (type(self.parameters["freqRange"]) is not tuple): freqRange = None
        elif len(self.parameters["freqRange"]) != 2: freqRange = None
        else: freqRange = self.parameters["freqRange"]
        if self.parameters["median"]:
            target = data[0].inherit(np.median(data, axis=0))
        else:
            target = data[0]
        freqShifts = []
        phaseShifts = []
        output = []
        for d in data:
            # output.append(suspect.processing.frequency_correction.correct_frequency_and_phase(d, data[0]))
            freqShift, phaseShift = suspect.processing.frequency_correction.spectral_registration(d, target, frequency_range=freqRange)
            freqShifts.append(freqShift)
            phaseShifts.append(phaseShift)
            output.append(d.adjust_frequency(-freqShift).adjust_phase(-phaseShift))
        self.freqShifts = freqShifts
        self.phaseShifts = phaseShifts
        return output

    def plot(self, canvas):
        canvas.figure.suptitle(self.__class__.__name__)
        ax = canvas.figure.add_subplot(2, 2, 1)
        for d in self.inputData:
            ax.plot(d.frequency_axis_ppm(), d.spectrum())
        ax.set_xlabel('Frequency (ppm)')
        ax.set_ylabel('Amplitude')
        ax.set_title("Input")
        ax = canvas.figure.add_subplot(2, 2, 2)
        for d in self.outputData:
            ax.plot(d.frequency_axis_ppm(), d.spectrum())
        ax.set_xlabel('Frequency (ppm)')
        ax.set_ylabel('Amplitude')
        ax.set_title("Output")
        ax = canvas.figure.add_subplot(2, 2, 3)
        ax.plot(self.freqShifts)
        ax.set_xlabel('Index')
        ax.set_ylabel('Frequency shift (Hz)')
        ax.set_title("Frequency shifts")
        ax = canvas.figure.add_subplot(2, 2, 4)
        ax.plot(self.phaseShifts)
        ax.set_xlabel('Index')
        ax.set_ylabel('Phase shift (rad)')
        ax.set_title("Phase shifts")
        canvas.figure.tight_layout()
        canvas.draw()