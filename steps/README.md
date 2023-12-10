## Processing steps

Custom processing steps should derive from the `ProcessingStep` class and implement a `process` method to modify incoming data in suspect's `MRSData` format, with an optional `plot` method to write to a matplotlib figure. Some common processing steps are included in this repository and can serve as references.


### process
The `process` method accepts a dictionary carrying its in- and output data under the following keys:
- `input` (list of `MRSData` objects): data coming from the last processing step in the pipeline, or the file reader if this is the first processing step;
- `original` (list of `MRSData` objects): data read from the imported MRS files; used for instance for frequency alignment, where `input` might have been modified by zero-padding and/or line broadening, and final changes are done on the unmodified data in `original` (until we implement branching pipelines);
- `output` (list of `MRSData` objects): output data of the processing step, and input data for the next one; it is `None` when passed to the processing step and should be written to with a new list of data;
- `wref`, `wref_original`, `wref_output` (`MRSData` objects): analogous data for the water reference, and is `None` if no water reference file was selected; used for instance for Eddy current correction.

### plot
The `plot` method can be implemented for a custom presentation of the same data dictionary immediately after `process` was called. It accepts the matplotlib figure which is then shown and exported to a file, and the data dictionary presented above. If not overridden, the `plot` method of the base class is used; this default method can still be customised by setting bools in the constructor of the derived class:
- if `self.plotTime` is set to `True`, the in- and output data will be plotted over time;
- if `self.plotSpectrum` is set to `True`, the in- and output data will (also) be plotted over frequency or chemical shift; the unit over which they are plotted can be chosen between PPM and Hertz by setting `self.plotPPM` to `True` or `False` respectively.

### Parameters
To implement user-modifiable parameters in the processing step, simply pass a dictionary with their names and default values to `super().__init__()` in the step's constructor. This dictionary will be accessible as `self.parameters` in the methods, and editable in the pipeline editor at runtime.