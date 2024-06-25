# (name here)
(name here) is a graphical application for the processing and analysis of magnetic resonance spectroscopy scans, focusing on user-friendliness, automated use and modularity. Currently supported and tested formats are DICOM and Twix files.

## Installation and usage
To run this application from source, download and extract this repository. Required packages can be installed by running the following command in the repository folder:

```pip install -r requirements.txt```

The GUI is started by running `MRSprocessing.py` with Python and is hoped to be self-explanatory. The program currently runs on Python versions 3.9, 3.10 and 3.11.

The application detects any processing steps placed in the `processing` folder. The creation of custom processing steps is detailed in the read-me file in that folder. A similar function might be planned for reading custom data types.

### Windows
A Windows executable is included in the `dist/MRSprocessing` directory, and can be run directly after downloading the repository. Currently this executable only contains the default processing modules and does not retrieve any new ones from the `steps` folder. It can be rebuilt using the `pyinstaller.py` script, in which case it will include all steps present in that folder.

### Linux
On a Linux system, the pip command given above will probably try to build the wxPython package for your specific Linux distribution, which can take a very long time. A much quicker alternative is to abort the running command (Ctrl+C in the terminal window) and download the latest pre-built package (`.whl` file) from the [wxPython database](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/) according to your OS (folder) and Python (cpXXX) versions. You can then install it using the following command ([source](https://wxpython.org/pages/downloads/index.html)):

```pip install -f <path_to_whl_file> wxPython```

(Re-)running `pip install -r requirements.txt` should verify that installation and ensure no other packages are missing.

## License and used libraries
(name here) is released under the (license here) license.

Code was taken and modified from the 'suspect' library for file-reading and processing functions and the `gsnodegraph` library for the editor panel. Windows and Linux binaries for LCModel were compiled from the source code on [Georg Oeltzschner's repository](https://github.com/schorschinho/LCModel), and compressed and shipped alongside our application for a straight-forward installation.
