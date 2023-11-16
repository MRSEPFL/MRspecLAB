# (name here)
(name here) is a graphical application for the processing and analysis of magnetic resonance spectroscopy scans. It can be thought of as a wrapper around the [suspect library by OpenMRSLab](https://github.com/openmrslab/suspect) and the [LCModel executable by Stephen Provencher](http://s-provencher.com/lcmodel.shtml), focusing on user-friendliness, automated use and modularity. Currently supported and tested formats are DICOM and Twix files.

The code for some reading and processing steps was taken from the suspect library and modified to better suit our purposes. Windows and Linux binaries for LCModel were compiled from the source code on [Georg Oeltzschner's repository](https://github.com/schorschinho/LCModel), compressed and shipped alongside our application for straight-forward usage. The licenses for both products are included in this repository.

## Usage
In order to use this application, download and extract this repository. Required packages can be installed by running `pip install -r requirements.txt` in the repository folder. The GUI is started by running `main.py` and is hoped to be self-explanatory. Compatibility was tested with Python versions `3.9` and above.

## Customisation
The application detects and uses any processing steps placed in the processing folder. A similar function might be planned for reading custom data types.

Custom processing steps should derive from the `ProcessingStep` class and implement a `process` method to modify incoming data in suspect's `MRSData` format, with an optional `plot` method to write to a matplotlib figure.

The `process` method accepts a dictionary carrying its in- and output data under the following keys:
- `input` (list of `MRSData` objects): data coming from the last processing step in the pipeline, or the file reader if this is the first processing step;
- `original` (list of `MRSData` objects): data read from the imported MRS files; used for instance for frequency alignment, where `input` might have been modified by zero-padding and/or line broadening, and final changes are done on the unmodified data in `original` (until we implement branching pipelines);
- `output` (list of `MRSData` objects): output data of the processing step, and input data for the next one; it is `None` when passed to the processing step and should be written to with a new list of data;
- `wref`, `wref_original`, `wref_output` (`MRSData` objects): analogous data for the water reference, and is `None` if no water reference file was selected; used for instance for Eddy current correction.

The `plot` method can be implemented for a custom presentation of the same data dictionary immediately after `process` was called. It accepts the matplotlib figure which is then shown and exported to a file, and the data dictionary presented above. If not overridden, the `plot` method of the base class is used; this method can still be customised by setting bools in the constructor of the derived class:
- if `self.plotTime` is set to `True`, the in- and output data will be plotted over time;
- if `self.plotSpectrum` is set to `True`, the in- and output data will (also) be plotted over frequency or chemical shift; the unit over which they are plotted can be chosen between PPM and Hertz by setting `self.plotPPM` to `True` or `False` respectively.

Common processing steps are included in this repository and can serve as references.

## License
(name here) is released under the (license here) license.