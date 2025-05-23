import processing.api as api
import os
import matplotlib.pyplot as plt
import numpy as np

class CreateHTMLReport(api.ProcessingNode):
    def __init__(self, nodegraph, id):
        self.meta_info = {
            "label": "CreateHTMLReport",
            "author": "Antonia Kaiser",
            "description": "Generates an HTML summary report of the processing steps and LCModel results.",
        }
        self.parameters = [
            api.StringProp(
                idname="output_directory",
                default="output",
                fpb_label="Output Directory"
            ),
            api.StringProp(
                idname="report_filename",
                default="report.html",
                fpb_label="Report Filename"
            )
        ]
        super().__init__(nodegraph, id)
        self.plotSpectrum = False

    def process(self, data):
        output_dir = self.get_parameter("output_directory")
        report_file = os.path.join(output_dir, self.get_parameter("report_filename"))

        if not os.path.exists(output_dir):
            raise ValueError(f"Output directory '{output_dir}' does not exist.")

        html_content = """
        <html>
        <head>
            <title>MRS Processing Report</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                h1, h2 { color: #2C3E50; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #3498DB; color: white; }
                .section { margin-bottom: 20px; }
                .file-link { color: #2980B9; text-decoration: none; }
                iframe { width: 100%; height: 600px; border: none; }
                .code-block { background: #f4f4f4; padding: 10px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; }
            </style>
        </head>
        <body>
        <h1>MRS Processing Report</h1>
        """

        # Pipeline Information
        pipeline_file = os.path.join(output_dir, "pipeline.pipe")
        mrsi_table = os.path.join(output_dir, "MRSinMRS_table.csv")
        overall_result = os.path.join(output_dir, "Result.pdf")

        html_content += "<div class='section'><h2>Pipeline Information</h2>"
        if os.path.exists(pipeline_file):
            html_content += f"<p><a class='file-link' href='pipeline.pipe'>Pipeline File (.pipe)</a></p>"
            # Attempt to read .pipe file content
            try:
                with open(pipeline_file, "r") as f:
                    pipe_content = f.read()
                html_content += f"<h3>Pipeline Summary</h3><div class='code-block'>{pipe_content}</div>"
            except Exception as e:
                html_content += f"<p>Error reading .pipe file: {e}</p>"
        if os.path.exists(mrsi_table):
            html_content += f"<p><a class='file-link' href='MRSinMRS_table.csv'>MRSinMRS Table</a></p>"
        if os.path.exists(overall_result):
            html_content += f"<p><a class='file-link' href='Result.pdf'>Overall Result (PDF)</a></p>"
            html_content += f"<iframe src='Result.pdf'></iframe>"
        html_content += "</div>"

        # Processing Steps
        processing_steps = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d)) and d[0].isdigit()]
        for step in sorted(processing_steps):
            step_path = os.path.join(output_dir, step)
            html_content += f"<div class='section'><h2>Processing Step: {step}</h2>"

            # Results PDF
            result_pdf = os.path.join(step_path, "result.pdf")
            if os.path.exists(result_pdf):
                html_content += f"<p><a class='file-link' href='{step}/result.pdf'>Results (PDF)</a></p>"
                html_content += f"<iframe src='{step}/result.pdf'></iframe>"

            # Quality Control PDF
            qc_pdf = next((f for f in os.listdir(step_path) if f.endswith(".pdf") and f != "result.pdf"), None)
            if qc_pdf:
                html_content += f"<p><a class='file-link' href='{step}/{qc_pdf}'>Quality Control ({qc_pdf})</a></p>"
                html_content += f"<iframe src='{step}/{qc_pdf}'></iframe>"

            # Intermediate Data
            data_path = os.path.join(step_path, "data")
            if os.path.exists(data_path):
                data_files = [f for f in os.listdir(data_path) if f.endswith((".RAW", ".nii"))]
                if data_files:
                    html_content += "<h3>Intermediate Data:</h3><ul>"
                    for file in data_files:
                        html_content += f"<li><a class='file-link' href='{step}/data/{file}'>{file}</a></li>"
                    html_content += "</ul>"

            html_content += "</div>"

        # LCModel Output
        lcmodel_path = os.path.join(output_dir, "LCModel")
        if os.path.exists(lcmodel_path):
            html_content += "<div class='section'><h2>LCModel Output</h2><ul>"

            lcmodel_files = [f for f in os.listdir(lcmodel_path) if f.endswith((".control", ".coord", ".csv", ".ps", ".print", ".nii", ".table", ".H2O", ".RAW"))]
            for file in lcmodel_files:
                file_path = f"LCModel/{file}"
                html_content += f"<li><a class='file-link' href='{file_path}'>{file}</a></li>"

                # Display LCModel PDF inline
                if file.endswith(".ps"):
                    html_content += f"<iframe src='{file_path}'></iframe
api.RegisterNode(CreateHTMLReport, "CreateHTMLReport") 
