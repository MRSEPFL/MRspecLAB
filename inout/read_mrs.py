import os
import numpy
import mapvbvd
import suspect.io
from suspect import MRSData
from .readheader import DataReaders

def loadFile(filepath):
    header = None
    ext = os.path.splitext(filepath)[1][1:].lower()
    if ext == "ima":
        data = suspect.io.load_siemens_dicom(filepath)
        header, _ = DataReaders().siemens_ima(filepath, None)
    elif ext == "dat":
        # data = suspect.io.load_twix(filepath)
        data = loadVBVD(filepath)
        header, _ = DataReaders().siemens_twix(filepath, None)
        data = suspect.processing.channel_combination.combine_channels(data) # temporary?
    elif ext == "sdat":
        data = suspect.io.load_sdat(filepath, None) # should find .spar
        spar = filepath.lower()[:-5] + ".spar"
        if os.path.exists(spar):
            header, _ = DataReaders().philips_spar(spar, None)
    else:
        return None, None, None, None
    vendor = None
    if ext == "ima" or "dat": vendor = "siemens"
    elif ext == "sdat": vendor = "philips"
    return data, header, ext, vendor

# adapted from suspect.io.load_twix to use mapVBVD for newer Siemens formats
def loadVBVD(filepath):
    twixobj = mapvbvd.mapVBVD(filepath, quiet=True)
    if isinstance(twixobj, list):
        if len(twixobj) == 1: twixobj = twixobj[0]
        if len(twixobj) == 2: twixobj = twixobj[1] # twixobj[0] is reference noise
        else: raise ValueError("Multiple acquisitions found in VBVD file.")

    # complex data
    data = twixobj.image['']
    data = numpy.squeeze(data)

    # suspect expects data as [Rep, Cha, Col]
    axes = twixobj.image.sqzDims # ['Col', 'Cha', 'Ave', 'Rep'] for example
    target = ['Rep', 'Cha', 'Col']
    inds = [i for i, dim in enumerate(axes) if dim not in target]
    data = numpy.mean(data, axis=tuple(inds))
    axes = [dim for dim in axes if dim in target]
    if 'Rep' not in axes: # happens with water reference
        data = numpy.expand_dims(data, 0)
        axes = ['Rep'] + axes
    data = numpy.transpose(data, (axes.index('Rep'), axes.index('Cha'), axes.index('Col')))

    # parameters
    if "DwellTime" in twixobj.hdr["Config"]:
        dt = twixobj.hdr["Config"]["DwellTime"] * 1e-9 # s to ns
    else:
        dt = twixobj.hdr["Config"]["DwellTimeSig"] * 1e-9 # s to ns
    f0 = twixobj.hdr["Config"]["Frequency"] * 1e-6 # Hz to MHz
    te = float(twixobj.hdr["Meas"]["alTE"].split()[0]) * 1e-3 # us to ms
    tr = float(twixobj.hdr["Meas"]["alTR"].split()[0]) * 1e-3 # us to ms

    transform = get_transform(twixobj)
    metadata = None
    return MRSData(data, dt, f0, te=te, tr=tr, transform=transform, metadata=metadata)

def get_transform(twixobj):
    pos_sag = twixobj.hdr["Config"]["VoI_Position_Sag"]
    pos_cor = twixobj.hdr["Config"]["VoI_Position_Cor"]
    pos_tra = twixobj.hdr["Config"]["VoI_Position_Tra"]
    if pos_sag == '' or pos_cor == '' or pos_tra == '':
        try: # keys may not exist
            pos_sag = twixobj.hdr["MeasYaps"][('sSpecPara', 'sVoI', 'sPosition', 'dCor')]
            pos_cor = twixobj.hdr["MeasYaps"][('sSpecPara', 'sVoI', 'sPosition', 'dSag')]
            pos_tra = twixobj.hdr["MeasYaps"][('sSpecPara', 'sVoI', 'sPosition', 'dTra')]
        except: pass
    if pos_sag == '' or pos_cor == '' or pos_tra == '':
        return None
    
    pos_sag = float(pos_sag)
    pos_cor = float(pos_cor)
    pos_tra = float(pos_tra)
    
    normal_sag = twixobj.hdr["Config"]["VoI_Normal_Sag"]
    normal_cor = twixobj.hdr["Config"]["VoI_Normal_Cor"]
    normal_tra = twixobj.hdr["Config"]["VoI_Normal_Tra"]
    if normal_sag == '' or normal_cor == '' or normal_tra == '':
        try: # keys may not exist
            normal_sag = twixobj.hdr["MeasYaps"][('sSpecPara', 'sVoI', 'sNormal', 'dSag')]
            normal_cor = twixobj.hdr["MeasYaps"][('sSpecPara', 'sVoI', 'sNormal', 'dCor')]
            normal_tra = twixobj.hdr["MeasYaps"][('sSpecPara', 'sVoI', 'sNormal', 'dTra')]
        except: pass
    if normal_sag == '' or normal_cor == '' or normal_tra == '':
        return None
    
    normal_sag = float(normal_sag)
    normal_cor = float(normal_cor)
    normal_tra = float(normal_tra)

    ro_fov = float(twixobj.hdr["Config"]["VoI_RoFOV"])
    pe_fov = float(twixobj.hdr["Config"]["VoI_PeFOV"])
    slice_thickness = float(twixobj.hdr["Config"]["VoI_SliceThickness"])
    in_plane_rot = twixobj.hdr["Config"]["VoI_InPlaneRotAngle"]

    normal_vector = numpy.array([normal_sag, normal_cor, normal_tra])
    if calculate_orientation(normal_vector) == "SAG": x_vector = numpy.array([0, 0, 1])
    else: x_vector = numpy.array([-1, 0, 0])
    orthogonal_x = x_vector - numpy.dot(x_vector, normal_vector) * normal_vector
    orthonormal_x = orthogonal_x / numpy.linalg.norm(orthogonal_x)
    rot_matrix = rotation_matrix(in_plane_rot, normal_vector)
    row_vector = numpy.dot(rot_matrix, orthonormal_x)
    column_vector = numpy.cross(row_vector, normal_vector)
    transform = transformation_matrix(row_vector, column_vector, [pos_sag, pos_cor, pos_tra], [ro_fov, pe_fov, slice_thickness])
    return transform

# taken from suspect._transforms
def calculate_orientation(normal):
    if normal[2] >= normal[1] - 1e-6 and normal[2] >= normal[0] - 1e-6:
        return "TRA"
    elif normal[1] >= normal[0] - 1e-6:
        return "COR"
    return "SAG"

def rotation_matrix(angle, axis):
    c = numpy.cos(angle)
    s = numpy.sin(angle)
    matrix = numpy.zeros((3, 3))
    matrix[0, 0] = c + axis[0] ** 2 * (1 - c)
    matrix[0, 1] = axis[0] * axis[1] * (1 - c) - axis[2] * s
    matrix[0, 2] = axis[0] * axis[2] * (1 - c) + axis[1] * s
    matrix[1, 0] = axis[1] * axis[0] * (1 - c) + axis[2] * s
    matrix[1, 1] = c + axis[1] ** 2 * (1 - c)
    matrix[1, 2] = axis[1] * axis[2] * (1 - c) - axis[0] * s
    matrix[2, 0] = axis[2] * axis[0] * (1 - c) - axis[1] * s
    matrix[2, 1] = axis[2] * axis[1] * (1 - c) + axis[0] * s
    matrix[2, 2] = c + axis[2] ** 2 * (1 - c)
    return matrix

def transformation_matrix(x_vector, y_vector, translation, spacing):
    matrix = numpy.zeros((4, 4), dtype=float) # removed deprecated numpy.float
    matrix[:3, 0] = x_vector
    matrix[:3, 1] = y_vector
    z_vector = numpy.cross(x_vector, y_vector)
    matrix[:3, 2] = z_vector
    matrix[:3, 3] = numpy.array(translation)
    matrix[3, 3] = 1.0

    spacing = list(spacing)
    while len(spacing) < 4:
        spacing.append(1.0)
    for i in range(4):
        for j in range(4):
            matrix[i, j] *= spacing[j]
    return matrix