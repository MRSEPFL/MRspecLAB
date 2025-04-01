import numpy as np
<<<<<<< HEAD
import nibabel as nib
import json
import numpy as np
import os
=======
>>>>>>> dfaee40a8dbd9a7675ff712b6626c00424e81f60
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
<<<<<<< HEAD
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

=======
    file = open(filepath, "r")
    lines = file.readlines()
    file.close()
    output = {}
    for line in lines:
        line = line.strip(" \n")
        if line == "" or line.startswith("$"): continue
        line = line.split("=")
        line[0] = line[0].strip(" ")
        line[1] = line[1].strip(" ")
        if line[1] == "T":
            output[line[0]] = True
        elif line[1] == "F":
            output[line[0]] = False
        elif line[1].startswith("'") and line[1].endswith("'"):
            output[line[0]] = line[1].strip("'")
        elif line[1].strip("-").isdigit():
            output[line[0]] = int(line[1])
        elif line[1].strip("-").replace(".", "", 1).isdigit():
            output[line[0]] = float(line[1])
        elif line[1].replace("-", "").replace(".", "").replace(",", "").isdigit():
            output[line[0]] = tuple(map(float, line[1].split(",")))
        else:
            output[line[0]] = line[1]
>>>>>>> dfaee40a8dbd9a7675ff712b6626c00424e81f60
    return output

# adapted from suspect.io.lcmodel.write_all_files because it unnecessarily overwrites entries
def save_control(filepath, params):
    with open(filepath, 'wt') as fout:
        fout.write(" $LCMODL\n")
<<<<<<< HEAD
        #fout.write(" KEY = 123456789\n")
=======
        fout.write(" KEY = 123456789\n")
>>>>>>> dfaee40a8dbd9a7675ff712b6626c00424e81f60
        for key, value in params.items():
            if isinstance(value, str):
                value = "'{0}'".format(value)
            elif isinstance(value, bool):
                value = 'T' if value else 'F'
            elif isinstance(value, tuple):
                value = str(value).strip("()").strip("'")
            fout.write(f" {key} = {value}\n")
        fout.write(" $END\n")

<<<<<<< HEAD
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
        "Sequence": seq,
    }
    
    # Convert metadata to JSON string and then encode to bytes
    json_metadata = json.dumps(metadata).encode('utf-8')
    
    # Create a NIfTI header extension with code 44 using bytes content
    ext = nib.nifti1.Nifti1Extension(44, json_metadata)
    nifti_img.header.extensions.append(ext)
    
    # Save the image to disk
    nib.save(nifti_img, filepath)

=======
>>>>>>> dfaee40a8dbd9a7675ff712b6626c00424e81f60
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

