import PyInstaller.__main__

PyInstaller.__main__.run([
    'MRSprocessing.py',
    '--noconfirm',
    # '--onefile', # doesn't run
    # own files
    '--hidden-import', 'processing.ProcessingStep',
    '--add-data', 'inout:inout',
    '--add-data', 'resources:resources',
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
])

# zip the contents of dist/MRSprocessing into dist/MRSprocessing.zip
import zipfile
import os
import shutil
with zipfile.ZipFile('dist/MRSprocessing.zip', 'w') as z:
    for root, dirs, files in os.walk('dist/MRSprocessing'):
        for file in files:
            z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), 'dist/MRSprocessing'))
        # add resources directory so that the program can access it
        z.write('resources', 'resources')
    
# remove the dist/MRSprocessing directory
shutil.rmtree('dist/MRSprocessing')