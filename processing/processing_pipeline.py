import wx
import numpy as np
import os, sys, shutil, zipfile, time, subprocess
import matplotlib
import ants
import datetime
import traceback
import subprocess

import re

from interface import utils
from inout.read_mrs import load_file
from inout.read_coord import ReadlcmCoord
from inout.read_header import Table
from inout.io_lcmodel import save_raw, read_control, save_control, save_nifti, save_nifti_spec2nii
from interface.plot_helpers import plot_mrs, plot_coord, read_file

#SVS


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
    self.issvs = True
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
            else:
                # check multi-voxel for rda data
                if dtype == "rda":
                    if header["CSIMatrix_Size[0]"] == 1 and header["CSIMatrix_Size[1]"] == 1 and header["CSIMatrix_Size[2]"] == 1:
                        self.issvs = True
                        utils.log_info("SVS data")
                    else:
                        self.issvs = False
                        utils.log_info("CSI data")

                if self.header is None: self.header = header
            utils.log_debug("Loaded file: " + filepath)
    
    if len(self.originalData) == 0:
        utils.log_error("No files loaded")
        return False
    if self.header is None:
        utils.log_error("No header found")
        return False
    
    nucleus = None
    for key in ["Nucleus", "nucleus"]:
        if key in self.header:
            nucleus = self.header[key]
            break

    if nucleus == "31P" and self.issvs:
        has_phase_alignment = any("PhaseAlignment31P" in step.__class__.__name__ for step in self.steps) or any("TEBasedPhaseCorrecton31P" in step.__class__.__name__ for step in self.steps)
        if not has_phase_alignment:
            dlg = wx.MessageDialog(
                self,
                "31P data detected, but the current pipeline does not include the 'PhaseAlignment31P' step.\n"
                "Would you like to load the standard 31P pipeline?",
                "Pipeline Mismatch",
                wx.YES_NO | wx.ICON_QUESTION
            )
            response = dlg.ShowModal()
            dlg.Destroy()
            if response == wx.ID_YES:
                standard_pipeline_path = os.path.join(os.getcwd(), "31P_standard_pipeline.pipe")
                self.pipeline_frame.on_load_pipeline(event=None, filepath=standard_pipeline_path)

        if len(self.filepaths) > 1 and dtype not in ("dcm", "ima", "raw"):
            utils.log_warning("Multiple files given despite not in DICOM, IMA, or RAW format")

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
    if dtype != "rda": # "rda" is coil combined 
        if len(self.originalData[0].shape) > 1: #check if its voxel or coil dimension better
            if len(self.steps) == 0 or self.steps[0].GetCategory() != "COIL_COMBINATION":
                utils.log_warning("Coil combination needed for multi-coil data; performing adaptive coil combination")
                from nodes._CoilCombinationAdaptive import coil_combination_adaptive
                datadict = {"input": self.originalData, "output": [], "wref": self.originalWref, "wref_output": None}
                coil_combination_adaptive(datadict)
                self.originalData = datadict["output"]
                self.originalWref = datadict["wref_output"]
    
    self.dataSteps = [self.originalData]
    self.wrefSteps = [self.originalWref]
    self.headerSteps = [self.header] # added for transmit header, for reading MRSI data dimension in processing nodes
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
        if self.sequence is not None:
            utils.log_info("Sequence detected: ", seqstr + " → " + self.sequence)

    # create output and work folders
    allfiles = [os.path.basename(f) for f in self.filepaths]
    if self.originalWref is not None:
        allfiles.append(os.path.basename(self.Waterfiles.filepaths[0]))
    # prefix = os.path.commonprefix(allfiles).strip("."+dtype).replace(" ", "").replace("^", "")
    # if prefix == "": prefix = "output"
    if hasattr(self, 'batch_mode') and self.batch_mode and hasattr(self, 'participant_name') and self.participant_name:
        prefix = self.participant_name
        base = os.path.join(self.batch_study_folder, prefix)
    else:
        prefix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + self.filepaths[0].split(os.path.sep)[-1][:-len(dtype)-1]
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
    
    dataDict["header"] = self.headerSteps[-1] # added for transmit header

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
        filepath = os.path.join(steppath, step.__class__.__name__ + ".pdf")
        figure.savefig(filepath, dpi=600, format = 'pdf')
        utils.log_debug("Saved "+ str(step.__class__.__name__) + " to " + filepath)
        # data plot
        figure.clear()
        if self.issvs:
            plot_mrs(dataDict["output"], figure)
            figure.suptitle("Result of " + step.__class__.__name__)
            filepath = os.path.join(steppath, "result.pdf")
            figure.savefig(filepath, dpi=600, format = 'pdf')
            utils.log_debug("Saved result of " + step.__class__.__name__ + " to " + filepath)
    # raw
    if self.save_raw_button.GetValue():
        steppath = os.path.join(self.outputpath, str(nstep) + step.__class__.__name__)
        if not os.path.exists(steppath): os.mkdir(steppath)
        filepath = os.path.join(steppath, "data")
        if not os.path.exists(filepath): os.mkdir(filepath)
        #for i, d in enumerate(dataDict["output"]): 
        #    if d is not None:
        #        save_raw(os.path.join(filepath, str(i) + ".RAW"), d, seq=self.sequence)
        #for i, d in enumerate(dataDict["wref_output"]): save_raw(os.path.join(filepath, "wref_" + str(i) + ".RAW"), d, seq=self.sequence)
        #for i, d in enumerate(dataDict["output"]): 
        #    if d is not None:
        #        save_nifti(os.path.join(filepath, str(i) + ".nii"), d, seq=self.sequence)
        #for i, d in enumerate(dataDict["wref_output"]): save_nifti(os.path.join(filepath, "wref_" + str(i) + ".nii"), d, seq=self.sequence)
        nucleus = None
        for key in ["Nucleus", "nucleus"]:
            if key in self.header:
                nucleus = self.header[key]
                break
        for i, d in enumerate(dataDict["output"]):
            if d is not None:
                # Save the .RAW file as before.
                raw_filepath = os.path.join(filepath, f"{i}.RAW")
                save_raw(raw_filepath, d, seq=self.sequence)
                
                # Now use spec2nii to convert the .RAW file to NIfTI.
                nifti_filepath = save_nifti_spec2nii(raw_filepath, d, nucleus=nucleus, seq=self.sequence)
                if nifti_filepath is not None:
                    utils.log_debug(f"NIfTI file generated: {nifti_filepath}")
                else:
                    utils.log_error(f"Failed to generate NIfTI file for {raw_filepath}")
                
        for i, d in enumerate(dataDict["wref_output"]):
            raw_filepath = os.path.join(filepath, f"wref_{i}.RAW")
            save_raw(raw_filepath, d, seq=self.sequence)
            nifti_filepath = save_nifti_spec2nii(raw_filepath, d, nucleus=nucleus, seq=self.sequence)
            if nifti_filepath is not None:
                utils.log_debug(f"WATER NIfTI file generated: {nifti_filepath}")
            else:
                utils.log_error(f"Failed to generate WATER NIfTI file for {raw_filepath}")


    # canvas plot
    if not self.fast_processing:
        self.matplotlib_canvas.clear()
        step.plot(self.matplotlib_canvas.figure, dataDict)
        self.matplotlib_canvas.draw()
    utils.log_info("Time to plot " + step.__class__.__name__ + ": {:.3f}".format(time.time() - start_time))
    
def saveDataPlot(self):
    if getattr(self, 'skip_manual_adjustment', False):
        if self.issvs:
            filepath = os.path.join(self.outputpath, "Result.pdf")
            figure = matplotlib.figure.Figure(figsize=(12, 9))
            plot_mrs(self.dataSteps[-1], figure)
            figure.suptitle("Result")
            figure.savefig(filepath, dpi=600, format='pdf')
            utils.log_debug("Saved result to " + filepath)
        return

    # 2. Show the same two-button dialog in all modes
    if self.issvs:
        dlg = wx.MessageDialog(None,
                            "Do you want to manually adjust frequency and phase shifts of the result?",
                            "",
                            wx.YES_NO | wx.ICON_INFORMATION)
        button_clicked = dlg.ShowModal()
        dlg.Destroy()

        if button_clicked == wx.ID_YES:
            self.matplotlib_canvas.clear()
            from processing.manual_adjustment import ManualAdjustment
            manual_adjustment = ManualAdjustment(self.dataSteps[-1], self.matplotlib_canvas)
            self.dataSteps.append(manual_adjustment.run())
        else:
            if getattr(self, 'batch_mode', False):
                self.skip_manual_adjustment = True

    if self.issvs:
        filepath = os.path.join(self.outputpath, "Result.pdf")
        figure = matplotlib.figure.Figure(figsize=(12, 9))
        plot_mrs(self.dataSteps[-1], figure)
        figure.suptitle("Result")
        figure.savefig(filepath, dpi=600, format='pdf')
        utils.log_debug("Saved result to " + filepath)


def analyseResults(self):
    results = self.dataSteps[-1]
    #if self.issvs == False:
        

        
    self.basis_file = None

    # Determine nucleus and Larmor frequency
    nucleus = None
    larmor = 0
    for key in ["Nucleus", "nucleus"]:
        if key in self.header.keys():
            nucleus = self.header[key]
            if self.header[key] == "1H": larmor = 42.577
            elif self.header[key] == "31P": larmor = 17.235
            elif self.header[key] == "23Na": larmor = 11.262
            elif self.header[key] == "2H": larmor = 6.536
            elif self.header[key] == "13C": larmor = 10.7084
            elif self.header[key] == "19F": larmor = 40.078
            break

    if nucleus is None:
        utils.log_error("Nucleus information not found in header.")
        return False

    # Conditionally set wresult based on the nucleus
    if nucleus == "1H":
        if self.wrefSteps and len(self.wrefSteps) > 0 and self.wrefSteps[-1] and len(self.wrefSteps[-1]) > 0:
            try:
                if self.wrefSteps[-1][0] is not None:
                    wresult = self.wrefSteps[-1][0].inherit(np.mean(np.array(self.wrefSteps[-1]), axis=0))
                else:
                    utils.log_warning("Last element of wrefSteps[-1][0] is None. Water reference will be ignored.")
                    wresult = None
            except Exception as e:
                utils.log_warning(f"Error processing wrefSteps: {e}. Water reference will be ignored.")
                wresult = None
        else:
            utils.log_warning("wrefSteps is empty or improperly formatted. Water reference will be ignored.")
            wresult = None
    else:
        # For nuclei other than 1H, water reference is not applicable
        wresult = None

    # Basis file generation
    tesla = round(results[0].f0 / larmor, 0)
    basis_file_gen = None
    if self.sequence is not None:
        strte = str(results[0].te)
        if strte.endswith(".0"):
            strte = strte[:-2]
        if nucleus == "31P":
            basis_file_gen = f"{int(tesla)}T_{self.sequence}_31P_TE{strte}ms.BASIS" #basis_file_gen = f"{int(tesla)}T_{self.sequence}_31P_TE{strte}ms.BASIS"
        else:
            basis_file_gen = f"{int(tesla)}T_{self.sequence}_TE{strte}ms.BASIS"
        basis_file_gen = os.path.join(self.programpath, "lcmodel", "basis", basis_file_gen)
    else:
        utils.log_warning("Sequence not found, basis file not generated")

    # Handle user-specified basis file
    if self.basis_file_user is not None:
        if not os.path.exists(self.basis_file_user):
            utils.log_warning("Basis set not found:\n\t", self.basis_file_user)
            self.basis_file = None
        else:
            self.basis_file = self.basis_file_user

    # If no user basis file, check generated basis file
    if self.basis_file is None and basis_file_gen is not None and os.path.exists(basis_file_gen):
        dlg = wx.MessageDialog(
            None, 
            basis_file_gen, 
            "Basis set found, is it the right one?\n" + basis_file_gen, 
            wx.YES_NO | wx.CANCEL | wx.ICON_INFORMATION
        )
        button_clicked = dlg.ShowModal()
        dlg.Destroy()  # Always destroy dialogs after use
        if button_clicked == wx.ID_YES:
            self.basis_file = basis_file_gen
        elif button_clicked == wx.ID_CANCEL:
            return False

    # If still no basis file
    if self.basis_file is None:
        utils.log_warning("Basis set not found:\n\t", basis_file_gen)
        self.fitting_frame.Show()
        self.fitting_frame.SetFocus()
        while self.fitting_frame.IsShown():
            time.sleep(0.1)
        self.basis_file = self.basis_file_user

    if self.basis_file is None:
        utils.log_error("No basis file specified")
        return False

    # Control file handling
    params = None
    if self.control_file_user is not None and os.path.exists(self.control_file_user):
        try:
            params = read_control(self.control_file_user)
        except Exception as e:
            utils.log_warning(f"Error reading user control file: {e}. Attempting to use default control file.")
            params = None
    else:
        if nucleus == "1H":
            self.control_file_user = os.path.join(self.programpath, "lcmodel", "default.CONTROL")
        if nucleus == "31P":
            self.control_file_user = os.path.join(self.programpath, "lcmodel", "31P_default.CONTROL")
        try:
            params = read_control(self.control_file_user)
            if nucleus == "1H":
                params.update({"DOECC": wresult is not None and "EddyCurrentCorrection" not in self.pipeline})
            else:
                params.update({"DOECC": False})
        except Exception as e:
            utils.log_warning(f"Error reading default control file: {e}.")
            params = None
    if params is None:
        utils.log_error("Control file not found or could not be read:\n\t", self.control_file_user)
        return False

    # Handle labels

    if "labels" in dataDict.keys():
        labels = dataDict["labels"]
    else:
        if self.issvs == True:
            labels = [str(i) for i in range(len(results))]
        else:
            labels = [str(i) for i in range(len(results[0]))]

    result_np = np.array(results[0])
    utils.log_info(f"length of results {len(results[0])}")
    utils.log_info(f"shape of results {result_np.shape}")

    # Segmentation and water concentration (only for 1H)
    wconc = None
    if nucleus == "1H" and self.wm_file_user and self.gm_file_user and self.csf_file_user:
        try:
            centre = results[0].centre
        except Exception as e:
            utils.log_error(f"Could not retrieve voxel location from data: {e}")
            return False
        try:
            wm_img = ants.image_read(self.wm_file_user)
            gm_img = ants.image_read(self.gm_file_user)
            csf_img = ants.image_read(self.csf_file_user)
        except Exception as e:
            utils.log_error(f"Could not load segmentation files:\n\t{e}")
            return False

        thickness = np.array([np.max(np.abs(np.array(results[0].transform)[:3, i])) for i in range(3)])
        index1 = ants.transform_physical_point_to_index(wm_img, centre - thickness / 2).astype(int)
        index2 = ants.transform_physical_point_to_index(wm_img, centre + thickness / 2).astype(int)
        for i in range(3):
            if index1[i] > index2[i]:
                index1[i], index2[i] = index2[i], index1[i]
        wm_sum = np.sum(wm_img.numpy()[index1[0]:index2[0], index1[1]:index2[1], index1[2]:index2[2]])
        gm_sum = np.sum(gm_img.numpy()[index1[0]:index2[0], index1[1]:index2[1], index1[2]:index2[2]])
        csf_sum = np.sum(csf_img.numpy()[index1[0]:index2[0], index1[1]:index2[1], index1[2]:index2[2]])
        _sum = wm_sum + gm_sum + csf_sum
        if _sum == 0:
            utils.log_warning("Segmentation sums to zero. Skipping water concentration calculation.")
            wconc = None
        else:
            f_wm = wm_sum / _sum
            f_gm = gm_sum / _sum
            f_csf = csf_sum / _sum
            wconc = (43300 * f_gm + 35880 * f_wm + 55556 * f_csf) / (1 - f_csf)
            utils.log_info(
                "Calculated the following values from the segmentation files:\n\tWM: ", 
                f_wm, 
                " GM: ", 
                f_gm, 
                " CSF: ", 
                f_csf, 
                " → Water concentration: ", 
                wconc
            )
    else:
        if nucleus != "1H":
            utils.log_info("Segmentation and water concentration calculation skipped for nucleus: ", nucleus)
        else:
            utils.log_warning("Segmentation files not provided. Water concentration will be ignored.")

    # Create work folder and copy LCModel executable
    lcmodelfile = os.path.join(self.programpath, "lcmodel", "lcmodel")  # Linux exe
    if os.name == 'nt':
        lcmodelfile += ".exe"  # Windows exe

    utils.log_debug("Looking for executable here: ", lcmodelfile)
    if not os.path.exists(lcmodelfile):
        zippath = os.path.join(self.programpath, "lcmodel", "lcmodel.zip")
        if not os.path.exists(zippath):
            utils.log_error("lcmodel executable or zip not found")
            return False
        utils.log_info("lcmodel executable not found, extracting from zip")
        utils.log_debug("Looking for zip here: ", zippath)
        try:
            with zipfile.ZipFile(zippath, "r") as zip_ref:
                zip_ref.extractall(os.path.join(self.programpath, "lcmodel"))
            utils.log_info("lcmodel executable extracted from zip.")
        except Exception as e:
            utils.log_error(f"Failed to extract lcmodel from zip: {e}")
            return False

    # Setup workpath
    workpath = os.path.join(os.path.dirname(self.outputpath_base), "temp")
    if os.path.exists(workpath):
        shutil.rmtree(workpath)
    os.mkdir(workpath)
    utils.log_debug("LCModel work folder: ", workpath)

    # Copy LCModel executable to workpath
    if os.name == 'nt':
        command = f"""copy "{lcmodelfile}" "{workpath}" """
    else:
        command = f"""cp "{lcmodelfile}" "{workpath}" """
    result_copy = subprocess.run(command, shell=True, capture_output=True, text=True)
    utils.log_debug(f"Copy command output:\n{result_copy.stdout}")
    if result_copy.stderr:
        utils.log_warning(f"Copy command errors:\n{result_copy.stderr}")

    # Setup LCModel save path
    lcmodelsavepath = os.path.join(self.outputpath, "lcmodel")
    if os.path.exists(lcmodelsavepath):
        shutil.rmtree(lcmodelsavepath)
    os.mkdir(lcmodelsavepath)
    utils.log_debug("LCModel output folder: ", lcmodelsavepath)
    
    # Iterate over each result and label
    if self.issvs == True:
        temp_results = results
    else:
        temp_results = results[0]

    

    def processVoxel(result, label):
        """
        All the existing logic needed to handle one voxel (or one spectrum).
        This is essentially the body of your old 'for' loop.
        """

        label = "lcm" if label == "0" else label

        result_label_np = np.array(result)
        utils.log_info(f"shape of result {label}: {result_label_np.shape}")

        # Initialize rparams with uppercase keys only
        # (Same as in your code; just extracted here)
        rparams = {}
        for key in ["Nucleus", "nucleus"]:
            if key in self.header.keys():
                rparams = {
                    "KEY": 123456789,
                    "FILRAW": f"./{label}.raw",
                    "FILBAS": self.basis_file,
                    "FILPRI": f"./{label}.print",
                    "FILTAB": f"./{label}.table",
                    "FILPS": f"./{label}.ps",
                    "FILCOO": f"./{label}.coord",
                    "FILCOR": f"./{label}.coraw",
                    "FILCSV": f"./{label}.csv",
                    "NUNFIL": result.np,
                    "DELTAT": result.dt,
                    "ECHOT": result.te,
                    "HZPPPM": result.f0,
                    "LCOORD": 9,
                    "LCSV": 11,
                    "LTABLE": 7
                }

                # Conditional parameters based on nucleus
                if wresult is not None:
                    rparams.update({
                        "FILH2O": f"./{label}.h2o",
                        "DOWS": "EddyCurrentCorrection" not in self.pipeline  # Use water ref correction if appropriate.
                    })
                    if wconc is not None:
                        rparams.update({"WCONC": wconc})
                else:  # 31P or other
                    rparams.update({"DOWS": False})
                    rparams.pop("FILH2O", None)
                    rparams.pop("WCONC", None)

                # Merge any extra parameters
                if params:
                    params_upper = {k.upper(): v for k, v in params.items()}
                    excluded_keys = [
                        "FILRAW", "FILBAS", "FILPRI", "FILTAB",
                        "FILPS", "FILCOO", "FILCOR", "FILCSV", "FILH2O",
                        "NUNFIL", "DELTAT", "ECHOT", "HZPPM"
                    ]
                    params_filtered = {
                        k: v for k, v in params_upper.items()
                        if k not in excluded_keys
                    }
                    rparams.update(params_filtered)

        # Write CONTROL and RAW files
        try:
            save_control(os.path.join(workpath, f"{label}.CONTROL"), rparams)
            raw_filepath = os.path.join(workpath, f"{label}.RAW")
            save_raw(raw_filepath, result, seq=self.sequence)
            nifti_filepath = save_nifti_spec2nii(raw_filepath, result, nucleus=nucleus, seq=self.sequence)
            if nifti_filepath is not None:
                utils.log_debug(f"NIfTI file generated for {label}: {nifti_filepath}")
            else:
                utils.log_error(f"Failed to generate NIfTI file for {raw_filepath}")
            if nucleus == "1H" and wresult is not None:
                water_raw_filepath = os.path.join(workpath, f"{label}.H2O")
                save_raw(water_raw_filepath, wresult, seq=self.sequence)
                water_nifti_filepath = save_nifti_spec2nii(water_raw_filepath, wresult, nucleus=nucleus, seq=self.sequence)
                if water_nifti_filepath is not None:
                    utils.log_debug(f"Water NIfTI file generated for {label}: {water_nifti_filepath}")
                else:
                    utils.log_error(f"Failed to generate Water NIfTI file for {water_raw_filepath}")
        except Exception as e:
            utils.log_error(f"Error writing CONTROL or RAW files for {label}: {e}")
            return  # skip this voxel

        # Run LCModel
        if os.name == 'nt':
            command = f"""cd "{workpath}" & lcmodel.exe < {label}.CONTROL"""
        else:
            command = f"""cd "{workpath}" && ./lcmodel < {label}.CONTROL"""
        utils.log_info(f"Running LCModel for {label}...")
        utils.log_debug("\n\t" + command)

        try:
            result_lcmodel = subprocess.run(command, shell=True,
                                            capture_output=True, text=True)
            utils.log_debug(f"LCModel Output for {label}:\n{result_lcmodel.stdout}")
            utils.log_debug(f"LCModel Errors for {label}:\n{result_lcmodel.stderr}")

            expected_files = [
                f"{label}.table", f"{label}.ps",
                f"{label}.coord", f"{label}.csv"
            ]
            missing_files = [
                f for f in expected_files
                if not os.path.exists(os.path.join(workpath, f))
            ]
            
            if missing_files:
                utils.log_error(f"Missing LCModel output files for {label}: {missing_files}")
        except Exception as e:
            utils.log_error(f"LCModel execution failed for {label}: {e}")
            return

        if result_lcmodel.returncode != 0:
            utils.log_error(
                f"LCModel failed for {label} with return code {result_lcmodel.returncode}"
            )
            return        

        # Move output files to savepath
        savepath = os.path.join(lcmodelsavepath, label)
        try:
            os.mkdir(savepath)
        except Exception as e:
            utils.log_error(f"Failed to create savepath for {label}: {e}")
            return

        command_move = ""
        for f in os.listdir(workpath):
            if "lcmodel" in f.lower():
                continue
            if os.name == 'nt':
                command_move += f""" & move "{os.path.join(workpath, f)}" "{savepath}" """
            else:
                command_move += f""" && mv "{os.path.join(workpath, f)}" "{savepath}" """

        if command_move:
            command_move = command_move[3:]  # Remove initial ' & ' or ' && '
            utils.log_debug("Moving files...\n\t" + command_move)
            try:
                subprocess.run(command_move, shell=True, check = True)
            except Exception as e:
                utils.log_warning(f"Failed to move files for {label}: {e}")
                utils.log_warning(f"Files remain in the temporary work folder: {workpath}")

        # Handle coord files
        filepath = os.path.join(savepath, f"{label}.coord")
        if os.path.exists(filepath):
            self.last_coord = filepath
            try:
                fcoord = ReadlcmCoord(filepath, nucleus)
                if nucleus == "31P":
                    from processing.add_calculated_metabolites import add_calculated_metabolites
                    add_calculated_metabolites(fcoord)
                figure = matplotlib.figure.Figure(figsize=(10, 10), dpi=600)
                plot_coord(fcoord, figure, title=filepath)
                read_file(filepath, self.matplotlib_canvas, self.file_text)
                filepath_pdf = os.path.join(savepath, "lcmodel.pdf")
                figure.savefig(filepath_pdf, dpi=600, format='pdf')
            except Exception as e:
                utils.log_warning(f"Failed to process coord file for {label}: {e}")
        else:
            utils.log_warning(f"LCModel output not found for {label}")

    if self.issvs:

        for result, label in zip(temp_results, labels):
            processVoxel(result, label)
    else:

        xdim, ydim, zdim, npoints = np.array(temp_results).shape

        for i in range(xdim):
            for j in range(ydim):
                for k in range(zdim):

                    result_data = temp_results[i][j][k]

                    label = "_".join([str(i+1),str(j+1),str(k+1)])

                    processVoxel(result_data, label)

    # Clean up workpath
    try:
        shutil.rmtree(workpath)  # Delete work folder
        utils.log_debug("Workpath deleted successfully.")
    except Exception as e:
        utils.log_warning(f"Failed to delete workpath: {e}")

    utils.log_info("LCModel processing complete")
    return True


def processPipeline(self):
    try:
        if self.current_step == 0:
            wx.CallAfter(self.plot_box.Clear)
            wx.CallAfter(self.plot_box.AppendItems, "")
            if not hasattr(self, 'originalData') or self.originalData is None:
                if not loadInput(self):
                    utils.log_error("Error loading input")
                    wx.CallAfter(self.reset)
                    return
            else:
                utils.log_debug("Skipping loadInput because self.originalData is already loaded.")
            
            
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
    
    except Exception as e:
        tb_str = traceback.format_exc()
        utils.log_error(f"Pipeline error:\n{tb_str}")
        wx.CallAfter(self.button_terminate_processing.Enable)


def autorun_pipeline_exe(self):
    while self.fast_processing and self.current_step <= len(self.steps):
        processPipeline(self)