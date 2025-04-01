import processing.api as api
import numpy as np
import interface.utils as utils
from scipy.ndimage import convolve
import copy


class Hanning_3D(api.ProcessingNode):
    def __init__(self, nodegraph, id):


        self.meta_info = {
            "label": "3D Hanning Filter",
            "author": "CIBM",
            "description": "Applies a 3D Hanning filter"
        }


        self.parameters = [
            api.IntegerProp(
                idname="Window size X",
                default=16,
                min_val=1,
                max_val=48,
                fpb_label="Window size X"
            ),
            api.IntegerProp(
                idname="Window size Y",
                default=16,
                min_val=1,
                max_val=48,
                fpb_label="Window size Y"
            ),
            api.IntegerProp(
                idname="Window size Z",
                default=8,
                min_val=1,
                max_val=48,
                fpb_label="Window size Z"
            )
        ]
        super().__init__(nodegraph, id)


    def initialize_parameters(self, data):
        """ Dynamically sets the max window size based on the input data dimensions """
        header = data["header"]
        size_x = header["CSIMatrix_Size[0]"]
        size_y = header["CSIMatrix_Size[1]"]
        size_z = header["CSIMatrix_Size[2]"]


        # # Set max_val dynamically to avoid exceeding data dimensions
        # max_x = min(10, size_x)
        # max_y = min(10, size_y)
        # max_z = min(10, size_z)


        self.parameters = [
            api.IntegerProp("Window size X", default=4, min_val=1, max_val=size_x, fpb_label="Window size X"),
            api.IntegerProp("Window size Y", default=4, min_val=1, max_val=size_y, fpb_label="Window size Y"),
            api.IntegerProp("Window size Z", default=4, min_val=1, max_val=size_z, fpb_label="Window size Z")
        ]


    def process(self, data):
        # Get adjustable window sizes
        window_size_x = self.get_parameter("Window size X")
        window_size_y = self.get_parameter("Window size Y")
        window_size_z = self.get_parameter("Window size Z")


        header = data["header"]
        CSIMatrix_Size = [header["CSIMatrix_Size[0]"],
                          header["CSIMatrix_Size[1]"],
                          header["CSIMatrix_Size[2]"]]


        utils.log_info(f"CSIMatrix_Size: {CSIMatrix_Size}")


        # Ensure input is at least 5D (Batch, X, Y, Z, Time)
        input_data = np.array(data["input"])  # Convert input to NumPy array


        utils.log_info(f"Shape of the input data: {input_data.shape}")


        # Create a 3D Hanning filter (X, Y, Z) with separate window sizes
        def hanning_filter_3d(size_x, size_y, size_z):
            hx = np.hanning(size_x)
            hy = np.hanning(size_y)
            hz = np.hanning(size_z)


            hxy = np.outer(hx, hy)  # 2D Hanning
            hxyz = np.outer(hxy.ravel(), hz).reshape(size_x, size_y, size_z)


            return hxyz / np.sum(hxyz)  # Normalize the filter


        hanning_kernel = hanning_filter_3d(window_size_x, window_size_y, window_size_z)  # Shape: (X, Y, Z)


        # Reshape kernel to match the data shape (1, X, Y, Z, 1) for convolution
        hanning_kernel = hanning_kernel.reshape(window_size_x, window_size_y, window_size_z, 1)


        # Apply the 3D Hanning filter while preserving the 1st and 5th dimensions
        smoothed_data = np.empty_like(input_data)
        for t in range(input_data.shape[-1]):  # Loop over the Time (5th) dimension
            smoothed_data[..., t] = convolve(input_data[..., t], hanning_kernel, mode='nearest')


        utils.log_info(f"Shape of the smoothed data: {smoothed_data.shape}")


        # Create the output list and inherit the processed data
        output = copy.deepcopy(data["input"])


        for i in range(CSIMatrix_Size[0]):
            for j in range(CSIMatrix_Size[1]):
                for k in range(CSIMatrix_Size[2]):
                    temp = smoothed_data[0, i, j, k, :]
                    temp = np.squeeze(temp)
                    output[0][i][j][k] = temp  # Store the processed data


        data["output"] = output


        # Log the output shape
        output_np = np.array(data["output"])
        utils.log_info(f"Shape of the output data: {output_np.shape}")


    def plot(self, figure, data):
        figure.suptitle(self.__class__.__name__)


        header = data["header"]
        CSIMatrix_Size = [header["CSIMatrix_Size[0]"],
                          header["CSIMatrix_Size[1]"],
                          header["CSIMatrix_Size[2]"]]


        ax = figure.add_subplot(1, 2, 1)


        d = data["input"][0]


        d_np = np.array(d)
        utils.log_info(f"Shape of the input data: {d_np.shape}")


        ax.plot(d.frequency_axis_ppm(), np.real(d[int(CSIMatrix_Size[0]/2)][int(CSIMatrix_Size[1]/2)][int(CSIMatrix_Size[2]/2)].spectrum()))
        ax.set_xlabel('ppm')
        ax.set_ylabel('Intensity')
        ax.set_title("Input central voxel spectrum")
        figure.tight_layout()


        ax = figure.add_subplot(1, 2, 2)


        d = data["output"][0]


        d_np = np.array(d)
        utils.log_info(f"Shape of the output data: {d_np.shape}")


        ax.plot(d.frequency_axis_ppm(), np.real(d[int(CSIMatrix_Size[0]/2)][int(CSIMatrix_Size[1]/2)][int(CSIMatrix_Size[2]/2)].spectrum()))
        ax.set_xlabel('ppm')
        ax.set_ylabel('Intensity')
        ax.set_title("Output central voxel spectrum")
        figure.tight_layout()


api.RegisterNode(Hanning_3D, "Hanning_3D")
