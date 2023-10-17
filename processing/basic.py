import ProcessingStep as ps

class Average(ps.ProcessingStep):
    def process(self, data):
        output = data[0]
        for i in range(1, len(data)):
            output += data[i]
        output /= len(data)
        self.processedData = output
        return output