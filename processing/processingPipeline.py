import os
import sys
import suspect
import shutil
import zipfile
import numpy as np
import matplotlib
import time
import wx
from suspect import MRSData
from spec2nii.other_formats import lcm_raw
# import nibabel
# import ants
# import pandas as pd

from inout.readcoord import ReadlcmCoord
from inout.readheader import DataReaders, Table
from inout.readcontrol import readControl
from inout.saveraw import save_raw
from interface.plots import plot_ima, plot_coord

def loadInput(self):
    self.filepaths = []
    for f in self.inputMRSfiles_dt.filepaths:
        if not f.lower().endswith(".coord"):
            self.filepaths.append(f)
    if len(self.filepaths) == 0:
        self.log_error("No files found")
        return False

    self.originalWref = None
    if len(self.inputwref_dt.filepaths)==0:
        self.log_warning("No water reference found")
    elif len(self.inputwref_dt.filepaths)>1:
        self.log_error("Only one water reference is supported for now")
        return False
    else:
        if self.inputwref_dt.filepaths[0].lower().endswith((".ima", ".dcm")):
            self.originalWref  = suspect.io.load_siemens_dicom(self.inputwref_dt.filepaths[0])
        elif self.inputwref_dt.filepaths[0].lower().endswith(".dat"):
            self.originalWref = suspect.io.load_twix(self.inputwref_dt.filepaths[0])
            self.originalWref = suspect.processing.channel_combination.combine_channels(self.originalWref) # temporary?
        self.log_info("Water reference loaded: " + self.inputwref_dt.filepaths[0])

    self.originalData = []
    self.header = None
    vendor = None
    dtype = None
    for i in range(len(self.filepaths)):
        try:
            if self.filepaths[i].lower().endswith((".ima", ".dcm")):
                data = suspect.io.load_siemens_dicom(self.filepaths[i])
                if vendor is None: vendor = "siemens"
                if self.header is None: self.header, _ = DataReaders().siemens_ima(self.filepaths[i], None)
            elif self.filepaths[i].lower().endswith(".dat"):
                data = suspect.io.load_twix(self.filepaths[i])
                if vendor is None: vendor = "siemens"
                if self.header is None: self.header, _ = DataReaders().siemens_twix(self.filepaths[i], None)
                data = suspect.processing.channel_combination.combine_channels(data) # temporary?
            elif self.filepaths[i].lower().endswith(".sdat"):
                data = suspect.io.load_sdat(self.filepaths[i], None) # should find .spar
                spar = self.filepaths[i].lower()[:-5] + ".spar"
                if vendor is None: vendor = "philips"
                if os.path.exists(spar):
                    if self.header is None: self.header, _ = DataReaders().philips_spar(spar, None)
                else: self.log_warning("SPAR file not found for: " + self.filepaths[i])
            else:
                self.log_error("Unsupported file format: " + self.filepaths[i])
                continue
            if dtype is None: dtype = os.path.splitext(self.filepaths[i])[1][1:].lower() # [1:] to remove .
            if len(data.shape) > 1:
                for d in data: self.originalData.append(data.inherit(d))
            else: self.originalData.append(data)
        except: self.log_warning("Error loading file: " + self.filepaths[i] + "\n\t" + str(sys.exc_info()[0]))
    if len(self.originalData) == 0:
        self.log_error("No files loaded")
        return False
    if self.header is None: self.log_warning("Header not found, crashes impending")
    self.log_info(len(self.originalData), " MRS files and ", "no" if self.originalWref is None else "1", " water reference file loaded")

    seqkey = None
    for key in ["SequenceString", "Sequence"]:
        if key in self.header.keys():
            seqkey = key
            break
    self.sequence = None # get sequence for proper raw file saving
    if seqkey is None: self.log_warning("Sequence not found in header")
    else:
        for seq in self.supported_sequences:
            if seq.lower() in self.header[seqkey].lower():
                self.sequence = seq
                break

    allfiles = [os.path.basename(f) for f in self.filepaths]
    allfiles.append(os.path.basename(self.inputwref_dt.filepaths[0]))
    prefix = os.path.commonprefix(allfiles)
    if prefix == "": prefix = "output"
    base = os.path.join(self.rootPath, "output", prefix)
    self.outputpath = base
    i = 1
    while os.path.exists(self.outputpath):
        self.outputpath = base + "(" + str(i) + ")"
        i += 1
    os.mkdir(self.outputpath)
    self.lcmodelsavepath = os.path.join(self.outputpath, "lcmodel")
    if os.path.exists(self.lcmodelsavepath): shutil.rmtree(self.lcmodelsavepath)
    os.mkdir(self.lcmodelsavepath)
    self.workpath = os.path.join(self.rootPath, "temp")
    if os.path.exists(self.workpath): shutil.rmtree(self.workpath)
    os.mkdir(self.workpath)
    self.dataSteps: list[MRSData] = [self.originalData]
    self.wrefSteps: list[MRSData] = [self.originalWref]
    self.last_wref = None

    # save header.csv
    table = Table()
    self.header = table.table_clean(vendor, dtype, self.header)
    table.populate(vendor, dtype, self.header)
    csvcols = ['Header', 'SubHeader', 'MRSinMRS', 'Values']
    table.MRSinMRS_Table[csvcols].to_csv(os.path.join(self.outputpath, "header.csv"))

def processStep(self, step, nstep):
    dataDict = {
        "input": self.dataSteps[-1],
        "wref": self.wrefSteps[-1],
        "original": self.dataSteps[0],
        "wref_original": self.wrefSteps[0],
        "output": None,
        "wref_output": None
    }
    self.button_step_processing.Disable()
    if not self.fast_processing:
        self.button_auto_processing.Disable()

    # updateprogress(self,step,nstep,len(self.steps))
    self.log_debug("Running ", step.__class__.__name__)
    start_time = time.time()
    step.process(dataDict)
    self.log_info("Time to process " + step.__class__.__name__ + ": {:.3f}".format(time.time() - start_time))
    self.dataSteps.append(dataDict["output"])
    if dataDict["wref_output"] is not None:
        self.wrefSteps.append(dataDict["wref_output"])
    else: self.wrefSteps.append(dataDict["wref"])

    self.log_debug("Plotting ", step.__class__.__name__)
    start_time = time.time()
    steppath = os.path.join(self.outputpath, str(nstep) + step.__class__.__name__)
    if not os.path.exists(steppath): os.mkdir(steppath)
    figure = matplotlib.figure.Figure(figsize=(12, 9))
    # step plot
    step.plot(figure, dataDict)
    figure.suptitle(step.__class__.__name__)
    filepath = os.path.join(steppath, "step.png")
    figure.savefig(filepath, dpi=600)
    self.log_debug("Saved "+ str(step.__class__.__name__) + " to " + filepath)
    # data plot
    figure.clear()
    plot_ima(dataDict["output"], figure)
    figure.suptitle("Result of " + step.__class__.__name__)
    filepath = os.path.join(steppath, "result.png")
    figure.savefig(filepath, dpi=600)
    self.log_debug("Saved "+ "Result of " + step.__class__.__name__ + " to " + filepath)
    # raw
    if self.save_raw:
        filepath = os.path.join(steppath, "data")
        if not os.path.exists(filepath): os.mkdir(filepath)
        for i, d in enumerate(dataDict["output"]): save_raw(os.path.join(filepath, str(i) + ".RAW"), d, seq=self.sequence)
        save_raw(os.path.join(filepath, "wref.RAW"), self.wrefSteps[-1], seq=self.sequence)
    # canvas plot
    if not self.fast_processing:
        self.matplotlib_canvas.clear()
        step.plot(self.matplotlib_canvas.figure, dataDict)
        self.matplotlib_canvas.draw()
    self.log_info("Time to plot " + step.__class__.__name__ + ": {:.3f}".format(time.time() - start_time))
    
def saveDataPlot(self): 
    for d, name in zip([self.dataSteps[0], self.dataSteps[-1]], ["Original", "Result"]):
        filepath = os.path.join(self.outputpath, name + ".png")
        figure = matplotlib.figure.Figure(figsize=(12, 9))
        plot_ima(d, figure)
        figure.suptitle(name)
        figure.savefig(filepath, dpi=600)
        self.log_debug("Saved "+ str(name) +" to " + filepath)
        
def analyseResults(self):
    result = self.dataSteps[-1]
    wresult = self.wrefSteps[-1]
    if len(result) == 1: result = result[0]
    else: result = result[0].inherit(np.mean(result, axis=0))

    # basis file
    larmor = 0
    nucleus = None
    for key in ["Nucleus", "nucleus"]:
        if key in self.header.keys():
            nucleus = self.header[key]
            if self.header[key] == "1H": larmor = 42.57747892
            elif self.header[key] == "31P": larmor = 10.705
            elif self.header[key] == "23Na": larmor = 11.262
            break
    tesla = round(result.f0 / larmor, 0)
    basisfile = None
    if self.sequence is not None:
        strte = str(result.te)
        if strte.endswith(".0"): strte = strte[:-2]
        basisfile = str(int(tesla)) + "T_" + self.sequence + "_TE" + str(strte) + "ms.BASIS"
        basisfile = os.path.join(self.rootPath, "lcmodel", basisfile)
    else: self.log_warning("Sequence not found, basis file not generated")

    def request_basisfile():
        basisfile = ""
        self.log_info("Requesting basisfile from user...")
        while basisfile == "" or not os.path.exists(os.path.join(self.rootPath, "lcmodel", basisfile)):
            self.log_warning("Basis set not found:\n\t", basisfile)
            dlg = wx.FileDialog(self, "Select basis set", os.path.join(self.rootPath, "lcmodel"), "", "BASIS files (*.BASIS)|*.BASIS", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
            if dlg.ShowModal() == wx.ID_CANCEL:
                dlg.Destroy()
                return None
            basisfile = dlg.GetPath()
            dlg.Destroy()
        return basisfile

    if basisfile is not None and os.path.exists(os.path.join(self.rootPath, "lcmodel", basisfile)):
        dlg = wx.MessageDialog(None, basisfile, "Basis set found, is it the right one?\n" + basisfile, wx.YES_NO | wx.CANCEL | wx.ICON_INFORMATION)
        button_clicked = dlg.ShowModal()
        if button_clicked == wx.ID_NO: basisfile = request_basisfile()
        elif button_clicked == wx.ID_CANCEL: return False
    else:
        self.log_warning("Basis set not found:\n\t", basisfile)
        basisfile = request_basisfile()
    if basisfile is None:
        self.log_error("No basis file specified")
        return False

    # lcmodel
    if self.controlfile is not None and os.path.exists(self.controlfile):
        params = readControl(self.controlfile)
    else:
        self.controlfile = os.path.join(self.rootPath, "lcmodel", "default.CONTROL")
        params = readControl(self.controlfile)
        params.update({
            "DOECC": wresult is not None and "EddyCurrentCorrection" not in self.pipeline # not good very bad code
        })
    if params is None:
        self.log_error("Control file not found:\n\t", self.controlfile)
        return False
    params.update({
        "FILBAS": basisfile,
        "FILCSV": "./result.csv",
        "FILCOO": "./result.coord",
        "FILPS": "./result.ps",
        "DOWS": wresult is not None,
        "NUNFIL": result.np,
        "DELTAT": result.dt,
        "ECHOT": result.te,
        "HZPPPM": result.f0
    })
    
    controlfilepath = os.path.join(self.workpath, "result")
    suspect.io.lcmodel.write_all_files(controlfilepath, result, wref_data=wresult, params=params) # write raw, h2o, control files to work folder
    save_raw(os.path.join(self.workpath, "result.RAW"), result, seq=self.sequence) # overwrite raw file with correct sequence type
    lcmodelfile = os.path.join(self.rootPath, "lcmodel", "lcmodel") # linux exe
    if os.name == 'nt': lcmodelfile += ".exe" # windows exe

    self.log_debug("Looking for executable here: ", lcmodelfile)
    if not os.path.exists(lcmodelfile): # lcmodel executables are zipped in the repo because of size
        zippath = os.path.join(self.rootPath, "lcmodel", "lcmodel.zip")
        if not os.path.exists(zippath):
            self.log_error("lcmodel executable or zip not found")
            pass
        self.log_info("lcmodel executable not found, extracting from zip")
        self.log_debug("Looking for zip here: ", zippath)
        with zipfile.ZipFile(zippath, "r") as zip_ref:
            zip_ref.extractall(os.path.join(self.rootPath, "lcmodel"))

    if os.name == 'nt': command = f"""mkdir {self.workpath} & copy {lcmodelfile} {self.workpath} & cd {self.workpath} & lcmodel.exe < result_sl0.CONTROL & del lcmodel.exe"""
    else: command = f"""mkdir {workpath} && cp {lcmodelfile} {workpath} && cd {workpath} && ./lcmodel < control_sl0.CONTROL && rm lcmodel"""
    self.log_debug("Running LCModel...\n\t", command)
    os.system(command)
    
    command = ''
    for f in os.listdir(self.workpath):
        if os.name == 'nt': command += f" & move {os.path.join(self.workpath, f)} {self.lcmodelsavepath}"
        else: command += f" && mv {os.path.join(workpath, f)} {lcmodelsavepath}"
    command = command[3:]
    self.log_debug("Moving files...\n\t", command)
    os.system(command)

    filepath = os.path.join(self.lcmodelsavepath, "result.coord")
    if os.path.exists(filepath):
        f = ReadlcmCoord(filepath)
        figure = matplotlib.figure.Figure(figsize=(10, 10), dpi=600)
        plot_coord(f, figure, title=filepath)
        self.matplotlib_canvas.clear()
        self.read_file(None, filepath) # also fills info panel
        self.matplotlib_canvas.draw()
        filepath = os.path.join(self.lcmodelsavepath, "lcmodel.png")
        figure.savefig(filepath, dpi=600)
    else: self.log_warning("LCModel output not found")
    
    # save nifti
    rawpath = os.path.join(self.workpath, "result.RAW")
    niftipath = os.path.join(self.workpath, "result.nii.gz")
    save_raw(rawpath, result, seq=self.sequence)
    class Args:
        pass
    args = Args()
    args.file = rawpath
    args.fileout = niftipath
    args.bandwidth = 1 / result.dt
    args.nucleus = nucleus
    args.imagingfreq = result.f0
    args.affine = None
    imageOut, _ = lcm_raw(args)
    imageOut[0].save(niftipath) # nifti
    
    # # segmentation
    # nib_image = nibabel.loadsave.load(niftipath)
    # fi = ants.from_nibabel(nib_image)
    # # seg = ants.kmeans_segmentation(fi,3)
    # mask = ants.get_mask(fi)
    # print(fi.shape)
    # # mask = ants.threshold_image(seg['segmentation'], 1, 1e15)
    # # priorseg = ants.prior_based_segmentation(fi, seg['probabilityimages'], mask, 0.25, 0.1, 3)
    # seg = ants.atropos(a=fi, m='[0.1,1x1x1]', c='[2,0]', i='kmeans[3]', x=mask)
    # CSF = seg['probabilityimages'][0]
    # GM = seg['probabilityimages'][1]
    # WM = seg['probabilityimages'][2]
    # try: centre = result.centre
    # except: centre = None
    # if centre is not None:
    #     print(CSF[centre[0], centre[1], centre[2]])
    #     print(GM[centre[0], centre[1], centre[2]])
    #     print(WM[centre[0], centre[1], centre[2]])

    shutil.rmtree(self.workpath) # delete work folder

def processPipeline(self):
    if self.current_step == 0:
        self.pipeline, self.steps = self.retrievePipeline()
        self.SetStatusText("Current pipeline: " + " → ".join(self.pipeline))
        valid_input = loadInput(self)
        if valid_input == False:
            wx.CallAfter(self.PostStepProcessingGUIChanges)
            self.fast_processing = False
            return
    if 0 <= self.current_step and self.current_step <= len(self.steps) - 1:
        processStep(self,self.steps[self.current_step], self.current_step + 1)
        self.current_step += 1
    elif self.current_step == len(self.steps):
        self.on_save_pipeline(None, os.path.join(self.outputpath, "pipeline.pipe"))
        saveDataPlot(self)
        valid_analysis = analyseResults(self)
        self.current_step += 1 ##### to change with a LCModeldone bool 
    else: print("Error  Finished, no further steps, to changes this part")
    wx.CallAfter(self.PostStepProcessingGUIChanges)
    self.proces_completion = True

def autorun_pipeline_exe(self):
    while self.fast_processing and self.current_step <= len(self.steps):
        processPipeline(self)