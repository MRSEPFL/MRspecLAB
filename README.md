# (name here)
(name here) is a graphical application for the processing and analysis of magnetic resonance spectroscopy scans. It can be thought of as a wrapper around the [suspect library by OpenMRSLab](https://github.com/openmrslab/suspect) and the [LCModel executable by Stephen Provencher](http://s-provencher.com/lcmodel.shtml), focusing on user-friendliness, automated use and modularity. Currently supported and tested formats are DICOM and Twix files.

## Installation and usage
In order to use this application, download and extract this repository. Required packages can be installed by running the following command in the repository folder:

```pip install -r requirements.txt```

The GUI is started by running `MRSprocessing.py` with Python and is hoped to be self-explanatory. Compatibility was tested with Python versions `3.9` and above.

The application detects any processing steps placed in the `processing` folder. The creation of custom processing steps is detailed in the read-me file in that folder. A similar function might be planned for reading custom data types.

### Linux
On a Linux system, the pip command given above will probably try to build the wxPython package for your specific Linux distribution, which can take a very long time. A much quicker alternative is to abort the running command (Ctrl+C in the terminal window) and download the latest pre-built package (`.whl` file) from the [wxPython database](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/) according to your OS (folder) and Python (cpXXX) versions. You can then install it using the following command ([source](https://wxpython.org/pages/downloads/index.html)):

```pip install -f <path_to_whl_file> wxPython```

(Re-)running `pip install -r requirements.txt` should verify that installation and ensure no other packages are missing.

## License and used libraries
(name here) is released under the (license here) license.

The code for some file-reading and processing steps was taken from the `suspect` library and modified to better suit our purposes. The [gsnodegraph library by GimelStudio](https://github.com/GimelStudio/gsnodegraph), initially designed for use in image editing, was also modified for our processing pipeline editor and shipped with our application. Finally, Windows and Linux binaries for LCModel were compiled from the source code on [Georg Oeltzschner's repository](https://github.com/schorschinho/LCModel), and compressed and shipped alongside our application for a straight-forward installation. The licenses for all these products are included in this repository.
