def ReadlcmCoord(filename, displayinfo=True):

    lcmdata = {
        'ppm': 0,
        'spec': 0,
        'fit': 0,
        'baseline': 0,
        'residue': 0,
        'conc': [],
        'linewidth': 0,
        'SNR': 0,
        'datashift': 0,
        'ph0': 0,
        'ph1': 0,
        'metab': [],
        'nfit': 0,
        'subspec': []
    }
    
    conc = {
        'name': 0,
        'c_cr': 0,
        'c': 0,
        'SD': 0
    }
    
    if displayinfo:
        print('**** READING LCMODEL RESULTS IN .COORD FILE *****\n\n')
        print(f'Opening file {filename}\n')
    
    def generator(path):
        with open(path) as file:
            for line in file:
                for word in line.split():
                    yield word

    words = generator(filename)

    def skipto(string):
        word = ''
        while word != string:
            word = next(words)
        # if word == string:
        # print("Found " + string)

    # Discard text until beginning of concentrations table (preceded by word 'Metab.')
    skipto("Metabolite")

    # Read concentration values
    index = 0
    endtable = False
    while not endtable:
        conc['c'] = float(next(words))
        temp = next(words).removesuffix('%')
        if temp == "lines": break
        conc['SD'] = temp
        conc['c_cr'] = float(next(words))
        conc['name'] = next(words).strip()
        lcmdata['conc'].append(conc.copy())
        index += 1
    
    # lcmdata['conc'].pop()  # Discard last line of table
    
    # Discard text until linewidth (preceded by word 'FWHM')
    skipto("FWHM")
    
    # Read linewidth
    next(words) # Read and discard '='
    lcmdata['linewidth'] = float(next(words))
    
    # Discard text until S/N (preceded by word 'S/N=')
    skipto("S/N")
    next(words) # Read and discard '='
    lcmdata['SNR'] = float(next(words))
    
    # Discard text until Data shift (preceded by word ' Data shift=')
    skipto("shift")
    word = next(words)
    if word == '=': lcmdata['datashift'] = float(next(words))
    else: lcmdata['datashift'] = word.removeprefix('=')
    
    # Discard text until Ph: (preceded by word 'Ph:')
    skipto("Ph:")
    
    # Read zero-order phase, in deg
    lcmdata['ph0'] = float(next(words))
    
    skipto("deg")
    
    # Read first-order phase, in deg/ppm
    lcmdata['ph1'] = float(next(words))
    
    # Discard text until number of data points (preceded by word 'extrema')
    skipto("extrs.")
    
    # Read number of points
    nbpoints = int(next(words))
    
    # Read and discard text 'points on ppm-axis = NY'
    skipto("NY")
    # Read ppm values
    lcmdata['ppm'] = [float(next(words)) for i in range(nbpoints)]
    
    # Read and discard text 'NY phased data points follow'
    skipto("follow")
    # Read data values
    lcmdata['spec'] = [float(next(words)) for i in range(nbpoints)]
    
    # Read and discard text 'NY points of the fit to the follow'
    skipto("follow")
    # Read fit values
    lcmdata['fit'] = [float(next(words)) for i in range(nbpoints)]
    
    # Read and discard text 'NY background values follow'
    skipto("follow")
    # Read baseline values
    lcmdata['baseline'] = [float(next(words)) for i in range(nbpoints)]
    
    # Calculate residual
    lcmdata['residue'] = [lcmdata['spec'][i] - lcmdata['fit'][i] for i in range(nbpoints)]
    
    # Read and discard text 'metabo'
    k = 0
    for i in range(len(lcmdata['conc'])):
        if displayinfo:
            print(f'{i+1}: {lcmdata["conc"][i]["name"]}')
        
        if '+' in lcmdata['conc'][i]['name'] and lcmdata['conc'][i]['name'][0] != '+':
            continue
        
        if lcmdata['conc'][i]['c'] != 0:
            word = next(words)
            if lcmdata['conc'][i]['name'] != word:
                print("Error: metabolite name mismatch")
                print(f"Expected {lcmdata['conc'][i]['name']}, got {word}")
                exit()
            lcmdata['metab'].append(word)
            skipto("=")
            next(words)
            # Read baseline values
            subspec_values = [float(next(words)) for i in range(nbpoints)]
            lcmdata['subspec'].append([float(x) - lcmdata['baseline'][j] for j, x in enumerate(subspec_values)])
            k += 1
    
    lcmdata['nfit'] = k
    return lcmdata

import os
if __name__ == "__main__":
    lcmdata = ReadlcmCoord(os.path.join(os.path.dirname(__file__), "output", "result.coord"))
    print("\n\n\n")
    for key in ['conc', 'linewidth', 'SNR', 'datashift', 'ph0', 'ph1', 'metab', 'nfit']:
        print(key, lcmdata[key])