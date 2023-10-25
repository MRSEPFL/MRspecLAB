import os
import numpy as np
import suspect
from suspect import MRSData

def plot_ima(data, canvas, title=None):
    if isinstance(data, str):
        filepath = data
        if filepath == "" or not os.path.exists(filepath):
            print(f"File not found:\n\t{filepath}")
            return
        data = suspect.io.load_siemens_dicom(filepath)
        title = filepath
    elif not isinstance(data, MRSData):
        print("Invalid data type")
        return
    
    if title is None: title = "Result"
    canvas.clear()
    ax = canvas.figure.add_subplot(2, 1, 1)
    ax.plot(data.time_axis(), np.absolute(data))
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Signal Intensity')
    ax = canvas.figure.add_subplot(2, 1, 2)
    ax.plot(data.frequency_axis_ppm(), data.spectrum())
    ax.set_xlabel('Frequency (ppm)')
    ax.set_ylabel('Amplitude')
    canvas.figure.suptitle(title)
    canvas.figure.tight_layout()
    canvas.draw()

def plot_coord(lcmdata, canvas, title=None):
    if isinstance(lcmdata, str):
        filepath = lcmdata
        if filepath == "" or not os.path.exists(filepath):
            print(f"File not found:\n\t{filepath}")
            return
        from readcoord import ReadlcmCoord
        lcmdata = ReadlcmCoord(filepath)
        if title is None: title = filepath
    elif not isinstance(lcmdata, dict):
        print("Invalid data type")
        return
    if title is None: title = ".coord file"
    
    canvas.clear()
    ax = canvas.figure.add_subplot(1, 1, 1)
    
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
    
    canvas.figure.suptitle(title)
    canvas.figure.tight_layout()
    canvas.draw()