# User manual
## General usage
General usage of the program is as follows:
- Add the MRS files to be processed in the list-boxes on the left, with the metabolite files in the top box and the water reference files in the bottom one. Adding can be done via the buttons above each box, or by drag-and-dropping them from a file explorer window; Please only load data of one participant at a time (if you want to process several datasets, please refer to 'batch-mode processing'
- (Optional) View the MRS files in a separate window by double-clicking them; you can view the individual coil data, or coil-combined (tick box right corner).
- (Optional) Edit the pipeline in the pipeline editor window by opening it with the button on the left of the upper button bar (colorful chain). Nodes can be added by dragging from the nodes list (click the '+') at the top left, connected by dragigng from the node sockets, and parameters can be edited in the right panel after clicking on them;
- (Optional) Apply fitting settings for LCModel via the button 'show fitting options' bar at the top: You can input a .basis set, a .control file, and anatomical segmentation files. 
- Run the processing pipeline step-by-step by pressing play on the top right, or let the steps run continuously with the fast-forward button next to it. 

The program will try to assist you as follows to simplify setting up the processing:
- The program automatically recognises the type of the input files and can read each filetype without extra information from the user;
- If not given manually, the .basis file used by the LCModel fitting tool defaults to automatic detection using the MRS data properties, as long as a corresponding .basis file is present in the `/lcmodel/basis` folder of the source code;
- If not given manually, the .control file used by LCModel will default to a pre-made one, and corrected automatically in certain fields depending on the MRS data properties;
- The processing pipeline will default to generic one containing adaptive coil-combination (if the data is not already coil-combined), frequency and phase alignment, Eddy current correction, removal of outlier data and averaging;
- Coil-combination accounts for multi-shot data by averaging each group of shots together into one time-series;
- If the input data is not coil-combined and no coil-combination is present in the pipeline, adaptive coil-combination is automatically carried out as the first step;
- The program automatically handles creation of the LCmodel input files, execution of LCModel as well as and proper plotting of its output files. This works for both Windows and Linux operating systems;
- The program creates a clear file structure with all its output files.

The functionality of the different elements of the interface is detailed below.

## GUI description
### Main window
The main window appears directly after the program is started. It contains the [input panels](#file-input) on the left, a [button bar](#button-bar) at the top right, a [plotting panel](#file-viewing-and-plotting-panel) in the right centre, a logging box at the bottom centre and an info box at the bottom right. The logging box shows informative and warning messages during execution, while the info box shows additional information when viewing the final fitting plots.

#### File input
The files to be viewed/processed are added on the left pane of the main window. The top box is for metabolite files and the bottom one for water reference files, each one with the same set of buttons:
- the "+" button opens a file dialog trough which one or multiple MRS files can be selected;
- the "-" button removes the file selected in the list box below;
- the "Clear" button removes all files from the list box below.

Files can also be dragged and dropped from an explorer window into each list box. The program currently only expects a single water reference file, and will only use the first one if multiple are provided.

Supported MRS formats are:
- .dcm (DICOM)
- .ima (Siemens DICOM)
- .dat (Siemens Twix)
- .rda (Siemens pre-processed)
- .sdat (Philips)
- .nii/.nii.gz (NIfTI MRS)

LCModel .coord files can be viewed, but are ignored for processing.

#### File viewing and plotting panel
Double-clicking a file in a list box will plot it in a separate window.
For MRS files, this shows the raw data over time and ppm and displays some file properties on the right. If the file is not coil-combined, all coils are plotted separately. For .coord files, this shows the various and metabolite spectra and the detailed concentrations on the right.

The plotting panel in the main window is used exclusively by the pipeline workflow, and shows relevant information after every processing step, optional manual adjustment interfaces as well as the final results from the fitting tool.

Both the plotting panel and the file vieweing window hold a toolbar that allows panning the graph, zooming in to a selection box, manually saving the shown figure, as well as resetting the view and undoing and redoing the last graph manipulations.

#### Button bar
The button bar contains most settings and controls related to MRS processing.
From left to right:
- The folder button opens the folder where the output files are produced. The pipeline button below it opens the [pipeline editor](#pipeline-editor);
- The next column handles the output and plotting parameters. The checkboxes toggle whether the plots of the processing steps are saved as .png, and whether the transient MRS data is saved as .raw files for each step. The drop-down menu selects which processing step is currently shown in the plotting panel;
- The third column handles fitting and debug parameters. The fitting window sets the .control file, .basis file and eventual corrected and segmented brain scans for use by the LCModel fitting tool. The Debug options allow showing the debug messages in the logging box, and rescanning the node folder when running the source code.

The last three buttons control the processing flow:
- The first "play" button starts the next processing step in the pipeline, or the first one of processing isn't running yet;
- The second "fast-forward" button toggles if the steps are continuously run without showing them in the plotting panel.  If toggled, the button changes to a "pause" button to turn this behaviour off again;
- The third "stop" button aborts processing, so that it can be restarted after eventual changes in the file input or pipeline editor.

### Pipeline editor
The pipeline editor opens a new window with a nodegraph. The nodes represent processing steps, and the pipeline is read starting from the input node and following all interconnected nodes in order. Fitting with LCModel is alway carried out after the pipeline is completed. The nodegrpah controls are as follows:
- Nodes are added by opening the node list with the "+" button at the top left, and dragging an entry from the list into the nodegraph;
- Nodes can be moved by left-dragging them, connected by left-dragging their sockets, and edited in the right panel by left-clicking them;
- The entire view can be moved by dragging while holding the mouse wheel, or by left-dragging while holding the shift-key;
- Nodes can be deleted or duplicated by right-clicking them;
- Multiple nodes can be selected for moving or deleting by left-dragging over an area of the nodegraph.

Additionally, the pipeline can be exported to and imported from .pipe files using the "save" and "load" buttons above. The "clear" button removes all nodes from the nodegraph, except for the input node. Node creation is detailed in the [node API description](nodes/README.md).
