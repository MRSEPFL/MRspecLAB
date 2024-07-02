import os
import numpy as np
import suspect
import matplotlib
from suspect import MRSData
from inout.readcoord import ReadlcmCoord

def plot_mrs(data, figure: matplotlib.figure, title=None):
    if isinstance(data, str):
        filepath = data
        if filepath == "" or not os.path.exists(filepath):
            print(f"File not found:\n\t{filepath}")
            return
        data = suspect.io.load_siemens_dicom(filepath)
        if title is None:
            title = filepath.rsplit(os.path.sep, 1)[1]
    elif isinstance(data, MRSData):
        data = [data]
    elif not (isinstance(data, list) and all(isinstance(d, MRSData) for d in data)):
        print("Invalid data type")
        return
    if title is None: title = "Result"
    # canvas.clear()
    ax = figure.add_subplot(2, 1, 1)
    for d in data:
        ax.plot(d.time_axis(), np.absolute(d))
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Signal Intensity')
    ax = figure.add_subplot(2, 1, 2)
    for d in data:
        ax.plot(d.frequency_axis_ppm(), np.real(d.spectrum()))
    ax.set_xlabel('Chemical shift (ppm)')
    ax.set_ylabel('Amplitude')
    ax.set_xlim((np.max(d.frequency_axis_ppm()), np.min(d.frequency_axis_ppm())))
    figure.suptitle(title)
    figure.tight_layout()

def plot_coord(lcmdata, figure: matplotlib.figure, title=None):
    if isinstance(lcmdata, str):
        filepath = lcmdata
        if filepath == "" or not os.path.exists(filepath):
            print(f"File not found:\n\t{filepath}")
            return
        lcmdata = ReadlcmCoord(filepath)
        if title is None: title = filepath
    elif not isinstance(lcmdata, dict):
        print("Invalid data type")
        return
    if title is None: title = ".coord file"
    
    # canvas.clear()
    ax = figure.add_subplot(1, 1, 1)
    
    def getOffset(data):
        return 1.1 * max(data) - min(data)
    
    ax.plot(lcmdata['ppm'], lcmdata['residue'], 'b-')
    ax.text(4.25, np.mean(lcmdata["residue"]), "Residue", rotation=0, va='center', ha='right', color='b')
    
    specHeight = max(getOffset(lcmdata['spec']), getOffset(lcmdata['fit']))
    offset = specHeight
    ax.plot(lcmdata['ppm'], [x - offset for x in lcmdata['spec']], 'k-', label="Spectrum")
    ax.plot(lcmdata['ppm'], [x - offset for x in lcmdata['fit']], 'r-', label="Fit")
    ax.text(4.25, np.mean(lcmdata["fit"]) - offset, "Fit", rotation=0, va='center', ha='right', color='r')

    offset += getOffset(lcmdata['baseline'])
    ax.plot(lcmdata['ppm'], [x - offset for x in lcmdata['baseline']], 'b-', label="Baseline")
    ax.text(4.25, np.mean(lcmdata["baseline"]) - offset, "Baseline", rotation=0, va='center', ha='right', color='b')

    offset += getOffset(lcmdata['subspec'][0])
    for i, (metab, subspec) in enumerate(zip(lcmdata['metab'], lcmdata['subspec'])):
        ax.plot(lcmdata['ppm'], [x - offset for x in subspec], 'k-', label=metab)
        ax.text(4.25, -offset, metab, rotation=0, va='center', ha='right', color='k')
        offset += 0.1 * specHeight

    ax.set_xlabel('ppm')
    ax.set_xlim((4.2, 1))
    ax.get_yaxis().set_visible(False)
    
    figure.suptitle(title)
    figure.tight_layout()