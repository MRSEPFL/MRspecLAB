import wx
import os
import glob
import inspect
import importlib.util
import zipfile
import shutil
import threading
import numpy as np
import suspect

from . import wxglade_out
from readcoord import ReadlcmCoord

class MyFrame(wxglade_out.MyFrame):

    def __init__(self, *args, **kwds):
        wxglade_out.MyFrame.__init__(self, *args, **kwds)
        processing_files = glob.glob(os.path.join(os.path.dirname(__file__), "processing", "*.py"))
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

    def on_button_processing(self, event):
        thread = threading.Thread(target=self.processPipeline, args=())
        thread.start()
        event.Skip()

    def on_read_coord(self, event):
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "result.coord")
        lcmdata = ReadlcmCoord(filepath)
        self.matplotlib_canvas.clear()
        ax = self.matplotlib_canvas.figure.add_subplot(1, 1, 1)
        
        def getOffset(data):
            return 1.1 * max(data) - min(data)
        
        ax.plot(lcmdata['ppm'], lcmdata['residue'], 'b-')
        ax.text(4.25, np.mean(lcmdata["residue"]), "Residue", rotation=0, va='center', ha='right', color='b')
        
        specHeight = max(getOffset(lcmdata['spec']), getOffset(lcmdata['fit']))
        offset = specHeight
        ax.plot(lcmdata['ppm'], [x - offset for x in lcmdata['spec']], 'k-', label="Spectrum")
        ax.plot(lcmdata['ppm'], [x - offset for x in lcmdata['fit']], 'r-', label="Fit")
        ax.text(4.25, np.mean(lcmdata["fit"]) - offset, "Fit", rotation=0, va='center', ha='right', color='r')

        offset += getOffset(lcmdata['baseline'])
        ax.plot(lcmdata['ppm'], [x - offset for x in lcmdata['baseline']], 'b-', label="Baseline")
        ax.text(4.25, np.mean(lcmdata["baseline"]) - offset, "Baseline", rotation=0, va='center', ha='right', color='b')

        offset += getOffset(lcmdata['subspec'][0])
        for i, (metab, subspec) in enumerate(zip(lcmdata['metab'], lcmdata['subspec'])):
            ax.plot(lcmdata['ppm'], [x - offset for x in subspec], 'k-', label=metab)
            ax.text(4.25, -offset, metab, rotation=0, va='center', ha='right', color='k')
            offset += 0.1 * specHeight

        ax.set_xlabel('ppm')
        ax.set_xlim((4.2, 1))
        ax.get_yaxis().set_visible(False)
        
        self.matplotlib_canvas.figure.suptitle(filepath)
        self.matplotlib_canvas.figure.tight_layout()
        self.matplotlib_canvas.draw()
        event.Skip()

    def processPipeline(self):
        filepaths = self.dt.dropped_file_paths
        if len(filepaths) == 0:
            print("No files dropped")
            return
        print("\n".join(filepaths))
        datas = []
        wref = None
        for file in filepaths:
            if file.find("0037.0001") != -1: # unsuppressed water reference
                wref = suspect.io.load_siemens_dicom(file)
                continue
            try: datas.append(suspect.io.load_siemens_dicom(file))
            except: print("Error loading dicom file: " + file)
    	
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
            input("Press enter to continue")
        
        plotThread = None
        for step in steps:
            datas = step._process(datas) # process and save output in step if saveOutput is True
            if plotThread is not None: plotThread.join() # wait for previous plot to finish
            plotThread = threading.Thread(target=plotWorker, args=(step,)) # plot in a separate thread so we can continue processing
            plotThread.start() # /!\ matplotlib is not thread safe, so we shouldn't plot multiple things in parallel
        plotThread.join() # wait for last plot to finish

        if len(datas) == 1: result = datas[0] # we want a single MRSData object for analysis
        else: result = datas[0].inherit(np.mean(datas, axis=0))

        ##### ANALYSIS #####
        outputdir = os.path.join(os.path.dirname(__file__), "output")
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

        lcmodelfile = os.path.join(os.path.dirname(__file__), "lcmodel", "lcmodel") # linux exe
        if os.name == 'nt': lcmodelfile += ".exe" # windows exe

        print("Looking for executable here: ", lcmodelfile)
        if not os.path.exists(lcmodelfile): # lcmodel executables are zipped in the repo because of size
            zippath = os.path.join(os.path.dirname(__file__), "lcmodel", "lcmodel.zip")
            if not os.path.exists(zippath):
                print("lcmodel executable or zip not found")
                pass
            print("lcmodel executable not found, extracting from zip here: ", zippath)
            with zipfile.ZipFile(zippath, "r") as zip_ref:
                zip_ref.extractall(os.path.join(os.path.dirname(__file__), "lcmodel"))

        if os.name == 'nt': command = f"""mkdir {outputdir} & copy {lcmodelfile} {outputdir} & cd {outputdir} & lcmodel.exe < control_sl0.CONTROL & del lcmodel.exe"""
        else: command = f"""mkdir {outputdir} && cp {lcmodelfile} {outputdir} && cd {outputdir} && ./lcmodel < control_sl0.CONTROL && rm lcmodel"""
        print(command)
        os.system(command)

        ##### PLOTTING #####
        self.matplotlib_canvas.clear()
        ax = self.matplotlib_canvas.figure.add_subplot(2, 1, 1)
        ax.plot(result.time_axis(), np.absolute(result))
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Signal Intensity')
        ax = self.matplotlib_canvas.figure.add_subplot(2, 1, 2)
        ax.plot(result.frequency_axis_ppm(), result.spectrum())
        ax.set_xlabel('Frequency (ppm)')
        ax.set_ylabel('Amplitude')
        self.matplotlib_canvas.figure.suptitle("Result")
        self.matplotlib_canvas.figure.tight_layout()
        self.matplotlib_canvas.draw()
        
        input("Press enter to continue")
        self.on_read_coord(None)

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True