import numpy as np
import nibabel as nib
import json
import numpy as np
import os
import sys
import shutil
import glob
from interface import utils
import subprocess
# from spec2nii.other_formats import lcm_raw

# adapted from suspect.io.lcmodel.save_raw because it gets SEQ errors
def save_raw(filepath, data, seq="PRESS"):
    with open(filepath, 'w') as fout:
        fout.write(" $SEQPAR\n")
        fout.write(" ECHOT = {}\n".format(data.te))
        fout.write(" HZPPPM = {}\n".format(data.f0))
        fout.write(f" SEQ = {seq}\n")
        fout.write(" $END\n")
        fout.write(" $NMID\n")
        fout.write(" FMTDAT = '(2E15.6)'\n")
        if data.transform is not None: fout.write(" VOLUME = {}\n".format(data.voxel_volume() * 1e-3))
        # else: print("Saving LCModel data without a transform, using default voxel volume of 1ml")
        fout.write(" $END\n")
        for point in np.nditer(data, order='C'):
            fout.write("  {0: 4.6e}  {1: 4.6e}\n".format(float(point.real), float(point.imag)))

def read_control(filepath):
    output = {}
    try:
        with open(filepath, "r") as file:
            lines = file.readlines()
    except Exception as e:
        utils.log_error(f"Failed to open CONTROL file {filepath}: {e}")
        return output  # Return empty dict on failure

    for line in lines:
        line = line.strip()
        if not line or line.startswith("$"):
            continue  # Skip empty lines and comments

        if '=' not in line:
            utils.log_warning(f"Malformed line in CONTROL file: {line}")
            continue  # Skip malformed lines

        key, value = line.split("=", 1)
        key = key.strip().upper()  # Ensure keys are uppercase
        value = value.strip()

        # Handle boolean values
        if value == "T":
            output[key] = True
        elif value == "F":
            output[key] = False
        # Handle quoted strings
        elif value.startswith("'") and value.endswith("'"):
            output[key] = value.strip("'")
        else:
            # Attempt to parse numerical values
            try:
                if ',' in value:
                    # Assume it's a tuple of floats
                    tuple_vals = tuple(map(float, value.split(",")))
                    output[key] = tuple_vals
                else:
                    # Try to convert to int
                    output[key] = int(value)
            except ValueError:
                try:
                    # Try to convert to float (handles scientific notation)
                    output[key] = float(value)
                except ValueError:
                    # Leave as string if all conversions fail
                    output[key] = value

    return output

# adapted from suspect.io.lcmodel.write_all_files because it unnecessarily overwrites entries
def save_control(filepath, params):
    with open(filepath, 'wt') as fout:
        fout.write(" $LCMODL\n")
        #fout.write(" KEY = 123456789\n")
        for key, value in params.items():
            if isinstance(value, str):
                value = "'{0}'".format(value)
            elif isinstance(value, bool):
                value = 'T' if value else 'F'
            elif isinstance(value, tuple):
                value = str(value).strip("()").strip("'")
            fout.write(f" {key} = {value}\n")
        fout.write(" $END\n")

def save_nifti(filepath, data, seq="PRESS"):
    # Convert to complex array if not already
    complex_array = np.asarray(data, dtype=np.complex64)
    
    # Separate real and imaginary parts
    real_part = np.real(complex_array)
    imag_part = np.imag(complex_array)
    
    # Stack as two rows: real part on top, imaginary part on bottom
    combined_data = np.vstack([real_part, imag_part])
    
    # Add a third dimension so the final shape is (2, n, 1)
    combined_data = combined_data[..., np.newaxis]
    
    # Create an identity affine (update if you have spatial info)
    affine = np.eye(4)
    
    # Create NIfTI image
    nifti_img = nib.Nifti1Image(combined_data, affine)
    
    # Update header with a simple description
    hdr = nifti_img.header
    desc = f"Sequence={seq}, TE={data.te}, f0={data.f0} Hz, points={len(data)}, mode=2D"
    hdr['descrip'] = desc.encode('utf-8')
    


    # Create metadata dictionary
    metadata = {
        "SpectrometerFrequency": [data.f0],
        "EchoTime": data.te,
        "RepetitionTime": getattr(data, 'tr', None),
        "ResonantNucleus": [getattr(data, 'nucleus', "unknown")],
        "ResonantNucleus": nucleus,
        "Sequence": seq,
    }
    
    # Convert metadata to JSON string and then encode to bytes
    json_metadata = json.dumps(metadata).encode('utf-8')
    
    # Create a NIfTI header extension with code 44 using bytes content
    ext = nib.nifti1.Nifti1Extension(44, json_metadata)
    nifti_img.header.extensions.append(ext)
    
    # Save the image to disk
    nib.save(nifti_img, filepath)

def save_nifti_spec2nii(filepath, data, nucleus = 'Unknown', seq="PRESS"):
    """
    Save a NIfTI file using spec2nii's raw conversion from an LCModel .RAW file.
    
    Parameters:
      filepath (str): Path to the .RAW file.
      data: A data object with header info (e.g. f0, te, nucleus, dt, bandwidth, etc.).
      seq (str): The acquisition sequence identifier.
    
    Returns:
      The path to the generated NIfTI file, or None on error.
    """
    out_dir = os.path.dirname(filepath)
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    
    # Retrieve header information from the data object.

    #nucleus = getattr(data, "nucleus", "unknown")  # e.g., "1H" or "31P"
    f0 = getattr(data, "f0", None)  # central frequency in Hz
    imagingfreq = str(f0 / 1e6) if f0 is not None else None  # convert to MHz
    
    # Retrieve bandwidth; if not present, try computing it from dt.
    bandwidth = getattr(data, "bandwidth", None)
    if bandwidth is None:
        dt = getattr(data, "dt", None)
        if dt is not None and dt > 0:
            bandwidth = 1.0 / dt
            utils.log_debug(f"Computed bandwidth from dt: {bandwidth} Hz")
        else:
            utils.log_error("Neither bandwidth nor a valid dt (dwell time) found in data.")
            return None

    # First try to find spec2nii in PATH.
    spec2nii_exe = shutil.which("spec2nii")
    
    # If not found, manually search in sys.prefix\Scripts.
    if spec2nii_exe is None:
        scripts_dir = os.path.join(sys.prefix, "Scripts")
        candidates = glob.glob(os.path.join(scripts_dir, "spec2nii*"))
        if candidates:
            spec2nii_exe = candidates[0]
        else:
            utils.log_error("spec2nii executable not found in PATH or in " + scripts_dir)
            return None

    # Build the spec2nii command using the "raw" subcommand.
    cmd = [
        spec2nii_exe, "raw",
        "-n", nucleus,
        "-j",
        "-f", base_name,
        "-o", out_dir,
        filepath
    ]
    if imagingfreq:
        cmd.extend(["-i", imagingfreq])
    if bandwidth:
        cmd.extend(["-b", str(bandwidth)])
    
    utils.log_debug("Running spec2nii command:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        utils.log_error(f"spec2nii conversion failed for {filepath}: {e}")
        return None
        
    # Search for the resulting NIfTI file (either .nii or .nii.gz) in out_dir.
    for f in os.listdir(out_dir):
        if f.startswith(base_name) and (f.endswith(".nii") or f.endswith(".nii.gz")):
            return os.path.join(out_dir, f)
    
    utils.log_error(f"No NIfTI file found after spec2nii conversion for {filepath}")
    return None

# def raw_to_nifti
#     rawpath = os.path.join(self.workpath, "result.RAW")
#     niftipath = os.path.join(self.workpath, "result.nii.gz")
#     save_raw(rawpath, result, seq=self.sequence)
#     class Args:
#         pass
#     args = Args()
#     args.file = rawpath
#     args.fileout = niftipath
#     args.bandwidth = 1 / result.dt
#     args.nucleus = nucleus
#     args.imagingfreq = result.f0
#     args.affine = None
#     imageOut, _ = lcm_raw(args)
#     imageOut[0].save(niftipath) # nifti

