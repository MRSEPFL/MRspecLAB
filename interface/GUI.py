import wx
import os
import time
import glob
import inspect
import importlib.util
import zipfile
import shutil
import threading
import numpy as np
import suspect

from . import wxglade_out
from .plots import plot_ima, plot_coord
from readcoord import ReadlcmCoord

class MyFrame(wxglade_out.MyFrame):

    def __init__(self, *args, **kwds):
        wxglade_out.MyFrame.__init__(self, *args, **kwds)
        processing_files = glob.glob(os.path.join(os.path.dirname(__file__), os.pardir, "processing", "*.py"))
        self.processing_steps = {}
        for file in processing_files:
            module_name = os.path.basename(file)[:-3]
            if module_name != "__init__":
                spec = importlib.util.spec_from_file_location(module_name, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and obj.__module__ == module_name:
                        obj = getattr(module, name)
                        self.processing_steps[name] = obj
        
        self.pipeline = ["ZeroPadding", "LineBroadening", "FreqPhaseAlignment", "RemoveBadAverages", "Average"]
        self.CreateStatusBar(1)
        self.SetStatusText("Current pipeline: " + " → ".join(self.pipeline))
        self.processing = False
        self.next = False

    def on_read_ima(self, event):
        wildcard = "IMA files (*.ima)|*.ima|DICOM files (*.dcm)|*.dcm"
        fileDialog = wx.FileDialog(self, "Choose a file", wildcard=wildcard, defaultDir=os.path.dirname(os.path.dirname(__file__)), style=wx.FD_OPEN | wx.FD_MULTIPLE)
        if fileDialog.ShowModal() == wx.ID_CANCEL: return
        filepaths = fileDialog.GetPaths()
        files = []
        for filepath in filepaths:
            if filepath == "" or not os.path.exists(filepath):
                print(f"File not found:\n\t{filepath}")
            else: files.append(filepath)
        self.dt.OnDropFiles(None, None, files)
        event.Skip()

    def on_button_processing(self, event):
        if not self.processing:
            self.processing = True
            self.next = False
            self.button_processing.SetLabel("Next")
            thread = threading.Thread(target=self.processPipeline, args=())
            thread.start()
        else:
            self.next = True
        event.Skip()

    def on_read_coord(self, event, filepath=None):
        if filepath is None:
            wildcard = "coord files (*.coord)|*.coord"
            filepath = wx.FileSelector("Choose a file", wildcard=wildcard, default_path=os.path.dirname(os.path.dirname(__file__)))
        if filepath == "" or not os.path.exists(filepath):
            print("File not found")
            return
        f = ReadlcmCoord(filepath)
        plot_coord(f, self.matplotlib_canvas, title=filepath)
        dtab = '\n\t\t'
        self.infotext.SetValue("")
        self.infotext.WriteText(f"File: {filepath}\n\tNumber of points: {len(f['ppm'])}\n\tNumber of metabolites: {len(f['conc'])} ({f['nfit']} fitted)\n"
                                + f"\t0th-order phase: {f['ph0']}\n\t1st-order phase: {f['ph1']}\n\tFWHM: {f['linewidth']}\n\tSNR: {f['SNR']}\n\tData shift: {f['datashift']}\n"
                                + f"""\tMetabolites:\n\t\t{dtab.join([f"{c['name']}: {c['c']} (±{c['SD']}%, Cr: {c['c_cr']})" for c in f['conc']])}\n""")
        event.Skip()

    def on_select(self, event):
        index = self.drag_and_drop_list.GetSelection()
        if index == wx.NOT_FOUND:
            return
        filepath = self.dt.dropped_file_paths[index]
        if filepath == "" or not os.path.exists(filepath):
            print("File not found")
            return
        f = suspect.io.load_siemens_dicom(filepath)
        plot_ima(f, self.matplotlib_canvas, title=filepath)
        self.infotext.SetValue("")
        self.infotext.WriteText(f"File: {filepath}\n\tNumber of points: {f.np}\n\tScanner frequency (Hz): {f.f0}\n\tDwell time (s): {f.dt}\n\tFrequency delta (Hz): {f.df}\n"
                               + f"\tSpectral Width (Hz): {f.sw}\n\tEcho time (ms): {f.te}\n\tRepetition time (ms): {f.tr}\n"
                               + f"\tPPM range: {[f.hertz_to_ppm(-f.sw / 2.0), f.hertz_to_ppm(f.sw / 2.0)]}\n\tCentre: {f.centre}\n"
                               + "\tMetadata: " + "\n\t\t".join([f"{k}: {v}" for k, v in f.metadata.items()]))
        event.Skip()

    def processPipeline(self):
        if not self.dt.dropped_file_paths or len(self.dt.dropped_file_paths) == 0:
            print("No files found")
            return
        else:
            filepaths = self.dt.dropped_file_paths
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
        steps = [] # instantiate the processing steps to keep their parameters, processedData etc.
        for step in self.pipeline:
            if step not in self.processing_steps.keys():
                print(f"Processing step {step} not found")
                continue
            steps.append(self.processing_steps[step]())
        
        def plotWorker(step):
            self.matplotlib_canvas.clear()
            step.plot(self.matplotlib_canvas)
            while not self.next: time.sleep(0.1)
            self.next = False
        
        plotThread = None
        for step in steps:
            datas = step._process(datas) # process and save output in step if saveOutput is True
            if plotThread is not None: plotThread.join() # wait for previous plot to finish
            plotThread = threading.Thread(target=plotWorker, args=(step,)) # plot in a separate thread so we can continue processing
            plotThread.start() # /!\ matplotlib is not thread safe, so we shouldn't plot multiple things in parallel
        if plotThread is not None: plotThread.join() # wait for last plot to finish

        if len(datas) == 1: result = datas[0] # we want a single MRSData object for analysis
        else: result = datas[0].inherit(np.mean(datas, axis=0))
        plot_ima(result, self.matplotlib_canvas)

        ##### ANALYSIS #####
        if wref is not None:
            self.button_processing.Disable()
            mainpath = os.path.dirname(os.path.dirname(__file__))
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
            self.next = False
            self.button_processing.SetLabel("Start Processing")
            plot_coord(os.path.join(outputdir, "result.coord"), self.matplotlib_canvas)

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True