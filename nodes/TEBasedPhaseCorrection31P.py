import processing.api as api
import numpy as np
import scipy
import copy
from interface import utils

class TEBasedPhaseCorrecton31P(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "TE Based Phase Correction (31P)",
            "author": "CIBM",
            "description": (
                "Performs frequency and phase alignment for 31P spectra, including "
                "automatic one-time first-order phase correction using TE (either from "
                "header or user-specified), moving the peak to 0 ppm, and supporting "
                "both single voxel and CSI multivoxel data."
            )
        }

        self.parameters = [
            # Zero-padding factor
            api.IntegerProp(
                idname="zp_factor",
                default=2,
                min_val=0,
                max_val=10,
                fpb_label="Zero-padding factor"
            ),
            # Line-broadening factor (Lorentzian)
            api.IntegerProp(
                idname="lb_factor",
                default=5,
                min_val=0,
                max_val=50,
                fpb_label="Line-broadening factor (e^(-f*pi))"
            ),
            # Toggle frequency alignment
            api.ChoiceProp(
                idname="alignFreq",
                default="True",
                choices=["True", "False"],
                fpb_label="Perform frequency alignment"
            ),
            # Toggle zero-order phase alignment
            api.ChoiceProp(
                idname="alignPhase",
                default="True",
                choices=["True", "False"],
                fpb_label="Perform zero-order phase alignment"
            ),

            # New param: useHeaderTE
            api.ChoiceProp(
                idname="useHeaderTE",
                default="True",
                choices=["True", "False"],
                fpb_label="Use Echo Time from header?"
            ),

            # Instead of FloatProp, we use StringProp for manual TE
            api.StringProp(
                idname="manualTE",
                default="0.0035",  # user enters as string
                fpb_label="User-specified Echo Time (s)"
            ),

            # Reference range for alignment (ppm)
            api.VectorProp(
                idname="freqRange",
                default=(-0.3, 0.3, 0),
                labels=("Lower Bound (ppm)", "Higher Bound (ppm)"),
                min_vals=(-10, -10, 0),
                max_vals=(10, 10, 0),
                fpb_label="Reference peak range (ppm)"
            ),

            # Determine how the target spectrum is selected
            api.ChoiceProp(
                idname="median",
                default="True",
                choices=["True", "False"],
                fpb_label="Set target to median of input data (SVS only)"
            ),
            api.StringProp(
                idname="target",
                default="0",
                fpb_label="Set target to index of input data (if not median; starts at 0, SVS only)"
            )
        ]
        
        super().__init__(nodegraph, id)

    def process(self, data):
        """
        Outline:
          1) Determine if data is single-voxel (SVS) or multivoxel (CSI) by checking the header.
          2) Zero-pad and perform line broadening.
          3) ALWAYS perform first-order phase correction once:
               - If useHeaderTE=True => read from header TE (converted to seconds)
               - Else => parse manualTE (string -> float)
          4) Build the target spectrum:
             - For SVS: use median or user-specified target.
             - For CSI: choose the voxel with the highest spectral area.
          5) For the target, apply the first-order correction and then perform peak-max
             zero-order phase correction.
          6) Move the target peak to 0 ppm: determine the frequency shift from the target's
             peak position and apply it to the target.
          7) For each dataset (or voxel), perform LS optimization (only on frequency and 0th-order phase)
             using an initial guess that includes the target frequency shift.
          8) Output the final aligned data.
        """
        raw_data = data["input"]

        do_freq  = (self.get_parameter("alignFreq") == "True")
        do_phase = (self.get_parameter("alignPhase") == "True")

        # Determine TE source
        use_header_te_str = self.get_parameter("useHeaderTE")
        use_header_te = (use_header_te_str == "True")
        manual_te_str = self.get_parameter("manualTE")
        try:
            user_te = float(manual_te_str)
        except ValueError:
            user_te = 0.0
            utils.log_error("Warning: manualTE was not a valid float. Using 0.0 s.")

        # Check if this is CSI (multivoxel) data by trying to read header dimensions.
        try:
            header = data["header"]
            xdim = header["CSIMatrix_Size[0]"]
            ydim = header["CSIMatrix_Size[1]"]
            zdim = header["CSIMatrix_Size[2]"]
            isCSI = True
        except Exception:
            isCSI = False

        # 1) Prepare working copy(s)
        if isCSI:
            # For CSI, assume raw_data is a multidimensional structure.
            _data = copy.deepcopy(raw_data)
        else:
            _data = [d.copy() for d in raw_data]

        # 2) Zero-padding
        zp_factor = self.get_parameter("zp_factor")
        if zp_factor != 0:
            if isCSI:
                # For CSI data, iterate over voxels.
                for ix in range(xdim):
                    for iy in range(ydim):
                        for iz in range(zdim):
                            d = _data[ix][iy][iz]
                            pad_len = int(np.floor(len(d) * zp_factor))
                            padding = np.zeros(pad_len, dtype=d.dtype)
                            _data[ix][iy][iz] = d.inherit(np.concatenate((d, padding), axis=None))
            else:
                new_data = []
                for d in _data:
                    pad_len = int(np.floor(len(d) * zp_factor))
                    padding = np.zeros(pad_len, dtype=d.dtype)
                    new_data.append(d.inherit(np.concatenate((d, padding), axis=None)))
                _data = new_data

        # 2b) Line broadening
        lb_factor = self.get_parameter("lb_factor")
        if lb_factor != 0:
            if isCSI:
                for ix in range(xdim):
                    for iy in range(ydim):
                        for iz in range(zdim):
                            d = _data[ix][iy][iz]
                            time_axis = d.time_axis()
                            exp_weight = np.exp(-time_axis * np.pi * lb_factor)
                            _data[ix][iy][iz] = d.inherit(d * exp_weight)
            else:
                time_axis = _data[0].time_axis()
                exp_weight = np.exp(-time_axis * np.pi * lb_factor)
                lb_data = []
                for d in _data:
                    lb_data.append(d.inherit(d * exp_weight))
                _data = lb_data

        # Keep a copy for plotting (for both SVS and CSI, store the pre-aligned data)
        self.freq_in = _data

        # Define function to compute first-order phase (in rad/Hz) from TE
        def get_phase_from_TE(d):
            # Multiply TE (in ms) by 1e-3 to obtain seconds.
            if use_header_te and hasattr(d, "TE") and (d.TE is not None):
                return 2 * np.pi * d.TE * 1e-3
            else:
                return 2 * np.pi * user_te * 1e-3

        # 3) Apply first-order correction once to all data
        self.firstOrderPhases = []
        if isCSI:
            for ix in range(xdim):
                for iy in range(ydim):
                    for iz in range(zdim):
                        d = _data[ix][iy][iz]
                        p1 = get_phase_from_TE(d)
                        self.firstOrderPhases.append(p1)  # (for plotting, order may be arbitrary)
                        _data[ix][iy][iz] = d.adjust_phase(0.0, first_phase=-p1)
        else:
            corrected_data = []
            for d in _data:
                p1 = get_phase_from_TE(d)
                self.firstOrderPhases.append(p1)
                corrected_data.append(d.adjust_phase(0.0, first_phase=-p1))
            _data = corrected_data

        # 4) Build target spectrum
        if isCSI:
            # For multivoxel, choose the voxel with the highest spectral area.
            target_voxel = _data[0][0][0]
            highest_spec_area = np.sum(np.real(target_voxel.spectrum()))
            for ix in range(xdim):
                for iy in range(ydim):
                    for iz in range(zdim):
                        d = _data[ix][iy][iz]
                        spec_area = np.sum(np.real(d.spectrum()))
                        if spec_area > highest_spec_area:
                            highest_spec_area = spec_area
                            target_voxel = d
            self.target = target_voxel.copy()
        else:
            # For SVS, use median or user-specified target.
            if self.get_parameter("median") == "True":
                arr = np.stack([d for d in _data], axis=0)
                median_spectrum = np.median(arr, axis=0)
                self.target = _data[0].inherit(median_spectrum)
            else:
                idx = int(self.get_parameter("target"))
                if 0 <= idx < len(_data):
                    self.target = _data[idx].copy()
                else:
                    self.target = _data[0].copy()

        # 5) Peak-max zero-order phase correction on the target
        ppm_bounds = self.get_parameter("freqRange")[:-1]  # (lower, upper)
        lower_ppm, upper_ppm = ppm_bounds

        def peak_max_zero_phase(data_obj, ppm1, ppm2):
            candidate_phases_deg = np.arange(-180, 181, 3)
            freq_ppm = data_obj.frequency_axis_ppm()
            idxs = np.where((freq_ppm >= ppm1) & (freq_ppm <= ppm2))[0]
            if len(idxs) == 0:
                idxs = np.arange(len(freq_ppm))
            best_phase_deg = 0.0
            best_peak = -np.inf
            for ph_deg in candidate_phases_deg:
                trial = data_obj.adjust_phase(-np.deg2rad(ph_deg))
                spec = np.real(trial.spectrum())
                peak_val = np.max(spec[idxs])
                if peak_val > best_peak:
                    best_peak = peak_val
                    best_phase_deg = ph_deg
            return best_phase_deg

        if do_phase:
            best_phase_deg = peak_max_zero_phase(self.target, lower_ppm, upper_ppm)
            self.target = self.target.adjust_phase(-np.deg2rad(best_phase_deg))
        else:
            best_phase_deg = 0.0

        # 6) Move the target peak to 0 ppm
        spec = np.real(self.target.spectrum())
        freq_axis = self.target.frequency_axis_ppm()
        max_index = np.argmax(spec)
        peak_ppm = freq_axis[max_index]
        # Compute frequency shift in Hz (target.f0 is the Larmor frequency)
        freq_shift_Hz = -peak_ppm * self.target.f0
        self.target = self.target.adjust_frequency(-freq_shift_Hz)

        # 7) Now perform LS optimization (only on frequency and 0th-order phase)
        # Compute spectral weights based on the target's frequency axis.
        freq_array = self.target.frequency_axis()
        freqRange_Hz = [self.target.ppm_to_hertz(ppm) for ppm in ppm_bounds]
        freqRange_Hz.sort()
        spectral_weights_global = np.logical_and(
            freq_array >= freqRange_Hz[0],
            freq_array <= freqRange_Hz[1]
        )

        # Define residual function
        def residual(params, dataset, spectral_weights):
            idx = 0
            temp = dataset.copy()
            if do_freq:
                fs = params[idx]
                idx += 1
                temp = temp.adjust_frequency(-fs)
            else:
                fs = 0.0
            if do_phase:
                zp = params[idx]
                idx += 1
                temp = temp.adjust_phase(-zp)
            else:
                zp = 0.0
            diff_data = temp - self.target
            spec_diff = diff_data.spectrum()
            weighted_spectrum = spec_diff * spectral_weights
            weighted_spectrum = weighted_spectrum[weighted_spectrum != 0]
            resid_td = np.fft.ifft(np.fft.ifftshift(weighted_spectrum))
            out_vec = np.concatenate([resid_td.real, resid_td.imag])
            return out_vec

        output = []
        # LS optimization differs for SVS versus CSI
        if not isCSI:
            # For single voxel: iterate over _data (a list)
            for i, d in enumerate(_data):
                guess_list = []
                if do_freq:
                    guess_list.append(freq_shift_Hz)  # initial guess from target frequency shift
                if do_phase:
                    guess_list.append(0.0)
                guess = np.array(guess_list)
                if do_freq or do_phase:
                    out = scipy.optimize.leastsq(residual, guess, args=(d, spectral_weights_global), maxfev=500)
                    pars = out[0]
                    idx_par = 0
                    final_freqShift = pars[idx_par] if do_freq else 0.0
                    if do_freq: idx_par += 1
                    final_zeroPhase = pars[idx_par] if do_phase else 0.0
                else:
                    final_freqShift = 0.0
                    final_zeroPhase = 0.0
                # Apply the corrections to get final aligned dataset.
                aligned = d.copy()
                if do_freq:
                    aligned = aligned.adjust_frequency(-final_freqShift)
                if do_phase:
                    aligned = aligned.adjust_phase(-final_zeroPhase)
                output.append(aligned)
        else:
            # For CSI: iterate over voxels in a triple loop
            output = copy.deepcopy(_data)
            for ix in range(xdim):
                for iy in range(ydim):
                    for iz in range(zdim):
                        voxel = _data[ix][iy][iz]
                        guess_list = []
                        if do_freq:
                            guess_list.append(freq_shift_Hz)
                        if do_phase:
                            guess_list.append(0.0)
                        guess = np.array(guess_list)
                        if do_freq or do_phase:
                            out = scipy.optimize.leastsq(residual, guess, args=(voxel, spectral_weights_global), maxfev=500)
                            pars = out[0]
                            idx_par = 0
                            final_freqShift = pars[idx_par] if do_freq else 0.0
                            if do_freq: idx_par += 1
                            final_zeroPhase = pars[idx_par] if do_phase else 0.0
                        else:
                            final_freqShift = 0.0
                            final_zeroPhase = 0.0
                        corrected_voxel = voxel.copy()
                        if do_freq:
                            corrected_voxel = corrected_voxel.adjust_frequency(-final_freqShift)
                        if do_phase:
                            corrected_voxel = corrected_voxel.adjust_phase(-final_zeroPhase)
                        output[ix][iy][iz] = corrected_voxel
        data["output"] = output

    def plot(self, figure, data):
        """
        Custom plot code.
        """
        figure.suptitle(self.__class__.__name__)
        if isinstance(self.freq_in, list):
            # SVS plotting
            xlim = (
                np.max(self.freq_in[0].frequency_axis_ppm()),
                np.min(self.freq_in[0].frequency_axis_ppm())
            )
            ax = figure.add_subplot(3, 6, (1,3))
            for d in data["input"]:
                ax.plot(d.frequency_axis_ppm(), np.real(d.spectrum()))
            ax.set_xlim(xlim)
            ax.set_title("Input")
            ax = figure.add_subplot(3, 6, (4,6))
            for d in data["output"]:
                ax.plot(d.frequency_axis_ppm(), np.real(d.spectrum()))
            ax.set_xlim(xlim)
            ax.set_title("Aligned Output")
            ax = figure.add_subplot(3, 6, (13,18))
            ax.plot(self.target.frequency_axis_ppm(), np.real(self.target.spectrum()), 'r')
            ax.set_xlim(xlim)
            ax.set_title("Reference Target Spectrum")
            figure.tight_layout()
        else:
            # CSI plotting: show central voxel spectrum from input and output.
            header = data["header"]
            CSIMatrix_Size = [header["CSIMatrix_Size[0]"],
                              header["CSIMatrix_Size[1]"],
                              header["CSIMatrix_Size[2]"]]
            central_idx = (int(CSIMatrix_Size[0]//2), int(CSIMatrix_Size[1]//2), int(CSIMatrix_Size[2]//2))
            ax = figure.add_subplot(1, 2, 1)
            central_input = data["input"][central_idx[0]][central_idx[1]][central_idx[2]]
            ax.plot(central_input.frequency_axis_ppm(), np.real(central_input.spectrum()))
            ax.set_xlabel("ppm")
            ax.set_ylabel("Amplitude")
            ax.set_title("Input central voxel")
            ax = figure.add_subplot(1, 2, 2)
            central_output = data["output"][central_idx[0]][central_idx[1]][central_idx[2]]
            ax.plot(central_output.frequency_axis_ppm(), np.real(central_output.spectrum()))
            ax.set_xlabel("ppm")
            ax.set_ylabel("Amplitude")
            ax.set_title("Output central voxel")
            figure.tight_layout()

api.RegisterNode(TEBasedPhaseCorrecton31P, "TEBasedPhaseCorrecton31P")
