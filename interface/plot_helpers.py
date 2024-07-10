import os
import numpy as np
import matplotlib
from suspect import MRSData
from inout.readcoord import ReadlcmCoord

def plot_mrs(data, figure: matplotlib.figure, title=None):
    if isinstance(data, MRSData):
        if len(data.shape) > 1:
            data = [data.inherit(data[i]) for i in range(data.shape[0])]
        else:
            data = [data]
    if not (isinstance(data, list) and all(isinstance(d, MRSData) for d in data)):
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

def estimate_snr(data: MRSData):
    ppms = data.frequency_axis_ppm()
    spec = data.spectrum()
    naapeak = np.max(np.real(spec[np.where(np.logical_and(ppms > 1.8, ppms < 2.2))]))
    noise = np.real(spec[np.where(np.logical_and(ppms > 0, ppms < 0.5))])
    poly = np.polynomial.polynomial.Polynomial.fit(range(len(noise)), noise, 5)
    noise -= poly(range(len(noise)))
    return naapeak / np.std(noise)

def plot_coord(lcmdata, figure: matplotlib.figure, title=None):
    if isinstance(lcmdata, str):
        filepath = lcmdata
        if filepath == "" or not os.path.exists(filepath):
            return
        lcmdata = ReadlcmCoord(filepath)
        if title is None: title = filepath
    elif not isinstance(lcmdata, dict):
        return
    if title is None: title = ".coord file"
    
    # canvas.clear()
    ax = figure.add_subplot(1, 1, 1)
    
    def getOffset(data, prevdata):
        return max(data) - min(prevdata)
    
    ax.plot(lcmdata['ppm'], lcmdata['residue'], 'b-')
    ax.text(4.25, np.mean(lcmdata["residue"]), "Residue", rotation=0, va='center', ha='right', color='b')
    
    padding = (max(lcmdata['fit']) - min(lcmdata['fit'])) * 0.1
    offset = getOffset(lcmdata['fit'], lcmdata['residue']) + padding
    ax.plot(lcmdata['ppm'], [x - offset for x in lcmdata['spec']], 'k-', label="Spectrum")
    ax.plot(lcmdata['ppm'], [x - offset for x in lcmdata['fit']], 'r-', label="Fit")
    ax.text(4.25, np.mean(lcmdata["fit"]) - offset, "Fit", rotation=0, va='center', ha='right', color='r')

    offset += getOffset(lcmdata['baseline'], lcmdata['fit']) + padding
    ax.plot(lcmdata['ppm'], [x - offset for x in lcmdata['baseline']], 'b-', label="Baseline")
    ax.text(4.25, np.mean(lcmdata["baseline"]) - offset, "Baseline", rotation=0, va='center', ha='right', color='b')

    offset += getOffset(lcmdata['subspec'][0], lcmdata['baseline']) + padding
    for i, (metab, subspec) in enumerate(zip(lcmdata['metab'], lcmdata['subspec'])):
        ax.plot(lcmdata['ppm'], [x - offset for x in subspec], 'k-', label=metab)
        ax.text(4.25, -offset, metab, rotation=0, va='center', ha='right', color='k')
        offset += padding

    ax.set_xlabel('ppm')
    ax.set_xlim((4.2, 1))
    ax.get_yaxis().set_visible(False)
    
    figure.suptitle(title)
    figure.tight_layout()