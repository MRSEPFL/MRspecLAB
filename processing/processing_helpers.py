import numpy as np
from suspect import MRSData

def zero_phase_flip(data: list[MRSData], start=2., end=2.1):
    '''flip spectrum if marked region is negative'''
    testrange = np.where(np.logical_and(start < data[0].frequency_axis_ppm(), end > data[0].frequency_axis_ppm()))
    if len(testrange) == 0: return
    output = data.copy()
    for i in range(len(data)):
        spec = data[i].spectrum()[testrange]
        if np.mean(spec) < 0:
            output[i] = data[i].adjust_phase(np.pi)
    return output