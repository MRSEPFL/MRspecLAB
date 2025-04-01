import processing.api as api
import numpy as np
import interface.utils as utils
import tkinter as tk
from tkinter import simpledialog
import copy


# import matplotlib.pyplot as plt
# from matplotlib.widgets import TextBox, Button
# import wx
# from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas


class LineBroadening_CSI(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Line Broadening CSI (Gaussian)",
            "author": "CIBM",
            "description": "Spectral linebroadening with Gaussian functions",
        }
        self.parameters = [
            api.IntegerProp(
                idname="Gaussian_lw_hz",
                default=5,
                min_val=1,
                max_val=50,
                fpb_label="Linewidth (Hz)"
            )
        ]
        super().__init__(nodegraph, id)
        self.plotSpectrum = False


    def process(self, data):
        self.exp = np.exp(-( (data["input"][0].time_axis() * np.pi * self.get_parameter("Gaussian_lw_hz")) / (2 * np.sqrt(np.log(2)))) ** 2)


        header = data["header"]
        CSIMatrix_Size = [header["CSIMatrix_Size[0]"],
                          header["CSIMatrix_Size[1]"],
                          header["CSIMatrix_Size[2]"]]


        # Create the output list and inherit the processed data
        output = copy.deepcopy(data["input"])


        for i in range(CSIMatrix_Size[0]):
            for j in range(CSIMatrix_Size[1]):
                for k in range(CSIMatrix_Size[2]):
                    d = np.squeeze(data["input"][0][i][j][k])
                    output[0][i][j][k] = d * self.exp


        data["output"] = output


        # output = []
        # self.dmax = 0
        # for d in data["input"]:
        #     output.append(d.inherit(d * self.exp))
        #     self.dmax = max(self.dmax, np.max(d)) # for plotting exp
        # data["output"] = output


        output_np = np.array(output)
        utils.log_info(f"Shape of the output data: {output_np.shape}")
        input0_np = np.array(data["input"][0].time_axis() )
        utils.log_info(f"Shape of the input0 data: {input0_np.shape}")


    def plot(self, figure, data):
        figure.suptitle(self.__class__.__name__)


        header = data["header"]
        CSIMatrix_Size = [header["CSIMatrix_Size[0]"],
                          header["CSIMatrix_Size[1]"],
                          header["CSIMatrix_Size[2]"]]


        # index = int(CSIMatrix_Size[0] * CSIMatrix_Size[1] * CSIMatrix_Size[2] / 2)
        # utils.log_info(f"3D moving average: plot number {index} voxel")


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


api.RegisterNode(LineBroadening_CSI, "LineBroadening_CSI")



"""import processing.api as api
import numpy as np
import interface.utils as utils
import tkinter as tk
from tkinter import simpledialog

# import matplotlib.pyplot as plt
# from matplotlib.widgets import TextBox, Button
# import wx
# from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

class LineBroadening_CSI(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "Line Broadening CSI (Gaussian)",
            "author": "CIBM",
            "description": "Spectral linebroadening with Gaussian functions",
        }
        self.parameters = [
            api.IntegerProp(
                idname="Gaussian_lw_hz",
                default=5,
                min_val=1,
                max_val=50,
                fpb_label="Linewidth (Hz)"
            )
        ]
        super().__init__(nodegraph, id)
        self.plotSpectrum = False

    def process(self, data):
        self.exp = np.exp(-( (data["input"][0].time_axis() * np.pi * self.get_parameter("Gaussian_lw_hz")) / (2 * np.sqrt(np.log(2)))) ** 2)
        output = []
        self.dmax = 0
        for d in data["input"]:
            output.append(d.inherit(d * self.exp))
            self.dmax = max(self.dmax, np.max(d)) # for plotting exp
        data["output"] = output

        output_np = np.array(output)
        utils.log_info(f"Shape of the output data: {output_np.shape}")
        input0_np = np.array(data["input"][0].time_axis() )
        utils.log_info(f"Shape of the input0 data: {input0_np.shape}")


    def plot(self, figure, data):

        figure.suptitle(self.__class__.__name__)

        # Create a Tkinter window for input
        root = tk.Tk()
        root.withdraw()  # Hide main Tkinter window

        # Ask the user for the index value
        index = simpledialog.askinteger("Select Index", "Enter index to plot:", minvalue=0, maxvalue=len(data["input"][0]) - 1)

        ax = figure.add_subplot(2, 2, 1)
        #for d in data["input"]:
        d = data["input"][0]
        ax.plot(d.time_axis(), np.real(d[index]))
        ax.plot(d.time_axis(), self.exp * self.dmax, ':k')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Intensity')
        ax.set_title("Input FID and apodisation function")

        ax = figure.add_subplot(2, 2, 2)
        #for d in data["output"]:
        d = data["output"][0]
        ax.plot(d.time_axis(), np.real(d[index]))
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Intensity')
        ax.set_title("Output FID")
        figure.tight_layout()

        ax = figure.add_subplot(2, 2, 3)
        #for d in data["output"]:
        d = data["input"][0]
        ax.plot(d.frequency_axis_ppm(), np.real(d[index].spectrum()))
        ax.set_xlabel('ppm')
        ax.set_ylabel('Intensity')
        ax.set_title("Input Spectrum")
        figure.tight_layout()

        ax = figure.add_subplot(2, 2, 4)
        #for d in data["output"]:
        d = data["output"][0]
        ax.plot(d.frequency_axis_ppm(), np.real(d[index].spectrum()))
        ax.set_xlabel('ppm')
        ax.set_ylabel('Intensity')
        ax.set_title("Output Spectrum")
        figure.tight_layout()"""

    # def plot(self, figure, data):

    #     figure.suptitle(self.__class__.__name__)

    #     # Default index
    #     index = 0

    #     # Create subplots
    #     ax1 = figure.add_subplot(2, 2, 1)
    #     ax2 = figure.add_subplot(2, 2, 2)
    #     ax3 = figure.add_subplot(2, 2, 3)
    #     ax4 = figure.add_subplot(2, 2, 4)

    #     def update_plot(text):
    #         """ Update the plot based on the entered index """
    #         nonlocal index
    #         try:
    #             index = int(text)
    #             index = min(max(0, index), len(data["input"][0]) - 1)  # Keep index within valid range
    #         except ValueError:
    #             return  # Ignore invalid inputs

    #         # Clear and update Input FID
    #         ax1.clear()
    #         ax1.plot(data["input"][0].time_axis(), np.real(data["input"][0][index]))
    #         ax1.plot(data["input"][0].time_axis(), self.exp * self.dmax, ':k')
    #         ax1.set_xlabel('Time (s)')
    #         ax1.set_ylabel('Intensity')
    #         ax1.set_title("Input FID and Apodization Function")

    #         # Clear and update Output FID
    #         ax2.clear()
    #         ax2.plot(data["output"][0].time_axis(), np.real(data["output"][0][index]))
    #         ax2.set_xlabel('Time (s)')
    #         ax2.set_ylabel('Intensity')
    #         ax2.set_title("Output FID")

    #         # Clear and update Input Spectrum
    #         ax3.clear()
    #         ax3.plot(data["input"][0].frequency_axis_ppm(), np.real(data["input"][0][index].spectrum()))
    #         ax3.set_xlabel('ppm')
    #         ax3.set_ylabel('Intensity')
    #         ax3.set_title("Input Spectrum")

    #         # Clear and update Output Spectrum
    #         ax4.clear()
    #         ax4.plot(data["output"][0].frequency_axis_ppm(), np.real(data["output"][0][index].spectrum()))
    #         ax4.set_xlabel('ppm')
    #         ax4.set_ylabel('Intensity')
    #         ax4.set_title("Output Spectrum")

    #         # Redraw figure
    #         figure.canvas.draw_idle()

    #     def clear_plot(event):
    #         """ Clears all plots and resets the index """
    #         ax1.clear()
    #         ax2.clear()
    #         ax3.clear()
    #         ax4.clear()
    #         figure.canvas.draw_idle()
    #         text_box.set_val("")  # Reset text box

    #     # Textbox for index input
    #     axbox = figure.add_axes([0.3, 0.02, 0.2, 0.05])  # Position: [left, bottom, width, height]
    #     text_box = TextBox(axbox, "Index:")
    #     text_box.set_val(str(index))  # Set default value
    #     text_box.on_submit(update_plot)  # Update plot when Enter is pressed

    #     # Button to clear the plot
    #     axclear = figure.add_axes([0.55, 0.02, 0.15, 0.05])  # Position for button
    #     clear_button = Button(axclear, "Clear Plot")
    #     clear_button.on_clicked(clear_plot)

    #     # Initial plot
    #     update_plot(str(index))

    #     figure.tight_layout()
    #     plt.show()

api.RegisterNode(LineBroadening_CSI, "LineBroadening_CSI")