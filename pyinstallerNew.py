import os
import sys
import PyInstaller.__main__

sys.setrecursionlimit(sys.getrecursionlimit() * 5)

# For logging, determine the spec2nii package path.
import spec2nii
SPEC2NII_PATH = os.path.dirname(spec2nii.__file__)
print("Spec2NII package path:", SPEC2NII_PATH)

# Construct a spec file as a string.
# Note: We use PyInstaller hook utilities to collect data files and submodules.
spec_content = r'''
# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
block_cipher = None

a = Analysis(
    ['MRSpecLAB.py'],
    pathex=[os.getcwd()],
    binaries=[],
    # Include your own data files and also collect all files from spec2nii and ometa.
    datas=[
        ('inout', 'inout'),
        ('lcmodel', 'lcmodel'),
        ('nodes', 'nodes'),
    ] + collect_data_files('spec2nii', include_py_files=True)
      + collect_data_files('ometa', include_py_files=True)
      + collect_data_files('nifti_mrs.standard', include_py_files=True),
    hiddenimports=[
        'processing.processing_node',
        'spec2nii',
        'spec2nii.Siemens',
        'spec2nii.Siemens.dicomfunctions',
        'spec2nii.GSL',
        'spec2nii.Philips',
        'spec2nii.GE',
        'spec2nii.bruker',
        'pydicom',
        'pydicom.encoders',
        'pydicom.encoders.gdcm',
        'pydicom.encoders.pylibjpeg',
        'pydicom.encoders.native',
        'nifti_mrs',
        'nifti_mrs.standard',
        'importlib_resources',
        'importlib_resources.trees',
        'wx',
        'wx._xml'
    ] + collect_submodules('spec2nii')
      + collect_submodules('nifti_mrs')
      + collect_submodules('pydicom')
      + collect_submodules('terml._generated'),
    hookspath=[],
    runtime_hooks=[],
    excludes=['cv2', 'babel', 'PyQt5'],
    #noarchive=True,  # Modules will be left as separate files.
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MRSpecLAB',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MRSpecLAB',
)
'''

# Write the spec file to disk.
spec_filename = os.path.join(os.getcwd(), "MRSpecLAB.spec")
with open(spec_filename, "w") as f:
    f.write(spec_content)

# Run PyInstaller using the generated spec file.
PyInstaller.__main__.run([spec_filename])

# Optionally, you can remove the spec file after building:
# os.remove(spec_filename)
