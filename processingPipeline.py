import os
import suspect
import threading
import shutil
import zipfile
import numpy as np
import matplotlib
from readcoord import ReadlcmCoord

from interface.plots import plot_ima, plot_coord
from suspect import MRSData

def processPipeline(self):
        filepaths = []
        for f in self.dt.dropped_file_paths:
            if not f.lower().endswith(".coord"):
                filepaths.append(f)
        if len(filepaths) == 0:
            self.log_error("No files found")
            self.button_processing.SetLabel("Start Processing")
            self.processing = False
            return

        if not self.dt.wrefindex:
            wrefindex = None
            self.log_warning("No water reference found")
        else:
            wrefindex = self.dt.wrefindex

        originalData = []
        originalWref = None
        for i in range(len(filepaths)):
            try:
                if filepaths[i].lower().endswith((".ima", ".dcm")):
                    data = suspect.io.load_siemens_dicom(filepaths[i])
                elif filepaths[i].lower().endswith(".dat"):
                    data = suspect.io.load_twix(filepaths[i])
                    data = suspect.processing.channel_combination.combine_channels(data) # temporary?
                else:
                    self.log_error("Unsupported file format: " + filepaths[i])
                    continue

                if i == wrefindex:
                    originalWref = data
                    self.log_info("Water reference loaded:" + filepaths[i])
                elif len(data.shape) > 1:
                    for d in data:
                        originalData.append(data.inherit(d))
                else:
                    originalData.append(data)
            except: self.log_warning("Error loading file: " + filepaths[i])
        if len(originalData) == 0:
            self.log_error("No files loaded")
            self.button_processing.SetLabel("Start Processing")
            self.processing = False
            return
        self.log_info(len(originalData), " files loaded")
        
        outputpath = os.path.join(self.rootPath, "output")
        if not os.path.exists(outputpath): os.mkdir(outputpath)
        outputpath = os.path.commonprefix([os.path.basename(f) for f in filepaths])
        if outputpath == "": outputpath = "output"
        outputpath = os.path.join(self.rootPath, "output", outputpath)
        if not os.path.exists(outputpath): os.mkdir(outputpath)
        stepplotpath = os.path.join(outputpath, "stepplots")
        if not os.path.exists(stepplotpath): os.mkdir(stepplotpath)

        ##### PROCESSING #####
        def plotWorker(step, dataDict, nstep):
            self.matplotlib_canvas.clear()
            step.plot(self.matplotlib_canvas.figure, dataDict)
            if not self.fast_processing: self.matplotlib_canvas.draw()
            filepath = os.path.join(stepplotpath, str(nstep) + step.__class__.__name__ + ".png")
            figure = matplotlib.figure.Figure(figsize=(12, 9), dpi=600)
            step.plot(figure, dataDict)
            figure.savefig(filepath, dpi=600)
        plotThread = None

        self.dataSteps: list[MRSData] = [originalData]
        self.wrefSteps: list[MRSData] = [originalWref]
        last_wref = None

        nstep = 0
        for step in self.steps:
            nstep += 1
            if originalWref is not None:
                for w in reversed(self.wrefSteps): # find the first non-None wref
                    if w is not None:
                        last_wref = w
                        break
            dataDict = {
                "input": self.dataSteps[-1],
                "wref": last_wref,
                "original": self.dataSteps[0],
                "wref_original": self.wrefSteps[0],
                "output": None,
                "wref_output": None
            }
            self.button_processing.Disable()
            self.button_processing.SetLabel("Running " + step.__class__.__name__ + "...")
            self.log_debug("Processing step: ", step.__class__.__name__)
            step.process(dataDict)
            self.dataSteps.append(dataDict["output"])
            self.wrefSteps.append(dataDict["wref_output"]) # might append None; we need this to keep a history of steps while saving memory

            if plotThread is not None and plotThread.is_alive(): # wait for previous plotting/saving to finish
                self.button_processing.SetLabel("Waiting for plot of previous step...")
                plotThread.join()
            plotThread = threading.Thread(target=plotWorker, args=(step, dict(dataDict), nstep)) # copy dataDict since it will be immediately modified by the next step
            plotThread.start()
            
            if not self.fast_processing: self.waitforprocessingbutton("Next")

        if plotThread is not None: plotThread.join() # wait for last step plot to finish

        ##### SAVING DATA PLOTS #####
        self.button_processing.Disable()
        self.button_processing.SetLabel("Saving plots...")
        dataplotpath = os.path.join(outputpath, "dataplots")
        if not os.path.exists(dataplotpath): os.makedirs(dataplotpath)

        def plotWorker2(data, filepath): # apparently matplotlib is not thread safe, but this works
            figure = matplotlib.figure.Figure(figsize=(10, 10), dpi=600)
            plot_ima(data, figure)
            figure.suptitle(filepath.rsplit(os.path.sep, 1)[-1][:-4])
            figure.savefig(filepath, dpi=600)

        index = 0
        plotthreads = []
        for d in self.dataSteps: # save dataplots (time + freq for each intermediate output)
            if index == 0: filename = "Original.png"
            elif index-1 < len(self.steps): filename = str(index) + self.steps[index-1].__class__.__name__ + ".png"
            else: filename = "Result.png"
            filepath = os.path.join(dataplotpath, filename)
            plotthreads.append(threading.Thread(target=plotWorker2, args=(d, filepath)))
            plotthreads[-1].start()
            index += 1
        for t in plotthreads: t.join()

        result = self.dataSteps[-1]
        wresult = None
        if originalWref is not None:
            for w in reversed(self.wrefSteps): # find the first non-None wref
                if w is not None:
                    wresult = w
                    break
        if len(result) == 1: result = result[0] # we want a single MRSData object for analysis
        else: result = result[0].inherit(np.mean(result, axis=0))

        self.waitforprocessingbutton("Run LCModel")

        ##### ANALYSIS #####
        self.button_processing.Disable()
        self.button_processing.SetLabel("Running LCModel...")
        workpath = os.path.join(self.rootPath, "temp")
        controlfile = os.path.join(workpath, "result")
        
        # basis set
        tesla = round(result.f0 / 42.57747892, 0) # larmor frequency in MHz
        if result.te >= 30: sequence = "PRESS" # very advanced detection
        else: sequence = "STEAM"
        strte = str(result.te)
        if strte.endswith(".0"): strte = strte[:-2]
        basisfile = str(int(tesla)) + "T_" + sequence + "_" + str(strte) + "ms.BASIS"

        if not os.path.exists(os.path.join(self.rootPath, "lcmodel", basisfile)):
            self.log_error("Basis set not found:\n\t", basisfile)
            self.processing = False
            self.button_processing.SetLabel("Start Processing")
            self.button_processing.Enable()
            return

        params = {
            "FILBAS": "../lcmodel/" + basisfile,
            "FILCSV": "./result.csv",
            "FILCOO": "./result.coord",
            "FILPS": "./result.ps",
            "LCSV": 11,
            "LCOORD": 9,
            "LPS": 8,
            "DOECC": wresult is not None and "EddyCurrentCorrection" not in self.pipeline,
            "DOWS": wresult is not None,
            "NUNFIL": result.np,
            "DELTAT": result.dt,
            "ECHOT": result.te,
            "HZPPPM": result.f0,
            "DOREFS": True,
            "VITRO": False,
            "NUSE1": 4,
            "CHUSE1(1)": "NAA",
            "CHUSE1(2)": "Cr",
            "CHUSE1(3)": "Glu",
            "CHUSE1(4)": "Ins",
            "PPMST": 4.2,
            "PPMEND": 0.2,
            "RFWHM": 1.8,
            "ATTH2O": 0.8187,
            "ATTMET": 0.8521,
            "NCOMBI": 0,
            "CONREL": 8.0,
            "DKNTMN": 0.25,
            "WCONC": 44444,
            "NEACH": 999,
            "NSIMUL": 0,
            "NCALIB": 0,
            "PGNORM": "US"
        }
        
        if os.path.exists(workpath): shutil.rmtree(workpath) # delete work folder
        os.mkdir(workpath)
        for f in os.listdir(outputpath): # delete old lcmodel outputs
            filepath = os.path.join(outputpath, f)
            if os.path.isfile(filepath): os.remove(filepath)
        
        suspect.io.lcmodel.write_all_files(controlfile, result, wref_data=wresult, params=params) # write raw, h2o, control files to work folder
        save_raw(os.path.join(workpath, "result.RAW"), result, seq=sequence) # overwrite raw file with correct sequence type

        lcmodelfile = os.path.join(self.rootPath, "lcmodel", "lcmodel") # linux exe
        if os.name == 'nt': lcmodelfile += ".exe" # windows exe

        self.log_info("Looking for executable here: ", lcmodelfile)
        if not os.path.exists(lcmodelfile): # lcmodel executables are zipped in the repo because of size
            zippath = os.path.join(self.rootPath, "lcmodel", "lcmodel.zip")
            if not os.path.exists(zippath):
                self.log_error("lcmodel executable or zip not found")
                pass
            self.log_info("lcmodel executable not found, extracting from zip here: ", zippath)
            with zipfile.ZipFile(zippath, "r") as zip_ref:
                zip_ref.extractall(os.path.join(self.rootPath, "lcmodel"))

        if os.name == 'nt': command = f"""mkdir {workpath} & copy {lcmodelfile} {workpath} & cd {workpath} & lcmodel.exe < result_sl0.CONTROL & del lcmodel.exe"""
        else: command = f"""mkdir {workpath} && cp {lcmodelfile} {workpath} && cd {workpath} && ./lcmodel < control_sl0.CONTROL && rm lcmodel"""
        self.log_debug("Running LCModel...\n\t", command)
        os.system(command)
        
        command = ''
        for f in os.listdir(workpath):
            if os.name == 'nt': command += f" & move {os.path.join(workpath, f)} {outputpath}"
            else: command += f" && mv {os.path.join(workpath, f)} {outputpath}"
        command = command[3:]
        self.log_debug("Moving files...\n\t", command)
        os.system(command)
        shutil.rmtree(workpath) # delete work folder

        # plot to canvas
        filepath = os.path.join(outputpath, "result.coord")
        if os.path.exists(filepath):
            self.matplotlib_canvas.clear()
            self.read_file(None, filepath)
            self.matplotlib_canvas.draw()
            # save to file with a fixed size
            f = ReadlcmCoord(filepath)
            figure = matplotlib.figure.Figure(figsize=(10, 10), dpi=600)
            filepath = os.path.join(outputpath, "lcmodel.png")
            plot_coord(f, figure, title=filepath)
            figure.savefig(filepath, dpi=600)
        else:
            self.log_warning("LCModel output not found")

        self.processing = False
        self.next = False
        self.button_processing.SetLabel("Start Processing")
        self.button_processing.Enable()
        return

# adapted from suspect.io.lcmodel.save_raw because it gets SEQ errors
def save_raw(filename, data, seq="PRESS"):
    with open(filename, 'w') as fout:
        fout.write(" $SEQPAR\n")
        fout.write(" ECHOT = {}\n".format(data.te))
        fout.write(" HZPPPM = {}\n".format(data.f0))
        fout.write(f" SEQ = {seq}\n")
        fout.write(" $END\n")
        fout.write(" $NMID\n")
        fout.write(" FMTDAT = '(2E15.6)'\n")
        if data.transform is not None: fout.write(" VOLUME = {}\n".format(data.voxel_volume() * 1e-3))
        # else: print("Saving LCModel data without a transform, using default voxel volume of 1ml")
        fout.write(" $END\n")
        for point in np.nditer(data, order='C'):
            fout.write("  {0: 4.6e}  {1: 4.6e}\n".format(float(point.real), float(point.imag)))