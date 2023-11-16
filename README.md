# (name here)
(name here) is a graphical application for the processing and analysis of magnetic resonance spectroscopy scans. It can be thought of as a wrapper around the [suspect library by OpenMRSLab](https://github.com/openmrslab/suspect) and the [LCModel executable by Stephen Provencher](http://s-provencher.com/lcmodel.shtml), focusing on user-friendliness, automated use and modularity. Currently supported and tested formats are DICOM and Twix files.

The code for some reading and processing steps was taken from the suspect library and modified to better suit our purposes. Windows and Linux binaries for LCModel were compiled from the source code on [Georg Oeltzschner's repository](https://github.com/schorschinho/LCModel), compressed and shipped alongside our application for straight-forward usage. The licenses for both products are included in this repository.

## Usage
In order to use this application, download and extract this repository. Required packages can be installed by running `pip install -r requirements.txt` in the repository folder. The GUI is started by running `main.py` and is hoped to be self-explanatory. Compatibility was tested with Python versions `3.9` and above.

The application detects any processing steps placed in the `processing` folder. The creation of custom processing steps is detailed in the read-me file in that folder. A similar function might be planned for reading custom data types.

## License
(name here) is released under the (license here) license.