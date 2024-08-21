import wx
import numpy as np
import os, sys, shutil, zipfile, time, subprocess
import matplotlib
import ants
import PIL

from interface import utils
from inout.read_mrs import load_file
from inout.read_coord import ReadlcmCoord
from inout.read_header import Table
from inout.save_lcm import save_raw, read_control, save_control
from interface.plot_helpers import plot_mrs, plot_coord, read_file

def loadInput(self):
    self.save_lastfiles()
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
        try: data, header, dtype, vendor = load_file(filepath)
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
        try: self.originalWref, _, _, _ = load_file(wrefpath)
        except: utils.log_warning("Error loading water reference: " + wrefpath + "\n\t" + str(sys.exc_info()[0]))
        else:
            if self.originalWref is None: utils.log_warning("Couldn't load water reference: " + wrefpath)
            else: utils.log_debug("Loaded water reference: " + filepath)

    utils.log_info(len(self.originalData), " MRS files and ", "no" if self.originalWref is None else "1", " water reference file loaded")

    # check coil combination
    if len(self.originalData[0].shape) > 1:
        if len(self.steps) == 0 or self.steps[0].GetCategory() != "COIL_COMBINATION":
            utils.log_warning("Coil combination needed for multi-coil data; performing adaptive coil combination")
            from nodes._CoilCombinationAdaptive import coil_combination_adaptive
            datadict = {"input": self.originalData, "output": [], "wref": self.originalWref, "wref_output": None}
            coil_combination_adaptive(datadict)
            self.originalData = datadict["output"]
            self.originalWref = datadict["wref_output"]
    
    self.dataSteps = [self.originalData]
    self.wrefSteps = [self.originalWref]
    self.last_wref = None

    # get sequence for proper raw file saving
    seqstr = None
    for key in ["SequenceString", "Sequence"]:
        if key in self.header.keys():
            seqstr = self.header[key]
            break
    self.sequence = None
    if seqstr is None: utils.log_warning("Sequence not found in header")
    else:
        for k, v in utils.supported_sequences.items():
            for seq in v:
                if seq in seqstr:
                    self.sequence = k
                    break
        if self.sequence is None: utils.log_warning("Sequence not supported: " + seqstr)
        else: utils.log_info("Sequence detected: ", seqstr + " → " + self.sequence)

    # create output and work folders
    allfiles = [os.path.basename(f) for f in self.filepaths]
    if self.originalWref is not None:
        allfiles.append(os.path.basename(self.Waterfiles.filepaths[0]))
    prefix = os.path.commonprefix(allfiles).strip("."+dtype).replace(" ", "").replace("^", "")
    if prefix == "": prefix = "output"
    if not os.path.exists(self.outputpath_base): os.mkdir(self.outputpath_base)
    base = os.path.join(self.outputpath_base, prefix)
    
    i = 1
    self.outputpath = base
    while os.path.exists(self.outputpath):
        self.outputpath = base + f"({i})"
        i += 1
    os.mkdir(self.outputpath)

    # save header.csv
    if vendor is not None:
        table = Table()
        self.header = table.table_clean(vendor, dtype, self.header)
        table.populate(vendor, dtype, self.header)
        csvcols = ['Header', 'SubHeader', 'MRSinMRS', 'Values']
        table.MRSinMRS_Table[csvcols].to_csv(os.path.join(self.outputpath, "MRSinMRS_table.csv"))
    return True

dataDict = {}

def processStep(self, step, nstep):
    global dataDict
    dataDict["input"] = self.dataSteps[-1]
    dataDict["wref"] = self.wrefSteps[-1]
    dataDict["output"] = []
    dataDict["wref_output"] = []
    
    self.button_step_processing.Disable()
    if not self.fast_processing:
        self.button_auto_processing.Disable()

    utils.log_debug("Running ", step.__class__.__name__)
    start_time = time.time()
    step.process(dataDict)
    utils.log_info("Time to process " + step.__class__.__name__ + ": {:.3f}".format(time.time() - start_time))
    self.dataSteps.append(dataDict["output"])
    if len(dataDict["wref_output"]) != 0:
        self.wrefSteps.append(dataDict["wref_output"])
    else: self.wrefSteps.append(dataDict["wref"])

    utils.log_debug("Plotting ", step.__class__.__name__)
    start_time = time.time()
    if self.save_plots_button.GetValue():
        steppath = os.path.join(self.outputpath, str(nstep) + step.__class__.__name__)
        if not os.path.exists(steppath): os.mkdir(steppath)
        figure = matplotlib.figure.Figure(figsize=(12, 9))
        # step plot
        step.plot(figure, dataDict)
        figure.suptitle(step.__class__.__name__)
        filepath = os.path.join(steppath, step.__class__.__name__ + ".png")
        figure.savefig(filepath, dpi=600)
        utils.log_debug("Saved "+ str(step.__class__.__name__) + " to " + filepath)
        # data plot
        figure.clear()
        plot_mrs(dataDict["output"], figure)
        figure.suptitle("Result of " + step.__class__.__name__)
        filepath = os.path.join(steppath, "result.png")
        figure.savefig(filepath, dpi=600)
        utils.log_debug("Saved result of " + step.__class__.__name__ + " to " + filepath)
    # raw
    if self.save_raw_button.GetValue():
        filepath = os.path.join(steppath, "data")
        if not os.path.exists(filepath): os.mkdir(filepath)
        for i, d in enumerate(dataDict["output"]): save_raw(os.path.join(filepath, str(i) + ".RAW"), d, seq=self.sequence)
        for i, d in enumerate(dataDict["wref_output"]): save_raw(os.path.join(filepath, "wref_" + str(i) + ".RAW"), d, seq=self.sequence)
    # canvas plot
    if not self.fast_processing:
        self.matplotlib_canvas.clear()
        step.plot(self.matplotlib_canvas.figure, dataDict)
        self.matplotlib_canvas.draw()
    utils.log_info("Time to plot " + step.__class__.__name__ + ": {:.3f}".format(time.time() - start_time))
    
def saveDataPlot(self):
    dlg = wx.MessageDialog(None, "Do you want to manually adjust frequency and phase shifts of the result?", "", wx.YES_NO | wx.ICON_INFORMATION)
    button_clicked = dlg.ShowModal()
    if button_clicked == wx.ID_YES:
        self.matplotlib_canvas.clear()
        from processing.manual_adjustment import ManualAdjustment
        manual_adjustment = ManualAdjustment(self.dataSteps[-1], self.matplotlib_canvas)
        self.dataSteps.append(manual_adjustment.run())
    # save result plot
    filepath = os.path.join(self.outputpath, "Result.png")
    figure = matplotlib.figure.Figure(figsize=(12, 9))
    plot_mrs(self.dataSteps[-1], figure)
    figure.suptitle("Result")
    figure.savefig(filepath, dpi=600)
    utils.log_debug("Saved result to " + filepath)
        
def analyseResults(self):
    results = self.dataSteps[-1]
    wresult = self.wrefSteps[-1][0].inherit(np.mean(np.array(self.wrefSteps[-1]), 0))
    self.basis_file = None

    # basis file
    larmor = 0
    for key in ["Nucleus", "nucleus"]:
        if key in self.header.keys():
            if self.header[key] == "1H": larmor = 42.577
            elif self.header[key] == "31P": larmor = 10.705
            elif self.header[key] == "23Na": larmor = 11.262
            break
    tesla = round(results[0].f0 / larmor, 0)
    basis_file_gen = None
    if self.sequence is not None:
        strte = str(results[0].te)
        if strte.endswith(".0"): strte = strte[:-2]
        basis_file_gen = str(int(tesla)) + "T_" + self.sequence + "_TE" + str(strte) + "ms.BASIS"
        basis_file_gen = os.path.join(self.programpath, "lcmodel", "basis", basis_file_gen)
    else: utils.log_warning("Sequence not found, basis file not generated")
    
    if self.basis_file_user is not None: # user specified basis file
        if not os.path.exists(self.basis_file_user):
            utils.log_warning("Basis set not found:\n\t", self.basis_file)
            self.basis_file = None
        else: self.basis_file = self.basis_file_user

    if self.basis_file is None and basis_file_gen is not None and os.path.exists(basis_file_gen): # generated basis file
        dlg = wx.MessageDialog(None, basis_file_gen, "Basis set found, is it the right one?\n" + basis_file_gen, wx.YES_NO | wx.CANCEL | wx.ICON_INFORMATION)
        button_clicked = dlg.ShowModal()
        if button_clicked == wx.ID_YES: self.basis_file = basis_file_gen
        elif button_clicked == wx.ID_CANCEL: return False
    
    if self.basis_file is None:
        utils.log_warning("Basis set not found:\n\t", self.basis_file)
        self.fitting_frame.Show()
        self.fitting_frame.SetFocus()
        while self.fitting_frame.IsShown(): time.sleep(0.1)
        self.basis_file = self.basis_file_user

    if self.basis_file is None:
        utils.log_error("No basis file specified")
        return False

    # control file
    params = None
    if self.control_file_user is not None and os.path.exists(self.control_file_user):
        try: params = read_control(self.control_file_user)
        except: params = None
    else:
        self.control_file_user = os.path.join(self.programpath, "lcmodel", "default.CONTROL")
        try:
            params = read_control(self.control_file_user)
            params.update({"DOECC": wresult is not None and "EddyCurrentCorrection" not in self.pipeline}) # not good very bad code
        except: params = None
    if params is None:
        utils.log_error("Control file not found:\n\t", self.control_file_user)
        return False
    
    if "labels" in dataDict.keys(): labels = dataDict["labels"]
    else: labels = [str(i) for i in range(len(results))]
    
    # segmentation
    wconc = None
    if self.wm_file_user is not None and self.gm_file_user is not None and self.csf_file_user is not None:
        try: centre = results[0].centre
        except:
            utils.log_error("Could not retrieve voxel location from data")
            return False
        try:
            wm_img = ants.image_read(self.wm_file_user)
            gm_img = ants.image_read(self.gm_file_user)
            csf_img = ants.image_read(self.csf_file_user)
        except Exception as e:
            utils.log_error("Could not load segmentation files\n\t", e)
            return False
        thickness = np.array([np.max(np.abs(np.array(results[0].transform)[:3, i])) for i in range(3)])
        index1 = ants.transform_physical_point_to_index(wm_img, centre - thickness / 2).astype(int)
        index2 = ants.transform_physical_point_to_index(wm_img, centre + thickness / 2).astype(int)
        for i in range(3):
            if index1[i] > index2[i]: index1[i], index2[i] = index2[i], index1[i]
        wm_sum = np.sum(wm_img.numpy()[index1[0]:index2[0], index1[1]:index2[1], index1[2]:index2[2]])
        gm_sum = np.sum(gm_img.numpy()[index1[0]:index2[0], index1[1]:index2[1], index1[2]:index2[2]])
        csf_sum = np.sum(csf_img.numpy()[index1[0]:index2[0], index1[1]:index2[1], index1[2]:index2[2]])
        _sum = wm_sum + gm_sum + csf_sum
        f_wm = wm_sum / _sum
        f_gm = gm_sum / _sum
        f_csf = csf_sum / _sum
        wconc = (43300*f_gm + 35880*f_wm + 55556*f_csf) / (1 - f_csf)
        utils.log_info("Calculated the following values from the segmentation files:\n\tWM: ", f_wm, " GM: ", f_gm, " CSF: ", f_csf, " → Water concentration: ", wconc)

    # create work folder and copy lcmodel
    lcmodelfile = os.path.join(self.programpath, "lcmodel", "lcmodel") # linux exe
    if os.name == 'nt': lcmodelfile += ".exe" # windows exe

    utils.log_debug("Looking for executable here: ", lcmodelfile)
    if not os.path.exists(lcmodelfile): # lcmodel executables are zipped in the repo
        zippath = os.path.join(self.programpath, "lcmodel", "lcmodel.zip")
        if not os.path.exists(zippath):
            utils.log_error("lcmodel executable or zip not found")
            pass
        utils.log_info("lcmodel executable not found, extracting from zip")
        utils.log_debug("Looking for zip here: ", zippath)
        with zipfile.ZipFile(zippath, "r") as zip_ref:
            zip_ref.extractall(os.path.join(self.programpath, "lcmodel"))

    workpath = os.path.join(os.getcwd(), "temp")
    if os.path.exists(workpath): shutil.rmtree(workpath)
    os.mkdir(workpath)
    utils.log_debug("LCModel work folder: ", workpath)

    if os.name == 'nt': command = f"""copy "{lcmodelfile}" "{workpath}" """
    else: command = f"""cp "{lcmodelfile}" "{workpath}" """
    subprocess.run(command, shell=True)

    lcmodelsavepath = os.path.join(self.outputpath, "lcmodel")
    if os.path.exists(lcmodelsavepath): shutil.rmtree(lcmodelsavepath)
    os.mkdir(lcmodelsavepath)
    utils.log_debug("LCModel output folder: ", lcmodelsavepath)

    for result, label in zip(results, labels):
        rparams = params.copy()
        rparams.update({
            "FILBAS": self.basis_file,
            "FILCSV": f"./{label}.csv",
            "FILCOO": f"./{label}.coord",
            "FILPS": f"./{label}.ps",
            "FILTAB": f"./{label}.table",
            "FILRAW": f"./{label}.RAW",
            "FILH2O": f"./{label}.H2O",
            "DOWS": wresult is not None,
            "NUNFIL": result.np,
            "DELTAT": result.dt,
            "ECHOT": result.te,
            "HZPPPM": result.f0
        })
        if wconc is not None: rparams.update({ "WCONC": wconc })
        
        # write_all_files(os.path.join(workpath, f"{label}.CONTROL"), result, wref_data=wresult, params=rparams) # write raw, h2o, control files to work folder
        save_control(os.path.join(workpath, f"{label}.CONTROL"), rparams)
        save_raw(os.path.join(workpath, f"{label}.RAW"), result, seq=self.sequence) # overwrite raw file with correct sequence type
        save_raw(os.path.join(workpath, f"{label}.H2O"), wresult, seq=self.sequence)
        if os.name == 'nt': command = f"""cd "{workpath}" & lcmodel.exe < {label}.CONTROL"""
        else: command = f"""cd "{workpath}" && ./lcmodel < {label}.CONTROL"""
        utils.log_info(f"Running LCModel for {label}...")
        utils.log_debug("\n\t", command)
        subprocess.run(command, shell=True)
        
        savepath = os.path.join(lcmodelsavepath, label)
        os.mkdir(savepath)

        command = "" # move all files from work to output folder
        for f in os.listdir(workpath):
            if "lcmodel" in f: continue
            if os.name == 'nt': command += f""" & move "{os.path.join(workpath, f)}" "{savepath}" """
            else: command += f""" && mv "{os.path.join(workpath, f)}" "{savepath}" """
        command = command[3:]
        utils.log_debug("Moving files...\n\t", command)
        subprocess.run(command, shell=True)

        filepath = os.path.join(savepath, f"{label}.coord")
        if os.path.exists(filepath):
            self.last_coord = filepath
            f = ReadlcmCoord(filepath)
            figure = matplotlib.figure.Figure(figsize=(10, 10), dpi=600)
            plot_coord(f, figure, title=filepath)
            read_file(filepath, self.matplotlib_canvas, self.file_text)
            filepath = os.path.join(savepath, "lcmodel.png")
            figure.savefig(filepath, dpi=600)
        else: utils.log_warning("LCModel output not found")

    shutil.rmtree(workpath) # delete work folder
    utils.log_info("LCModel processing complete")
    return True

def processPipeline(self):
    if self.current_step == 0:
        wx.CallAfter(self.plot_box.Clear)
        wx.CallAfter(self.plot_box.AppendItems, "")
        if not loadInput(self):
            utils.log_error("Error loading input")
            wx.CallAfter(self.reset)
            return
        
    if 0 <= self.current_step and self.current_step <= len(self.steps) - 1:
        self.retrieve_pipeline() # bad way to update any changed parameters
        processStep(self, self.steps[self.current_step], self.current_step + 1)
        wx.CallAfter(self.plot_box.AppendItems, str(self.current_step + 1) + self.steps[self.current_step].__class__.__name__)
        if not self.fast_processing:
            wx.CallAfter(self.button_step_processing.Enable)
            wx.CallAfter(self.button_auto_processing.Enable)

    elif self.current_step == len(self.steps):
        self.pipeline_frame.on_save_pipeline(None, os.path.join(self.outputpath, "pipeline.pipe"))
        saveDataPlot(self)
        if analyseResults(self): wx.CallAfter(self.plot_box.AppendItems, "lcmodel")
        else: self.reset()

    self.current_step += 1
    wx.CallAfter(self.plot_box.SetSelection, self.current_step)
    if self.current_step > len(self.steps):
        self.reset()
        return
    if not self.fast_processing:
        wx.CallAfter(self.button_terminate_processing.Enable)

def autorun_pipeline_exe(self):
    while self.fast_processing and self.current_step <= len(self.steps):
        processPipeline(self)