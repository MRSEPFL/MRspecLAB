import os, sys, shutil, zipfile, time, subprocess
import numpy as np
import matplotlib
import wx
from suspect.io.lcmodel import write_all_files
# from spec2nii.other_formats import lcm_raw
# import nibabel
# import ants
# import pandas as pd

from interface import utils
from inout.read_mrs import loadFile
from inout.readcoord import ReadlcmCoord
from inout.readheader import Table
from inout.readcontrol import readControl
from inout.saveraw import save_raw
from interface.plot_helpers import plot_mrs, plot_coord

def loadInput(self):
    self.filepaths = []
    for f in self.MRSfiles.filepaths:
        if not f.lower().endswith(".coord"): self.filepaths.append(f)
    if len(self.filepaths) == 0:
        utils.log_error("No files found")
        return False

    self.originalData = []
    self.header = None
    vendor = None
    dtype = None

    for filepath in self.filepaths:
        try: data, header, dtype, vendor = loadFile(filepath)
        except: utils.log_warning("Error loading file: " + filepath + "\n\t" + str(sys.exc_info()[0]))
        else:
            if data is None:
                utils.log_warning("Couldn't load file: " + filepath)
                continue
            if isinstance(data, list):
                self.originalData += data
            elif len(data.shape) > 1:
                for d in data: self.originalData.append(data.inherit(d))
            else: self.originalData.append(data)
            if header is None: utils.log_warning("Header not found in file: " + filepath)
            elif self.header is None: self.header = header
            utils.log_debug("Loaded file: " + filepath)
    
    if len(self.originalData) == 0:
        utils.log_error("No files loaded")
        return False
    if self.header is None:
        utils.log_error("No header found")
        return False

    self.originalWref = None
    wrefpath = None
    if len(self.Waterfiles.filepaths) > 1: utils.log_warning("Only one water reference is supported; choosing first one")
    if len(self.Waterfiles.filepaths) == 0: utils.log_warning("No water reference given")
    else: wrefpath = self.Waterfiles.filepaths[0]
    if wrefpath is not None:
        try: self.originalWref, _, _, _ = loadFile(wrefpath)
        except: utils.log_warning("Error loading water reference: " + wrefpath + "\n\t" + str(sys.exc_info()[0]))
        else:
            if self.originalWref is None: utils.log_warning("Couldn't load water reference: " + wrefpath)
            self.originalWref = self.originalWref[0]
            utils.log_debug("Loaded water reference: " + filepath)

    utils.log_info(len(self.originalData), " MRS files and ", "no" if self.originalWref is None else "1", " water reference file loaded")

    # check coil combination
    if len(self.originalData[0].shape) > 1:
        if len(self.steps) == 0 or self.steps[0].GetCategory() != "COIL_COMBINATION":
            utils.log_warning("Coil combination needed for multi-coil data; performing basic SVD coil combination")
            # from suspect.processing.channel_combination import combine_channels
            from steps.CoilCombinationAdaptive import combine_channels
            self.originalData = [combine_channels(d) for d in self.originalData]
            if self.originalWref is not None: self.originalWref = combine_channels(self.originalWref)
    
    self.dataSteps = [self.originalData]
    self.wrefSteps = [self.originalWref]
    self.last_wref = None

    # get sequence for proper raw file saving
    seqkey = None
    for key in ["SequenceString", "Sequence"]:
        if key in self.header.keys():
            seqkey = key
            break
    self.sequence = None
    if seqkey is None: utils.log_warning("Sequence not found in header")
    else:
        for seq in utils.supported_sequences:
            if seq.lower() in self.header[seqkey].lower():
                self.sequence = seq
                break
        if self.sequence is None: utils.log_warning("Sequence not supported: " + self.header[seqkey])

    # create output and work folders
    allfiles = [os.path.basename(f) for f in self.filepaths]
    if self.originalWref is not None:
        allfiles.append(os.path.basename(self.Waterfiles.filepaths[0]))
    prefix = os.path.commonprefix(allfiles).strip("."+dtype).replace(" ", "").replace("^", "")
    if prefix == "": prefix = "output"
    base = os.path.join(self.rootPath, "output", prefix)
    self.outputpath = base
    i = 1
    while os.path.exists(self.outputpath):
        self.outputpath = base + f"({i})"
        i += 1
    os.mkdir(self.outputpath)
    self.lcmodelsavepath = os.path.join(self.outputpath, "lcmodel")
    if os.path.exists(self.lcmodelsavepath): shutil.rmtree(self.lcmodelsavepath)
    os.mkdir(self.lcmodelsavepath)
    self.workpath = os.path.join(self.rootPath, "temp")
    if os.path.exists(self.workpath): shutil.rmtree(self.workpath)
    os.mkdir(self.workpath)

    # save header.csv
    if vendor is not None:
        table = Table()
        self.header = table.table_clean(vendor, dtype, self.header)
        table.populate(vendor, dtype, self.header)
        csvcols = ['Header', 'SubHeader', 'MRSinMRS', 'Values']
        table.MRSinMRS_Table[csvcols].to_csv(os.path.join(self.outputpath, "header.csv"))

dataDict = {}

def processStep(self, step, nstep):
    global dataDict
    dataDict["input"] = self.dataSteps[-1]
    dataDict["wref"] = self.wrefSteps[-1]
    dataDict["original"] = self.dataSteps[0]
    dataDict["wref_original"] = self.wrefSteps[0]
    dataDict["output"] = None
    dataDict["wref_output"] = None
    
    self.button_step_processing.Disable()
    if not self.fast_processing:
        self.button_auto_processing.Disable()

    utils.log_debug("Running ", step.__class__.__name__)
    start_time = time.time()
    step.process(dataDict)
    utils.log_info("Time to process " + step.__class__.__name__ + ": {:.3f}".format(time.time() - start_time))
    self.dataSteps.append(dataDict["output"])
    self.dataSteps[0] = dataDict["original"] # very illegal but allows coil combination steps
    if dataDict["wref_output"] is not None:
        self.wrefSteps.append(dataDict["wref_output"])
    else: self.wrefSteps.append(dataDict["wref"])

    utils.log_debug("Plotting ", step.__class__.__name__)
    start_time = time.time()
    steppath = os.path.join(self.outputpath, str(nstep) + step.__class__.__name__)
    if not os.path.exists(steppath): os.mkdir(steppath)
    figure = matplotlib.figure.Figure(figsize=(12, 9))
    # step plot
    step.plot(figure, dataDict)
    figure.suptitle(step.__class__.__name__)
    filepath = os.path.join(steppath, "step.png")
    figure.savefig(filepath, dpi=600)
    utils.log_debug("Saved "+ str(step.__class__.__name__) + " to " + filepath)
    # data plot
    figure.clear()
    plot_mrs(dataDict["output"], figure)
    figure.suptitle("Result of " + step.__class__.__name__)
    filepath = os.path.join(steppath, "result.png")
    figure.savefig(filepath, dpi=600)
    utils.log_debug("Saved "+ "Result of " + step.__class__.__name__ + " to " + filepath)
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
    utils.log_info("Time to plot " + step.__class__.__name__ + ": {:.3f}".format(time.time() - start_time))
    
def saveDataPlot(self): 
    for d, name in zip([self.dataSteps[0], self.dataSteps[-1]], ["Original (after coil combination)", "Result"]):
        filepath = os.path.join(self.outputpath, name + ".png")
        figure = matplotlib.figure.Figure(figsize=(12, 9))
        plot_mrs(d, figure)
        figure.suptitle(name)
        figure.savefig(filepath, dpi=600)
        utils.log_debug("Saved "+ str(name) +" to " + filepath)
        
def analyseResults(self):
    results = self.dataSteps[-1]
    wresult = self.wrefSteps[-1]

    # basis file
    larmor = 0
    for key in ["Nucleus", "nucleus"]:
        if key in self.header.keys():
            if self.header[key] == "1H": larmor = 42.57747892
            elif self.header[key] == "31P": larmor = 10.705
            elif self.header[key] == "23Na": larmor = 11.262
            break
    tesla = round(results[0].f0 / larmor, 0)
    basisfile = None
    if self.sequence is not None:
        strte = str(results[0].te)
        if strte.endswith(".0"): strte = strte[:-2]
        basisfile = str(int(tesla)) + "T_" + self.sequence + "_TE" + str(strte) + "ms.BASIS"
        basisfile = os.path.join(self.rootPath, "lcmodel", basisfile)
    else: utils.log_warning("Sequence not found, basis file not generated")

    def request_basisfile():
        basisfile = ""
        utils.log_info("Requesting basisfile from user...")
        while basisfile == "" or not os.path.exists(os.path.join(self.rootPath, "lcmodel", basisfile)):
            utils.log_warning("Basis set not found:\n\t", basisfile)
            dlg = wx.FileDialog(self, "Select basis set", os.path.join(self.rootPath, "lcmodel"), "", "BASIS files (*.BASIS)|*.BASIS", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
            if dlg.ShowModal() == wx.ID_CANCEL:
                dlg.Destroy()
                return None
            basisfile = dlg.GetPath()
            dlg.Destroy()
        return basisfile

    # if basisfile is not None and os.path.exists(os.path.join(self.rootPath, "lcmodel", basisfile)):
    if basisfile is not None and os.path.exists(basisfile):
        dlg = wx.MessageDialog(None, basisfile, "Basis set found, is it the right one?\n" + basisfile, wx.YES_NO | wx.CANCEL | wx.ICON_INFORMATION)
        button_clicked = dlg.ShowModal()
        if button_clicked == wx.ID_NO: basisfile = request_basisfile()
        elif button_clicked == wx.ID_CANCEL: return False
    else:
        utils.log_warning("Basis set not found:\n\t", basisfile)
        basisfile = request_basisfile()
    if basisfile is None:
        utils.log_error("No basis file specified")
        return False

    for seq in utils.supported_sequences:
        if seq.lower() in basisfile.lower():
            self.sequence = seq
            break

    # lcmodel
    params = None
    if self.controlfile is not None and os.path.exists(self.controlfile):
        try: params = readControl(self.controlfile)
        except: params = None
    else:
        self.controlfile = os.path.join(self.rootPath, "lcmodel", "default.CONTROL")
        try:
            params = readControl(self.controlfile)
            params.update({"DOECC": wresult is not None and "EddyCurrentCorrection" not in self.pipeline}) # not good very bad code
        except: params = None
    if params is None:
        utils.log_error("Control file not found:\n\t", self.controlfile)
        return False
    
    if "labels" in dataDict.keys(): labels = dataDict["labels"]
    else: labels = [str(i) for i in range(len(results))]

    # create work folder and copy lcmodel
    lcmodelfile = os.path.join(self.rootPath, "lcmodel", "lcmodel") # linux exe
    if os.name == 'nt': lcmodelfile += ".exe" # windows exe

    utils.log_debug("Looking for executable here: ", lcmodelfile)
    if not os.path.exists(lcmodelfile): # lcmodel executables are zipped in the repo because of size
        zippath = os.path.join(self.rootPath, "lcmodel", "lcmodel.zip")
        if not os.path.exists(zippath):
            utils.log_error("lcmodel executable or zip not found")
            pass
        utils.log_info("lcmodel executable not found, extracting from zip")
        utils.log_debug("Looking for zip here: ", zippath)
        with zipfile.ZipFile(zippath, "r") as zip_ref:
            zip_ref.extractall(os.path.join(self.rootPath, "lcmodel"))

    if os.name == 'nt': command = f"""mkdir "{self.workpath}" & copy "{lcmodelfile}" "{self.workpath}" """
    else: command = f"""mkdir "{self.workpath}" && cp "{lcmodelfile}" "{self.workpath}" """
    subprocess.run(command, shell=True)

    for result, label in zip(results, labels):
        rparams = params.copy()
        rparams.update({
            "FILBAS": basisfile,
            "FILCSV": f"./{label}.csv",
            "FILCOO": f"./{label}.coord",
            "FILPS": f"./{label}.ps",
            # "FILRAW": f"./{label}.RAW"
            "DOWS": wresult is not None,
            "NUNFIL": result.np,
            "DELTAT": result.dt,
            "ECHOT": result.te,
            "HZPPPM": result.f0
        })
        
        write_all_files(os.path.join(self.workpath, label), result, wref_data=wresult, params=rparams) # write raw, h2o, control files to work folder
        save_raw(os.path.join(self.workpath, f"{label}.RAW"), result, seq=self.sequence) # overwrite raw file with correct sequence type
        if os.name == 'nt': command = f"""cd "{self.workpath}" & lcmodel.exe < {label}_sl0.CONTROL"""
        else: command = f"""cd "{self.workpath}" && ./lcmodel < {label}_sl0.CONTROL"""
        utils.log_debug(f"Running LCModel for {label}...\n\t", command)
        subprocess.run(command, shell=True)

        savepath = os.path.join(self.lcmodelsavepath, label)
        os.mkdir(savepath)
        command = ""
        for f in os.listdir(self.workpath):
            if "lcmodel" in f: continue
            if os.name == 'nt': command += f""" & move "{os.path.join(self.workpath, f)}" "{savepath}" """
            else: command += f""" && mv "{os.path.join(workpath, f)}" "{savepath}" """
        command = command[3:]
        utils.log_debug("Moving files...\n\t", command)
        subprocess.run(command, shell=True)

        filepath = os.path.join(savepath, f"{label}.coord")
        if os.path.exists(filepath):
            f = ReadlcmCoord(filepath)
            figure = matplotlib.figure.Figure(figsize=(10, 10), dpi=600)
            plot_coord(f, figure, title=filepath)
            self.matplotlib_canvas.clear()
            self.read_file(None, filepath) # also fills info panel
            self.matplotlib_canvas.draw()
            filepath = os.path.join(savepath, "lcmodel.png")
            figure.savefig(filepath, dpi=600)
        else: utils.log_warning("LCModel output not found")

    shutil.rmtree(self.workpath) # delete work folder
    utils.log_info("LCModel processing complete")
    
    # save nifti
    # rawpath = os.path.join(self.workpath, "result.RAW")
    # niftipath = os.path.join(self.workpath, "result.nii.gz")
    # save_raw(rawpath, result, seq=self.sequence)
    # class Args:
    #     pass
    # args = Args()
    # args.file = rawpath
    # args.fileout = niftipath
    # args.bandwidth = 1 / result.dt
    # args.nucleus = nucleus
    # args.imagingfreq = result.f0
    # args.affine = None
    # imageOut, _ = lcm_raw(args)
    # imageOut[0].save(niftipath) # nifti
    
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


def processPipeline(self):
    if self.current_step == 0:
        valid_input = loadInput(self)
        if valid_input == False:
            utils.log_error("Error loading input")
            wx.CallAfter(self.reset)
            return
        
    if 0 <= self.current_step and self.current_step <= len(self.steps) - 1:
        processStep(self,self.steps[self.current_step], self.current_step + 1)
        wx.CallAfter(self.DDstepselection.AppendItems, str(self.current_step + 1) + self.steps[self.current_step].__class__.__name__)
        if not self.fast_processing:
            wx.CallAfter(self.button_step_processing.Enable)
            wx.CallAfter(self.button_auto_processing.Enable)
        self.current_step += 1

    elif self.current_step == len(self.steps):
        self.on_save_pipeline(None, os.path.join(self.outputpath, "pipeline.pipe"))
        saveDataPlot(self)
        wx.CallAfter(self.button_step_processing.SetBitmap, self.bmpRunLCModel)
        valid_analysis = analyseResults(self)
        wx.CallAfter(self.DDstepselection.AppendItems, "lcmodel")
        if self.fast_processing:
            wx.CallAfter(self.button_auto_processing.SetBitmap, self.bmp_autopro)
            wx.CallAfter(self.button_auto_processing.Disable)
            wx.CallAfter(self.button_terminate_processing.Enable)
        self.current_step += 1
        
    wx.CallAfter(self.DDstepselection.SetSelection, self.current_step)
    if not self.fast_processing:
        wx.CallAfter(self.button_terminate_processing.Enable)

def autorun_pipeline_exe(self):
    while self.fast_processing and self.current_step <= len(self.steps):
        processPipeline(self)