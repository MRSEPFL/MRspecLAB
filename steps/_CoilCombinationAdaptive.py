# this file exists to allow coil combination in MRSviewer without also including the nodegraph libraries
import numpy as np
from processing.processing_helpers import zero_phase_flip

# translated from FID-A code
def estimate_csm(data):
    ncoils = data.shape[0]
    s_raw = np.array(data) / np.sqrt(np.sum(data * np.conj(data), 0))
    Rs = np.zeros((ncoils, ncoils), dtype=complex)
    for i in range(0, ncoils):
        for j in range(0, i):
            Rs[i, j] = s_raw[i] * np.conj(s_raw[j])
            Rs[j, i] = np.conj(Rs[i, j])
        Rs[i, i] = s_raw[i] * np.conj(s_raw[i])
    csm, _ = eig_power(Rs)
    return csm

def eig_power(R):
    R = np.array([[R]])
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

def coil_combination_adaptive(data):
    if data["wref"] is not None:
        ref = data["wref"][:, 1] # 2nd timepoints of all coils of the water reference
    else: ref = data["input"][0][:, 1] # 2nd timepoints of all coils of the first fid
    phase = np.exp(-1j*np.angle(ref))
    csm = np.array(estimate_csm(ref * phase)[0][0])
    csmsq = np.sum(csm * np.conj(csm), 0)
    csm[csm < np.finfo(float).eps] = 1
    for d in data["input"]:
        output = []
        for i in range(0, d.shape[-1]):
            output.append(np.sum(np.conj(csm) * d[:, i] * phase, 0) / csmsq)
        data["output"].append(d.inherit(np.array(output)))
    data["output"] = zero_phase_flip(data["output"])
    if data["wref"] is not None:
        output = []
        for i in range(0, data["wref"].shape[-1]):
            output.append(np.sum(np.conj(csm) * data["wref"][:, i] * phase, 0) / csmsq)
        data["wref_output"] = data["wref"].inherit(np.array(output))
        data["wref_output"] = zero_phase_flip([data["wref_output"]])[0]