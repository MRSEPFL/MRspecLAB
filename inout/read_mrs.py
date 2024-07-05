import os
import numpy
import mapvbvd
import suspect.io
import pydicom.dicomio
from suspect import MRSData
from suspect.io._common import complex_array_from_iter
from suspect.io.twix import calculate_orientation
from suspect._transforms import rotation_matrix
from .readheader import DataReaders

def loadFile(filepath):
    header = None
    ext = os.path.splitext(filepath)[1][1:].lower()
    if ext == "ima":
        data = suspect.io.load_siemens_dicom(filepath)
        header, _ = DataReaders().siemens_ima(filepath, None)
    if ext == "dcm":
        data = load_dicom(filepath) # suspect's load_dicom doesn't work
        header, _ = DataReaders().siemens_ima(filepath, None)
    elif ext == "dat":
        data = loadVBVD(filepath) # coils not combined
        header, _ = DataReaders().siemens_twix(filepath, None)
    elif ext == "sdat":
        data = suspect.io.load_sdat(filepath, None) # should find .spar
        spar = filepath.lower()[:-5] + ".spar"
        if os.path.exists(spar):
            header, _ = DataReaders().philips_spar(spar, None)
    elif ext == "rda":
        data, header = load_rda(filepath) # no rda in DataReaders; we only need Sequence and Nucleus for processing
    else:
        return None, None, None, None
    vendor = None
    if ext in ["ima", "dat"]: vendor = "siemens"
    elif ext == "sdat": vendor = "philips"
    return data, header, ext, vendor

# adapted from suspect.io.load_twix to use mapVBVD for newer Siemens formats
def loadVBVD(filepath):
    twixobj = mapvbvd.mapVBVD(filepath, quiet=True)
    if isinstance(twixobj, list):
        if len(twixobj) == 1: twixobj = twixobj[0]
        if len(twixobj) == 2: twixobj = twixobj[1] # twixobj[0] is reference noise
        else: raise ValueError("Multiple acquisitions found in VBVD file.")
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

# adapted from suspect._transforms
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

# adapted from suspect.io.load_dicom
def load_dicom(filename):
    dataset = pydicom.dicomio.read_file(filename)
    sw = dataset[0x0018, 0x9052].value
    dt = 1.0 / sw
    f0 = dataset[0x0018, 0x9098].value
    te = float(dataset[0x5200, 0x9229][0][0x0018, 0x9114][0][0x0018, 0x9082].value)
    tr = float(dataset[0x5200, 0x9229][0][0x0018, 0x9112][0][0x0018, 0x0080].value)
    ppm0 = dataset[0x0018, 0x9053].value
    rows = dataset[0x0028, 0x0010].value
    cols = dataset[0x0028, 0x0011].value
    frames = dataset[0x0028, 0x0008].value
    num_second_spectral = dataset[0x0028, 0x9001].value
    num_points = dataset[0x0028, 0x9002].value
    data_shape = [frames, rows, cols, num_second_spectral, 4*num_points]
    data_iter = iter(dataset[0x5600, 0x0020])
    data = complex_array_from_iter(data_iter, shape=data_shape, chirality=-1)
    return MRSData(data, dt, f0=f0, te=te, tr=tr, ppm0=ppm0)

def load_rda(filepath):
    header = {}
    dt = None
    tr = None
    te = None
    f0 = None
    vector_size = None
    filebytes = open(filepath, 'rb').read()
    headerend = filebytes.find(">>> End of header <<<".encode('utf-8')) + 21
    headerstr = filebytes[:headerend].decode('utf-8')
    data = filebytes[headerend:]
    data = data[len(data) % 16:]
    for line in headerstr.split('\n'):
        if line.startswith('Nucleus: '):
            header["Nucleus"] = line.split(':')[1].strip()
            continue
        if line.startswith('SequenceName: '):
            header["Sequence"] = line.split(':')[1].strip()
            continue
        if line.startswith('TR: '):
            tr = float(line.split(':')[1].strip()) # ms
            continue
        if line.startswith('TE: '):
            te = float(line.split(':')[1].strip()) # ms
            continue
        if line.startswith('DwellTime: '):
            dt = float(line.split(':')[1].strip()) * 1e-6 # us
            continue
        if line.startswith('MRFrequency: '):
            f0 = float(line.split(':')[1].strip().replace(',', '.')) # MHz
            continue
        if line.startswith('VectorSize: '):
            vector_size = int(line.split(':')[1].strip())
            continue
    data = numpy.frombuffer(data, dtype=numpy.float64)
    data = data[::2] + 1j * data[1::2]
    # assert data.size == vector_size
    return MRSData(data, dt, f0=f0, te=te, tr=tr), header