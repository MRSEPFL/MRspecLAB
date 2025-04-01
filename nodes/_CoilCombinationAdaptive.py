# this file exists to allow coil combination in MRSviewer without also including the nodegraph libraries
import numpy as np
import scipy.linalg as lin
from interface import utils

# translated from FID-A code
def estimate_csm(data):
    s_raw = np.array(data) / np.sqrt(np.sum(data * np.conj(data), 0))
    s_raw = s_raw.reshape((-1, 1))
    Rs = s_raw @ s_raw.conj().T
    csm, _ = eig_power(Rs)
    # s, v = lin.eig(Rs)
    # csm = [[s]]
    return csm

def eig_power(R):
    R = np.array([[R]]) # yay matlab copy-paste
    rows, cols, ncoils = R.shape[0], R.shape[1], R.shape[2]
    N_iterations = 2
    v = np.ones((rows, cols, ncoils), dtype=complex)
    d = np.zeros((rows, cols))
    for i in range(0, N_iterations):
        v = np.sum(R * np.tile(v[..., None], (1, 1, 1, ncoils)), 2)
        d = np.sqrt(np.sum(np.abs(v) ** 2, 2))
        d[d <= np.finfo(float).eps] = np.finfo(float).eps
        v = v / np.tile(d[..., None], (1, 1, ncoils))
    p1 = np.angle(np.conj(v[:, :, 0]))
    v = v * np.tile(np.exp(1j * p1)[..., None], (1, 1, ncoils))
    v = np.conj(v)
    return v, d

def coil_combination_adaptive(data, p=0):
    if p == 0: 
        if (data["input"][0].metadata is not None and 
        "ave_per_rep" in data["input"][0].metadata):
            p = data["input"][0].metadata["ave_per_rep"]
        else: p = 1
    ref = "wref" if "wref" in data and data["wref"] is not None and len(data["wref"]) != 0 else "input"
    if ref == "input": utils.log_warning("No water reference provided, using averaged FIDs as reference")
    ref = np.mean(np.array(data[ref]), 0)[:, 0]
    phase = np.exp(-1j*np.angle(ref))
    csm = np.array(estimate_csm(ref * phase)[0][0])
    csmsq = np.sum(csm * np.conj(csm), 0)
    csm[csm < np.finfo(float).eps] = 1
    output = []
    for d in data["input"]:
        output2 = []
        for i in range(0, d.shape[-1]):
            output2.append(np.sum(np.conj(csm) * d[:, i] * phase, 0) / csmsq)
        output.append(d.inherit(np.array(output2)))
    data["output"] = [output[i].inherit(np.mean(output[i:i+p], 0)) for i in range(0, len(output), p)]
    if "wref" in data and data["wref"] is not None and len(data["wref"]) != 0:
        output = []
        for d in data["wref"]:
            output2 = []
            for i in range(0, d.shape[-1]):
                output2.append(np.sum(np.conj(csm) * d[:, i] * phase, 0) / csmsq)
            output.append(d.inherit(np.array(output2)))
        data["wref_output"] = [output[i].inherit(np.mean(output[i:i+p], 0)) for i in range(0, len(output), p)]