import os
import numpy as np
import matplotlib.pyplot
from suspect import MRSData
from inout.read_mrs import loadFile
from inout.readcoord import ReadlcmCoord

def plot_mrs(data, figure: matplotlib.pyplot.figure, title=None, fit_gaussian=False):
    ncoils = 1
    if isinstance(data, MRSData):
        if len(data.shape) > 1: # plot each coil separately
            ncoils = data.shape[0]
            data = [data.inherit(data[i]) for i in range(data.shape[0])]
        else:
            data = [data]
            if len(data[0].shape) > 1:
                ncoils = data[0].shape[0]
                data2 = []
                for d in data:
                    data2 = data2 + [d.inherit(d[i]) for i in range(d.shape[0])]
                data = data2
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

    f = data[0]
    info = ""
    if hasattr(f, "np"): info += f"\n\tNumber of points: {f.np}"
    info += f"\n\tNumber of coils: {ncoils}"
    info += f"\n\tNumber of averages: {len(data)}"
    if hasattr(f, "f0"): info += f"\n\tScanner frequency (MHz): {f.f0}"
    if hasattr(f, "dt"): info += f"\n\tDwell time (s): {f.dt}"
    if hasattr(f, "df"): info += f"\n\tFrequency delta (Hz): {f.df}"
    if hasattr(f, "sw"): info += f"\n\tSpectral Width (Hz): {f.sw}"
    if hasattr(f, "te"): info += f"\n\tEcho time (ms): {f.te}"
    if hasattr(f, "tr"): info += f"\n\tRepetition time (ms): {f.tr}"
    info += f"\n\tPPM range: {[f.hertz_to_ppm(-f.sw / 2.0), f.hertz_to_ppm(f.sw / 2.0)]}"
    try:
        if hasattr(f, "centre"): info += f"\n\tCentre: {f.centre}"
    except: pass
    if hasattr(f, "metadata") and hasattr(f.metadata, "items"): info += "\n\tMetadata: " + "\n\t\t".join([f"{k}: {v}" for k, v in f.metadata.items()])
    return info

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

    dtab = '\n\t\t'
    info = (
        f"\n\tNumber of points: {len(lcmdata['ppm'])}\n\tNumber of metabolites: {len(lcmdata['conc'])} ({lcmdata['nfit']} fitted)\n\t0th-order phase: {lcmdata['ph0']}"
        f"\n\t1st-order phase: {lcmdata['ph1']}\n\tFWHM: {lcmdata['linewidth']}\n\tSNR: {lcmdata['SNR']}\n\tData shift: {lcmdata['datashift']}\n"
        f"""\tMetabolites:\n\t\t{dtab.join([f"{c['name']}: {str(c['c'])} (±{str(c['SD'])}%, Cr: {str(c['c_cr'])})" for c in lcmdata['conc']])}\n"""
    )
    return info

def read_file(filepath, canvas, text, fit_gaussian=False):
    if filepath.lower().endswith(".coord"):
        f = ReadlcmCoord(filepath)
        canvas.clear()
        info = plot_coord(f, canvas.figure, title=filepath)
        canvas.draw()
        text.SetValue(f"File: {filepath}\n{info}")
        return
    else:
        f, _, _, _= loadFile(filepath)
        for i in range(len(f)):
            if len(f[i].shape) > 1:
                from suspect.processing.channel_combination import combine_channels
                f[i] = combine_channels(f[i])

        canvas.clear()
        info = plot_mrs(f, canvas.figure, title=filepath, fit_gaussian=fit_gaussian)
        canvas.draw()
        text.SetValue(f"File: {filepath}\n{info}")