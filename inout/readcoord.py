def ReadlcmCoord(filename):

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
    
    def generator(path):
        with open(path) as file:
            for line in file:
                for word in line.split():
                    yield word

    words = generator(filename)

    def skipto(string):
        word = ''
        while word.find(string) == -1:
            word = next(words)
        return word

    skipto("Metabolite")
    index = 0
    while True:
        conc['c'] = float(next(words))
        temp = next(words).removesuffix('%')
        if temp == "lines": break
        conc['SD'] = temp
        word = next(words)
        try: float(word)
        except: # probably "number+Scyllo" without space
            if '+' in word and word[0] != '+' and word[-1] != '+' and word[word.find('+') - 1].isdigit():
                split = word.split('+', 1)
                conc['c_cr'] = split[0]
                conc['name'] = split[1]
            else:
                continue
        else:
            conc['c_cr'] = word
            conc['name'] = next(words).strip()
        lcmdata['conc'].append(conc.copy())
        index += 1

    skipto("FWHM")
    next(words) # Read and discard '='
    lcmdata['linewidth'] = float(next(words))
    
    skipto("S/N")
    next(words) # Read and discard '='
    lcmdata['SNR'] = float(next(words))
    
    skipto("shift")
    word = next(words)
    if word == '=': lcmdata['datashift'] = float(next(words))
    else: lcmdata['datashift'] = word.removeprefix('=')
    
    word = skipto("Ph:")
    if word == "Ph:": lcmdata['ph0'] = float(next(words))
    else: lcmdata['ph0'] = word[3:]

    skipto("deg")
    lcmdata['ph1'] = float(next(words))
    
    skipto("extr")
    nbpoints = int(next(words))
    
    skipto("NY")
    lcmdata['ppm'] = [float(next(words)) for i in range(nbpoints)]
    
    skipto("follow")
    lcmdata['spec'] = [float(next(words)) for i in range(nbpoints)]
    
    skipto("follow")
    lcmdata['fit'] = [float(next(words)) for i in range(nbpoints)]
    
    skipto("follow")
    lcmdata['baseline'] = [float(next(words)) for i in range(nbpoints)]
    
    lcmdata['residue'] = [lcmdata['spec'][i] - lcmdata['fit'][i] for i in range(nbpoints)]
    
    k = 0
    for i in range(len(lcmdata['conc'])):
        key = next(words)
        if key == "lines": # start of fitting warnings
            break
        index = -1
        for j in range(len(lcmdata['conc'])):
            if lcmdata['conc'][j]['name'] == key:
                index = j
                break
        if index == -1 or lcmdata['conc'][index]['c'] == 0 or ('+' in key and key[0] != '+'):
            continue
        lcmdata['metab'].append(key)
        skipto("=")
        next(words)
        subspec_values = [float(next(words)) for _ in range(nbpoints)]
        lcmdata['subspec'].append([float(x) - lcmdata['baseline'][j] for j, x in enumerate(subspec_values)])
        k += 1
    lcmdata['nfit'] = k
    return lcmdata