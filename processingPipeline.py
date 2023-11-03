import os
import glob
import suspect
import numpy as np
import scipy
import matplotlib.pyplot as plt
import threading
import time
import shutil
import zipfile

from interface import plots

def processPipeline(self):
        filepaths = []
        for f in self.dt.dropped_file_paths:
            if f.lower().endswith(".ima") or f.lower().endswith(".dcm"):
                filepaths.append(f)
        if len(filepaths) == 0:
            print("No files found")
            self.button_processing.SetLabel("Start Processing")
            self.processing = False
            return
            # print("Files found: " + ", ".join(filepaths))

        if not self.dt.wrefindex:
            wrefindex = None
            print("No water reference found")
        else:
            wrefindex = self.dt.wrefindex

        datas = []
        wref = None
        for i in range(len(filepaths)):
            try:
                data = suspect.io.load_siemens_dicom(filepaths[i])
                if i == wrefindex:
                    wref = data
                    print("Water reference loaded:" + filepaths[i])
                else:
                    datas.append(data)
            except: print("Error loading dicom file: " + filepaths[i])
    	
        print(len(datas), "dicoms loaded")

        # cols = 8
        # fig, axs = plt.subplots(int(np.ceil(len(dicoms)/cols)), cols, figsize=(8, 8))
        # fig.suptitle('Dicoms')
        # for i, d in enumerate(dicoms):
        #     axs[i//cols, i%cols].plot(d.time_axis(), np.absolute(d))
        #     axs[i//cols, i%cols].set_title(f"Dicom {i+1}")
        #     axs[i//cols, i%cols].set_xlabel('Time (s)')
        #     axs[i//cols, i%cols].set_ylabel('Signal Intensity')
        # plt.show()

        ##### PROCESSING #####

        
        def plotWorker(step):
            self.matplotlib_canvas.clear()
            step.plot(self.matplotlib_canvas)
            while not self.next: time.sleep(0.1)
            self.next = False
        
        plotThread = None
        for step in self.steps:
            datas = step._process(datas) # process and save output in step if saveOutput is True
            if plotThread is not None: plotThread.join() # wait for previous plot to finish
            plotThread = threading.Thread(target=plotWorker, args=(step,)) # plot in a separate thread so we can continue processing
            plotThread.start() # /!\ matplotlib is not thread safe, so we shouldn't plot multiple things in parallel
        if plotThread is not None: plotThread.join() # wait for last plot to finish

        if len(datas) == 1: result = datas[0] # we want a single MRSData object for analysis
        else: result = datas[0].inherit(np.mean(datas, axis=0))
        plots.plot_ima(result, self.matplotlib_canvas)

        ##### ANALYSIS #####
        if wref is not None:
            self.button_processing.Disable()
            mainpath = os.path.dirname(__file__)
            outputdir = os.path.join(mainpath, "output")
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
                shutil.rmtree(outputdir) # delete output folder
            suspect.io.lcmodel.write_all_files(controlfile, result, wref_data=wref, params=params) # write raw, h2o, control files to output folder

            lcmodelfile = os.path.join(mainpath, "lcmodel", "lcmodel") # linux exe
            if os.name == 'nt': lcmodelfile += ".exe" # windows exe

            print("Looking for executable here: ", lcmodelfile)
            if not os.path.exists(lcmodelfile): # lcmodel executables are zipped in the repo because of size
                zippath = os.path.join(mainpath, "lcmodel", "lcmodel.zip")
                if not os.path.exists(zippath):
                    print("lcmodel executable or zip not found")
                    pass
                print("lcmodel executable not found, extracting from zip here: ", zippath)
                with zipfile.ZipFile(zippath, "r") as zip_ref:
                    zip_ref.extractall(os.path.join(mainpath, "lcmodel"))

            if os.name == 'nt': command = f"""mkdir {outputdir} & copy {lcmodelfile} {outputdir} & cd {outputdir} & lcmodel.exe < control_sl0.CONTROL & del lcmodel.exe"""
            else: command = f"""mkdir {outputdir} && cp {lcmodelfile} {outputdir} && cd {outputdir} && ./lcmodel < control_sl0.CONTROL && rm lcmodel"""
            print(command)
            os.system(command)

            self.button_processing.Enable()
            while not self.next: time.sleep(0.1)
            self.processing = False
            self.next = False
            self.button_processing.SetLabel("Start Processing")
            self.read_file(None, os.path.join(outputdir, "result.coord"))
            return