import PyInstaller.__main__
import sys ; sys.setrecursionlimit(sys.getrecursionlimit() * 5)

PyInstaller.__main__.run([
    'MRSprocessing.py',
    '--noconfirm',
    '--onefile',
    # own files
    '--hidden-import', 'processing.processing_node',
    '--add-data', 'inout:inout',
    '--add-data', 'lcmodel:lcmodel',
    '--add-data', 'nodes:nodes',
    # external libraries
    '--hidden-import', 'pydicom.encoders.gdcm',
    '--hidden-import', 'pydicom.encoders.pylibjpeg',
    '--hidden-import', 'pydicom.encoders.native',
    '--collect-submodules', 'ometa._generated',
    '--collect-submodules', 'terml._generated',
    '--hidden-import', 'wx',
    '--hidden-import', 'wx._xml',
    # exclude
    '--exclude-module', 'cv2',
    '--exclude-module', 'babel',
    '--exclude-module', 'PyQt5',
])