# import os
# import glob
# import inspect
# import importlib.util


import wx
from GUI import MyApp


if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()


# # get all processing steps from ./processing (all classes from all files)
# # maybe check if the class is a subclass of ProcessingStep
# processing_files = glob.glob(os.path.join(os.path.dirname(__file__), "processing", "*.py"))
# processing_steps = {}
# for file in processing_files:
#     module_name = os.path.basename(file)[:-3]
#     if module_name != "__init__":
#         spec = importlib.util.spec_from_file_location(module_name, file)
#         module = importlib.util.module_from_spec(spec)
#         spec.loader.exec_module(module)
#         for name, obj in inspect.getmembers(module):
#             if inspect.isclass(obj) and obj.__module__ == module_name:
#                 obj = getattr(module, name)
#                 processing_steps[name] = obj

# print(processing_steps)



# ##### READING #####
# import suspect

# # list of dicom file-paths to get from wxpython
# # maybe add option to get only the folder-path from wxpython
# dicom_files = glob.glob("C:\OneDrive\epfl\cibmproject\STEAM_1H\*.IMA")
# print(len(dicom_files))

# dicoms = []
# wref = None
# for file in dicom_files:
#     if file.find("0037.0001") != -1: # unsuppressed water reference
#         wref = suspect.io.load_siemens_dicom(file)
#         continue
#     try: dicoms.append(suspect.io.load_siemens_dicom(file))
#     except: print("Error loading dicom file: " + file)



# ##### PROCESSING #####
# pipeline = ["yeet", "Average"]
# result = dicoms
# for step in pipeline:
#     if step not in processing_steps.keys():
#         print(f"Processing step {step} not found")
#         continue
#     result = processing_steps[step]().process(result)



# ##### ANALYSIS #####
# import os
# import zipfile
# import shutil

# outputdir = os.path.join(os.path.dirname(__file__), "output")
# controlfile = os.path.join(outputdir, "control")
# params = {
#     "FILBAS": "../lcmodel/7T_SIM_STEAM_TE4p5_TM25_mod.BASIS",
#     "FILCSV": "./result.csv",
#     "FILCOO": "./result.coord",
#     "FILPS": "./result.ps",
#     "LCSV": 11,
#     "LCOORD": 9,
#     "LPS": 8
# }

# shutil.rmtree(outputdir) # delete output folder
# suspect.io.lcmodel.write_all_files(controlfile, result, wref_data=wref, params=params) # write raw, h2o, control files to output folder

# lcmodelfile = "lcmodel" # linux exe
# if os.name == 'nt': lcmodelfile += ".exe" # windows exe

# if not os.path.exists("lcmodel/" + lcmodelfile): # lcmodel executables are zipped in the repo because of size
#     if not os.path.exists("lcmodel/lcmodel.zip"):
#         print("lcmodel executable or zip not found")
#         pass
#     print("lcmodel executable not found, extracting from zip")
#     with zipfile.ZipFile("lcmodel/lcmodel.zip", "r") as zip_ref:
#         zip_ref.extractall("lcmodel")

# if os.name == 'nt': command = r"""copy lcmodel\\lcmodel.exe output & cd output & lcmodel.exe < control_sl0.CONTROL & del lcmodel.exe"""
# else: command = r"cp lcmodel/lcmodel output && cd output && ./lcmodel < control_sl0.CONTROL && rm lcmodel"
# os.system(command)



# ##### PLOTTING #####
# import matplotlib.pyplot as plt
# import numpy as np

# cols = 8
# fig, axs = plt.subplots(int(np.ceil(len(dicoms)/cols)), cols, figsize=(8, 8))
# fig.suptitle('Dicoms')

# for i, d in enumerate(dicoms):
#     axs[i//cols, i%cols].plot(d.time_axis(), np.absolute(d))
#     axs[i//cols, i%cols].set_title(f"Dicom {i+1}")
#     axs[i//cols, i%cols].set_xlabel('Time (s)')
#     axs[i//cols, i%cols].set_ylabel('Signal Intensity')

# plt.figure()
# plt.title("result")
# plt.plot(result.time_axis(), np.absolute(result))
# plt.xlabel('Time (s)')
# plt.ylabel('Signal Intensity')
# plt.show() # ideally the plots appear in the GUI