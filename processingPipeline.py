import os
import suspect
import shutil
import zipfile
import numpy as np
import matplotlib
from readcoord import ReadlcmCoord
import time
import wx
from interface.plots import plot_ima, plot_coord
from suspect import MRSData

from interface.custom_wxwidgets import DROPDOWNMENU_ITEM_IDS

def stop_processing(self):
    self.next = False
    self.processing = False
    self.fast_processing = False
    # self.button_step_processing.SetLabel("Start Processing")
    self.button_step_processing.Enable()
    return

def waitforprocessingbutton(self):
    self.button_step_processing.Enable()
    self.button_auto_processing.Enable()
    # self.processing_throbber.Hide()


    while not self.next:
        if not self.processing: return False
        time.sleep(0.1)
    self.next = False
    return True




def updateprogress(self,current_step,current_step_index,totalstep):
    self.progress_bar_info.SetLabel("Progress ("+str(current_step_index)+ "/"+str(totalstep)+"):"+"\n"+str(current_step_index)+" - "+ current_step.__class__.__name__ )

def updatedropdownstep(self,current_step,current_step_index):
    # self.DDstepselection.AddMenuItem(str(current_step_index)+" - "+current_step.__class__.__name__ )
    print("to")
    # self.Layout()
    
def loadInput(self):
    self.filepaths = []
    for f in self.dt.dropped_file_paths:
        if not f.lower().endswith(".coord"):
            self.filepaths.append(f)
    if len(self.filepaths) == 0:
        self.log_error("No files found")
        # return stop_processing(self)
        return False

    if not self.dt.wrefindex:
        wrefindex = None
        self.log_warning("No water reference found")
    else:
        wrefindex = self.dt.wrefindex

    self.originalData = []
    self.originalWref = None
    for i in range(len(self.filepaths)):
        try:
            if self.filepaths[i].lower().endswith((".ima", ".dcm")):
                data = suspect.io.load_siemens_dicom(self.filepaths[i])
            elif self.filepaths[i].lower().endswith(".dat"):
                data = suspect.io.load_twix(self.filepaths[i])
                data = suspect.processing.channel_combination.combine_channels(data) # temporary?
            else:
                self.log_error("Unsupported file format: " + self.filepaths[i])
                continue

            if i == wrefindex:
                self.originalWref = data
                self.log_info("Water reference loaded: " + self.filepaths[i])
            elif len(data.shape) > 1:
                for d in data:
                    self.originalData.append(data.inherit(d))
            else:
                self.originalData.append(data)
        except: self.log_warning("Error loading file: " + self.filepaths[i])
    if len(self.originalData) == 0:
        self.log_error("No files loaded")
        self.proces_completion = True
        # return stop_processing(self)
        return False
    self.log_info(len(self.originalData), " files loaded")
    
    ##### OUTPUT FOLDERS #####
    self.outputpath = os.path.join(self.rootPath, "output")
    if not os.path.exists(self.outputpath): os.mkdir(self.outputpath)
    prefix = os.path.commonprefix([os.path.basename(f) for f in self.filepaths])
    if prefix == "": prefix = "output"
    self.outputpath = os.path.join(self.rootPath, "output", prefix)
    if not os.path.exists(self.outputpath): os.mkdir(self.outputpath)
    self.lcmodelsavepath = os.path.join(self.outputpath, "lcmodel")
    if os.path.exists(self.lcmodelsavepath): shutil.rmtree(self.lcmodelsavepath)
    os.makedirs(self.lcmodelsavepath)
    self.workpath = os.path.join(self.rootPath, "temp")
    if os.path.exists(self.workpath): shutil.rmtree(self.workpath)
    os.mkdir(self.workpath)
    initializeDataprocessed(self)
    
def initializeDataprocessed(self):
    self.dataSteps: list[MRSData] = [self.originalData]
    self.wrefSteps: list[MRSData] = [self.originalWref]
    self.last_wref = None

def processStep(self,step,nstep):
    dataDict = {
                "input": self.dataSteps[-1],
                "wref": self.last_wref,
                "original": self.dataSteps[0],
                "wref_original": self.wrefSteps[0],
                "output": None,
                "wref_output": None
            }
    # self.processing_throbber.Start()
    # self.processing_throbber.Show()
    self.button_step_processing.Disable()
    if not self.fast_processing:
        self.button_auto_processing.Disable()

    # updateprogressbar(self,step,nstep,len(self.steps))
    self.log_debug("Running ", step.__class__.__name__)
    start_time = time.time()
    step.process(dataDict)
    self.log_debug("\tTime to process " + step.__class__.__name__ + ": {:.3f}".format(time.time() - start_time))
    self.dataSteps.append(dataDict["output"])
    if dataDict["wref_output"] is not None:
        self.wrefSteps.append(dataDict["wref_output"])
    else: self.wrefSteps.append(dataDict["wref"])

    self.log_debug("Plotting ", step.__class__.__name__)
    start_time = time.time()
    steppath = os.path.join(self.outputpath, str(nstep) + step.__class__.__name__)
    if not os.path.exists(steppath): os.mkdir(steppath)
    figure = matplotlib.figure.Figure(figsize=(10, 10))
    # step plot
    step.plot(figure, dataDict)
    figure.suptitle(step.__class__.__name__)
    filepath = os.path.join(steppath, "step.png")
    figure.savefig(filepath, dpi=600)
    self.log_info("Saved "+ str(step.__class__.__name__) +" to " + filepath)
    # data plot
    plot_ima(dataDict["output"], figure)
    figure.suptitle("Result of " + step.__class__.__name__)
    filepath = os.path.join(steppath, "result.png")
    figure.savefig(filepath, dpi=600)
    self.log_info("Saved "+ "Result of " + step.__class__.__name__ +" to " + filepath)
    # canvas plot
    if not self.fast_processing:
        self.matplotlib_canvas.clear()
        step.plot(self.matplotlib_canvas.figure, dataDict)
        self.matplotlib_canvas.draw()
    self.log_debug("\tTime to plot " + step.__class__.__name__ + ": {:.3f}".format(time.time() - start_time))
    
def saveDataPlot(self): 
    for d, name in zip([self.dataSteps[0], self.dataSteps[-1]], ["Original", "Result"]):
        filepath = os.path.join(self.outputpath, name + ".png")
        figure = matplotlib.figure.Figure(figsize=(10, 10), dpi=600)
        plot_ima(d, figure)
        figure.suptitle(name)
        figure.savefig(filepath, dpi=600)
        self.log_info("Saved "+ str(name) +" to " + filepath)
        
def analyseResults(self):
    
    result = self.dataSteps[-1]
    wresult = self.wrefSteps[-1]
    if len(result) == 1: result = result[0] # we want a single MRSData object for analysis
    else: result = result[0].inherit(np.mean(result, axis=0))

    controlfile = os.path.join(self.workpath, "result")
    
    # basis set
    tesla = round(result.f0 / 42.57747892, 0) # larmor frequency in MHz
    if result.te >= 30: sequence = "PRESS" # very advanced detection
    else: sequence = "STEAM"
    strte = str(result.te)
    if strte.endswith(".0"): strte = strte[:-2]
    basisfile = str(int(tesla)) + "T_" + sequence + "_" + str(strte) + "ms.BASIS"

    if not os.path.exists(os.path.join(self.rootPath, "lcmodel", basisfile)):
        self.log_error("Basis set not found:\n\t", basisfile)
        # return stop_processing(self)
        return False

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
    
    suspect.io.lcmodel.write_all_files(controlfile, result, wref_data=wresult, params=params) # write raw, h2o, control files to work folder
    save_raw(os.path.join(self.workpath, "result.RAW"), result, seq=sequence) # overwrite raw file with correct sequence type

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
    shutil.rmtree(self.workpath) # delete work folder

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
    else:
        self.log_warning("LCModel output not found")

    

def processPipeline(self):
    
        
        ##### LOAD INPUT #####
        if self.current_step==0:
            self.pipeline=self.retrievePipeline()
            self.steps = [self.processing_steps[step]() for step in self.pipeline]
            valid_input=loadInput(self)
            if valid_input==False:
                # self.semaphore_step_pro.release()
                return
        
        

        ##### PROCESSING #####
        if 0<=self.current_step and self.current_step<=(len(self.steps)-1):
            processStep(self,self.steps[self.current_step],self.current_step+1)
            self.current_step+=1
        elif self.current_step==(len(self.steps)):
            self.on_save_pipeline(None, os.path.join(self.outputpath, "pipeline.pipe"))
            saveDataPlot(self)
            valid_analysis=analyseResults(self)
            if valid_analysis==False:
                # self.semaphore_step_pro.release()
                return
            self.current_step+=1 ##### to change with a LCModeldone bool 
        else:
            print("Error  Finished, no further steps, to changes this part")
        
        wx.CallAfter(self.PostStepProcessingGUIChanges)

        self.proces_completion = True
        print("yo")
        # self.semaphore_step_pro.release()
        return print("bulleeeeeeet")
           

        # nstep = 0
        # for step in self.steps:
        #     nstep += 1
            # processStep(self,self.steps[self.current_step],self.current_step+1)
            # dataDict = {
            #     "input": self.dataSteps[-1],
            #     "wref": self.last_wref,
            #     "original": self.dataSteps[0],
            #     "wref_original": self.wrefSteps[0],
            #     "output": None,
            #     "wref_output": None
            # }
            # # self.processing_throbber.Start()
            # # self.processing_throbber.Show()
            # self.button_step_processing.Disable()
            # if not self.fast_processing:
            #     self.button_auto_processing.Disable()

            # # updateprogressbar(self,step,nstep,len(self.steps))
            # # self.button_step_processing.SetLabel("Running " + step.__class__.__name__ + "...")
            # self.log_debug("Running ", step.__class__.__name__)
            # step.process(dataDict)
            # self.dataSteps.append(dataDict["output"])
            # if dataDict["wref_output"] is not None:
            #     self.wrefSteps.append(dataDict["wref_output"])
            # else: self.wrefSteps.append(dataDict["wref"])
            # # self.button_step_processing.SetLabel("Plotting " + step.__class__.__name__ + "...")
            # self.log_debug("Plotting ", step.__class__.__name__)

            # filepath = os.path.join(self.stepplotpath, str(nstep) + step.__class__.__name__ + ".png")
            # figure = matplotlib.figure.Figure(figsize=(12, 9), dpi=600)
            # step.plot(figure, dataDict)
            # figure.savefig(filepath, dpi=600)
                
                
            # if not self.fast_processing:
            #     self.matplotlib_canvas.clear()
            #     step.plot(self.matplotlib_canvas.figure, dataDict)
            #     self.matplotlib_canvas.draw()
                    

            # updatedropdownstep(self,step,nstep)
            



            # if not self.fast_processing:
            #     if not waitforprocessingbutton(self):
            #         return stop_processing(self)
                
                
        

                

        ##### SAVING DATA PLOTS #####
        # self.button_step_processing.Disable()
        # self.button_processing.SetLabel("Saving plots...")
        # self.on_save_pipeline(None, os.path.join(self.outputpath, "pipeline.pipe"))

        # saveDataPlot(self)
        
        # if not self.fast_processing:
        #     if not waitforprocessingbutton(self):
        #         return stop_processing(self)


        ##### ANALYSIS #####
        # self.button_step_processing.Disable()        
        # analyseResults(self)

        # return stop_processing(self)

def autorun_pipeline_exe(self):
    while (self.fast_processing and (self.current_step<=(len(self.steps)))):
        processPipeline(self)
        
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