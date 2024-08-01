import numpy as np
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
    return output

# adapted from suspect.io.lcmodel.write_all_files because it unnecessarily overwrites entries
def save_control(filepath, params):
    with open(filepath, 'wt') as fout:
        fout.write(" $LCMODL\n")
        fout.write(" KEY = 123456789\n")
        for key, value in params.items():
            if isinstance(value, str):
                value = "'{0}'".format(value)
            elif isinstance(value, bool):
                value = 'T' if value else 'F'
            elif isinstance(value, tuple):
                value = str(value).strip("()").strip("'")
            fout.write(f" {key} = {value}\n")
        fout.write(" $END\n")

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

