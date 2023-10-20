import wx
import wxglade_out
import os
import glob
import inspect
import importlib.util
import matplotlib_canvas

import suspect




    
class MyFrame(wxglade_out.MyFrame):


    def on_button_processing(self, event):
        
        
        dicom_files=self.dt.dropped_file_paths
        print(dicom_files)

        dicoms = []
        wref = None
        for file in dicom_files:
            if file.find("0037.0001") != -1: # unsuppressed water reference
                wref = suspect.io.load_siemens_dicom(file)
                continue
            try: dicoms.append(suspect.io.load_siemens_dicom(file))
            except: print("Error loading dicom file: " + file)



        ##### PROCESSING #####
        pipeline = ["yeet", "Average"]
        result = dicoms
        for step in pipeline:
            if step not in self.processing_steps.keys():
                print(f"Processing step {step} not found")
                continue
            result = self.processing_steps[step]().process(result)



        ##### ANALYSIS #####
        import os
        import zipfile
        import shutil

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
            "DOECC": False
        }

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

        if os.name == 'nt': command = f"""copy {lcmodelfile} {outputdir} & cd {outputdir} & lcmodel.exe < control_sl0.CONTROL & del lcmodel.exe"""
        else: command = f"""cp {lcmodelfile} {outputdir} && cd {outputdir} && ./lcmodel < control_sl0.CONTROL && rm lcmodel"""
        print(command)
        os.system(command)



        ##### PLOTTING #####
        import matplotlib.pyplot as plt
        import numpy as np

        cols = 8
        fig, axs = plt.subplots(int(np.ceil(len(dicoms)/cols)), cols, figsize=(8, 8))
        fig.suptitle('Dicoms')

        for i, d in enumerate(dicoms):
            axs[i//cols, i%cols].plot(d.time_axis(), np.absolute(d))
            axs[i//cols, i%cols].set_title(f"Dicom {i+1}")
            axs[i//cols, i%cols].set_xlabel('Time (s)')
            axs[i//cols, i%cols].set_ylabel('Signal Intensity')

        # plt.figure()
        # plt.title("result")
        # plt.plot(result.time_axis(), np.absolute(result))
        # plt.xlabel('Time (s)')
        # plt.ylabel('Signal Intensity')
        # plt.show() # ideally the plots appear in the GUI
        # self.matplotlib_canvas.axes.plot(result.time_axis(),np.absolute(result))
        # self.matplotlib_canvas.draw()
        
        event.Skip()



class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True