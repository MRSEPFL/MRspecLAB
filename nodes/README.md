# Processing steps
Processing nodes derive from the `ProcessingNode` class and implement a `process` method to modify incoming data in suspect's `MRSData` format, with an optional `plot` method to write to a matplotlib figure. Some common processing steps are included in this repository and can serve as references.

## MRSData
The data read from the MRS files are stored in instances of suspect's MRSData class, each representing a single FID. It behaves like a NumPy array and has methods for conversion to spectral data, retrieval of ppm axes, adjusting frequency and phase etc. It also holds attributes such as the scanning frequency (`MRSData.f0`), dwell time (`.dt`) and echo and repetition times (`.te`, `.tr`). Examples of use can be seen in the existing node implementations.

An MRSData is a 1-dimensional array over time, or a 2-dimensional array of size (#coils x #timepoints) if not coil-combined. In the toolbox, multiple FIDs are stored in a 1-dimensional list in the same order as the files given, squashing the "averages" and "repetitions" axes commonly used in some input formats. If the input data has multiple averages and multiple repetitions, the FIDs will be sorted in average-first order in the lists (e.g. Rep1Ave1, Rep1Ave2, Rep2Ave1, ...). In this case, the number of averages per repetition can be retrieved via `MRSData.metadata["ave_per_rep"]`.

## Initialisation
All necessary definitions for the creation of a custom node are imported via the `processing.api` interface. It includes the base class `ProcessingNode` as well as property classes that can be added to the node for UI interactions.

Any node derives from the `ProcessingNode` class. For it to function as a gsnodegraph node, the constructor must accept the `nodegraph` and `id` arguments, which are simply passed on to the base class constructor via `super().__init__(nodegraph, id)`. Before this call, the node's information fields and parameters can be configured. Outside the class definition, the node file must include the line `api.RegisterNode(NodeClass, "id")` for the node to appear in the interface, where `NodeClass` is the node class object and `id` is an identifier only used internally by the toolbox, but usually set to the name of the node for clarity.

#### Info
The dictionary `self.meta_info` can be declared with the following optional fields:
- "label" is the name of the node shown in the UI, and is set to the name of the class if not given;
- "author", "version" and "description" are shown in the help window of the node and are empty by default;
- "category" is one of the preset category strings for the node, and is "PROCESSING" by default.

The "category" field determines the colour of the node in the pipeline editor, and can only be set to certain hard-coded strings. It has to be set to "COIL_COMBINATION" for a coil-combination node, as the toolbox currently automatically runs adaptive coil combination if it detects multi-coil input data but no "COIL_COMBINATION" category for the first node in the pipeline.

#### Parameters
The list of parameters `self.parameters` can be declared, containing instances of gsnodegraph properties. These can then be manipulated from the UI and used in the `process` and `plot` methods. The available properties in the API currently are `IntegerProp`, `FloatProp`, `ChoiceProp`, `VectorProp` and `StringProp`. Their implementations can differ and are best looked up in the existing node implementations, but there are common arguments:
- "idname" is the string used to read the property's value from within the class via `self.get_parameter("idname")`;
- "fpb_label" is the text shown in the configuration panel of the node, serving as a description of the property;
- "default" is the value of the property when the node is created.

When the property represents one or multiple numerical values, the arguments `min_val`(`s`) and `max_val`(`s`) have to be given to determine the range of the property slider in the UI.

## `process`
The `process` method accepts a dictionary carrying the in- and output data of the node. All values are lists of MRSData and are found under the following keys:
- "input" is the list of metabolite FIDs produced by the previous node;
- "output" is the list of metabolite FIDs after being processed by the current node (initially empty);
- "wref" and "wref_output" are the same for the water FIDs.

The method should store the processed data in the output fields, and no return value is expected. The output fields become the inputs of the next node. The "wref_output" field can be left empty, in which case the "wref" field of the next node will be filled with the last state of the water reference data.

The output data must be of the MRSData type to allow proper plotting and further processing. Since most NumPy functions used on MRSData objects will return NumPy arrays, it is necessary to turn those arrays back into MRSData objects using MRSData's `inherit` method. This retrieves the attributes of an old MRSData instance and copies them over to the new one. Since those parameters are usually the same for all FIDs in a given processing pipeline, the old data used can be any of the ones available.
```python
new_array = np.mean(list_of_mrsdata) # example of a numpy function that returns an array
new_mrsdata = list_of_mrsdata[0].inherit(new_array) # copy the data from any (the first) old instance to create a new one
```

A field "labels" can be added to the data dictionary, containing the name under which the output files of each FID will be saved after fitting. It should be a list of strings and have the same length as the "output" field. This field is not used or backed up while in the processing loop, so the labels might be overwritten by later nodes.

## `plot`
The `plot` method can be implemented for a custom presentation of the same data dictionary immediately after `process` was called. It accepts the matplotlib figure which is then shown and exported to a file, and the data dictionary.

If not overridden, the `plot` method of the base class is used. This default method can still be customised by setting bools in the constructor of the derived class. It can only handle coil-combined data.
- if `self.plotTime` is set to `True`, the in- and output data will be plotted over time;
- if `self.plotSpectrum` is set to `True`, the in- and output data will (also) be plotted over frequency or chemical shift;
- if `self.plotPPM` is set to `True`, the spectra will be plotted over the usual flipped PPM axis, otherwise over a non-flipped Hz axis.

For a custom implementation, useful functions are `MRSData.time_axis()`, `MRSData.frequency_axis()` and `MRSData.frequency_axis_ppm()` that produce point coordinates along the x-axis for the MRSData object, and the `MRSData.spectrum()` method that performs the Fourier transform on the MRSData; time data can be retrieved by directly indexing or using the MRSData object itself. The time and frequency data being complex, they should be cast to 1-dimensional values before plotting.
```python
ax.plot(mrsdata.time_axis(), np.real(mrsdata)) # plots FID over time
ax.plot(mrsdata.frequency_axis_ppm(), np.real(mrsdata.spectrum())) # plots spectrum over flipped PPM
ax.plot(mrsdata.frequency_axis(), np.real(mrsdata.spectrum())) # plots spectrum over Hz
```