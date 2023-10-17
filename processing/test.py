import ProcessingStep as ps

# test classes
class Step1(ps.ProcessingStep):
    def __init__(self):
        super().__init__({"param1": 1, "param2": 2})

class Step2(ps.ProcessingStep):
    def __init__(self):
        super().__init__({"param1": 1, "param2": 2})
            