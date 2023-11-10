import os
import suspect
import threading
import shutil
import zipfile
import numpy as np

from interface.plots import plot_ima
from suspect import MRSData

def processPipeline(self):
        filepaths = []
        for f in self.dt.dropped_file_paths:
            if not f.lower().endswith(".coord"):
                filepaths.append(f)
        if len(filepaths) == 0:
            print("No files found")
            self.button_processing.SetLabel("Start Processing")
            self.processing = False
            return

        if not self.dt.wrefindex:
            wrefindex = None
            print("No water reference found")
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
                    print("Unsupported file format: " + filepaths[i])
                    continue

                if i == wrefindex:
                    originalWref = data
                    print("Water reference loaded:" + filepaths[i])
                elif len(data.shape) > 1:
                    for d in data:
                        originalData.append(data.inherit(d))
                else:
                    originalData.append(data)
            except: print("Error loading file: " + filepaths[i])
        if len(originalData) == 0:
            print("No files loaded")
            self.button_processing.SetLabel("Start Processing")
            self.processing = False
            return
        print(len(originalData), " files loaded")
        
        plotPath = os.path.commonprefix([os.path.basename(f) for f in filepaths])
        if plotPath == "": plotPath = "plots"
        plotPath = os.path.join(self.rootPath, plotPath)
        if not os.path.exists(plotPath): os.makedirs(plotPath)

        ##### PROCESSING #####
        def plotWorker(step, dataDict, nstep): # /!\ matplotlib is not thread safe, so we shouldn't plot multiple things in parallel
            self.matplotlib_canvas.clear()
            step.plot(self.matplotlib_canvas, dataDict)
            filepath = os.path.join(plotPath, str(nstep) + step.__class__.__name__ + ".png")
            self.savefigure(self.matplotlib_canvas.figure, filepath, size=(12, 9), dpi=600)
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
            print("Processing step: ", step.__class__.__name__)
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

        ##### SAVING PLOTS #####
        self.button_processing.Disable()
        self.button_processing.SetLabel("Saving plots...")
        dataplotpath = os.path.join(plotPath, "dataplots")
        if not os.path.exists(dataplotpath): os.makedirs(dataplotpath)
        index = 0
        for d in self.dataSteps: # save plots
            plot_ima(d, self.matplotlib_canvas)
            if index == 0: filepath = os.path.join(dataplotpath, "Original.png")
            elif index-1 < len(self.steps): filepath = os.path.join(dataplotpath, str(index) + self.steps[index-1].__class__.__name__ + ".png")
            else: filepath = os.path.join(dataplotpath, "Result.png")
            self.savefigure(self.matplotlib_canvas.figure, filepath, size=(10, 10), dpi=600)
            index += 1

        result = self.dataSteps[-1]
        wresult = None
        if originalWref is not None:
            for w in reversed(self.wrefSteps): # find the first non-None wref
                if w is not None:
                    wresult = w
                    break
        if len(result) == 1: result = result[0] # we want a single MRSData object for analysis
        else: result = result[0].inherit(np.mean(result, axis=0))

        self.waitforprocessingbutton("Next")

        ##### ANALYSIS #####
        if wresult is not None:
            self.button_processing.Disable()
            self.button_processing.SetLabel("Running LCModel...")
            outputdir = os.path.join(self.rootPath, "output")
            controlfile = os.path.join(outputdir, "control")
            params = {
                "FILBAS": "../lcmodel/7T_SIM_STEAM_TE4p5_TM25_mod.BASIS",
                "FILCSV": "./result.csv",
                "FILCOO": "./result.coord",
                "FILPS": "./result.ps",
                "LCSV": 11,
                "LCOORD": 9,
                "LPS": 8,
                "DOECC": False,
                "DOWS": True,
                "DOREFS": True,
                "VITRO": False,
                "PPMST": 4.2,
                "PPMEND": 0.2,
                "RFWHM": 1.8,
                "ECHOT": 16.0,
                "ATTH2O": 0.8187,
                "ATTMET": 0.8521,
                "NCOMBI": 5,
                "DELTAT": 2.5e-04,
                "CONREL": 8.0,
                "DKNTMN": 0.25,
                "HZPPPM": 2.9721e+02,
                "WCONC": 44444,
                "NEACH": 999,
                "NUNFIL": 2048,
                "NSIMUL": 0,
                "NCALIB": 0,
                "PGNORM": "US"
            }
            if os.path.exists(outputdir):
                shutil.rmtree(outputdir) # delete output folder content
            suspect.io.lcmodel.write_all_files(controlfile, result, wref_data=wresult, params=params) # write raw, h2o, control files to output folder

            lcmodelfile = os.path.join(self.rootPath, "lcmodel", "lcmodel") # linux exe
            if os.name == 'nt': lcmodelfile += ".exe" # windows exe

            print("Looking for executable here: ", lcmodelfile)
            if not os.path.exists(lcmodelfile): # lcmodel executables are zipped in the repo because of size
                zippath = os.path.join(self.rootPath, "lcmodel", "lcmodel.zip")
                if not os.path.exists(zippath):
                    print("lcmodel executable or zip not found")
                    pass
                print("lcmodel executable not found, extracting from zip here: ", zippath)
                with zipfile.ZipFile(zippath, "r") as zip_ref:
                    zip_ref.extractall(os.path.join(self.rootPath, "lcmodel"))

            if os.name == 'nt': command = f"""mkdir {outputdir} & copy {lcmodelfile} {outputdir} & cd {outputdir} & lcmodel.exe < control_sl0.CONTROL & del lcmodel.exe"""
            else: command = f"""mkdir {outputdir} && cp {lcmodelfile} {outputdir} && cd {outputdir} && ./lcmodel < control_sl0.CONTROL && rm lcmodel"""
            print(command)
            os.system(command)

            self.read_file(None, os.path.join(outputdir, "result.coord"))
            filepath = os.path.join(plotPath, "lcmodel.png")
            self.savefigure(self.matplotlib_canvas.figure, filepath, size=(8, 8), dpi=600)

        self.processing = False
        self.next = False
        self.button_processing.SetLabel("Start Processing")
        self.button_processing.Enable()
        return