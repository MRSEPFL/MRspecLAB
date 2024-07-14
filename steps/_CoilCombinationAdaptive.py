import numpy as np

# translated from FID-A code
def estimate_csm(data):
    ncoils = data.shape[0]
    s_raw = data / np.sqrt(np.sum(data * np.conj(data), 0))
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

def combine_channels(data):
        ref = data[:, 0]
        phase = np.exp(-1j*np.angle(ref))
        ref = ref * phase
        csm = estimate_csm(ref)
        csm = np.array(csm[0][0])
        csmsq = np.sum(csm * np.conj(csm), 0)
        csm[csm < np.finfo(float).eps] = 1
        output = []
        for i in range(0, data.shape[-1]):
            ref = data[:, i] * phase
            output.append(np.sum(np.conj(csm) * ref, 0) / csmsq)
        return data.inherit(np.array(output))