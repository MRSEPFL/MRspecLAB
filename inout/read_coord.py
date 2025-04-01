import re
from interface import utils

def ReadlcmCoord(filename, mrs_type='1H'):
    import re
    # Updated template includes new key 'c_ref'
    lcmdata = {
        'ppm': [],
        'spec': [],
        'fit': [],
        'baseline': [],
        'residue': [],
        'conc': [],
        'linewidth': 0.0,
        'SNR': 0.0,
        'datashift': 0.0,
        'ph0': 0.0,
        'ph1': 0.0,
        'metab': [],
        'nfit': 0,
        'subspec': [],
        'crnaa': ''
    }

    conc_template = {
        'name': '',
        'c_cr': 0.0,
        'c_ref': 0.0,
        'c': 0.0,
        'SD': ''
    }

    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{filename}' not found.")
    
    nbpoints = 0
    line_idx = 0
    total_lines = len(lines)
    
    while line_idx < total_lines:
        line = lines[line_idx].strip()

        if not line:
            line_idx += 1
            continue
        
        # Parse %SD Section
        if line.startswith("%SD"):
            parts = line.split()
            if len(parts) > 1:
                crnaa = parts[1]
            else:
                line_idx += 1
                if line_idx < total_lines:
                    next_line = lines[line_idx].strip()
                    crnaa = next_line.split()[0] if next_line else ''
                else:
                    raise ValueError("Missing crnaa after %SD")
            if mrs_type.upper() == '1H':
                if 'Cr' in crnaa:
                    lcmdata['crnaa'] = 'Cr'
                elif 'NAA+NA' in crnaa:
                    lcmdata['crnaa'] = 'NAA+NA'
                else:
                    lcmdata['crnaa'] = crnaa
            elif mrs_type.upper() == '31P':
                if 'PCr' in crnaa:
                    lcmdata['crnaa'] = 'PCr'
                elif 'γ-ATP' in crnaa or 'G-ATP' in crnaa:
                    lcmdata['crnaa'] = 'γ-ATP'
                else:
                    lcmdata['crnaa'] = crnaa
            else:
                lcmdata['crnaa'] = crnaa
            line_idx += 1
            continue
        
        # Parse Metabolite Concentration Table
        # Modified regex similar to the old version to capture possible '+' in the reference field.
        metabolite_pattern = re.compile(
            r'^([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+([0-9]+)%\s+(\S+)\s+(.+)$'
        )
        
        match = metabolite_pattern.match(line)
        if match:
            try:
                c = float(match.group(1))
                SD = match.group(2)
                c_ref_field = match.group(3)  # May contain a '+' if no space was present.
                name_field = match.group(4).strip()
                name_field = name_field.replace("Conc.", "").strip()
                
                # Try to convert c_ref_field to float.
                try:
                    c_ref_val = float(c_ref_field)
                    c_cr_val = c_ref_val
                except ValueError:
                    # Possibly of the form "number+metabolite"
                    if ('+' in c_ref_field and c_ref_field[0] != '+' and 
                        c_ref_field[-1] != '+' and c_ref_field[c_ref_field.find('+') - 1].isdigit()):
                        parts = c_ref_field.split('+', 1)
                        try:
                            c_ref_val = float(parts[0])
                        except ValueError:
                            c_ref_val = 0.0
                        # Use the part after the plus as the metabolite name if nonempty.
                        if parts[1].strip():
                            name_field = parts[1].strip()
                        c_cr_val = c_ref_val
                    else:
                        # Fallback if conversion fails and no plus sign found.
                        c_ref_val = 0.0
                        c_cr_val = 0.0
                
                conc_entry = conc_template.copy()
                conc_entry['c'] = c
                conc_entry['SD'] = SD
                conc_entry['c_cr'] = c_cr_val
                conc_entry['c_ref'] = c_ref_val  # New key with c_ref information
                conc_entry['name'] = name_field
                lcmdata['conc'].append(conc_entry)
            except ValueError:
                # Log debug information or skip the malformed line.
                # e.g., utils.log_debug(f"Skipping malformed metabolite line at {line_idx + 1}")
                pass
            line_idx += 1
            continue
        
        # Parse FWHM and S/N
        if "FWHM" in line and "S/N" in line:
            fwhm_pattern = re.compile(r'FWHM\s*[:=]\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)')
            sn_pattern = re.compile(r'S/N\s*[:=]\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)')
            
            fwhm_match = fwhm_pattern.search(line)
            sn_match = sn_pattern.search(line)
            
            if fwhm_match:
                try:
                    lcmdata['linewidth'] = float(fwhm_match.group(1))
                except ValueError:
                    raise ValueError("Invalid FWHM value.")
            
            if sn_match:
                try:
                    lcmdata['SNR'] = float(sn_match.group(1))
                except ValueError:
                    raise ValueError("Invalid S/N value.")
            
            line_idx += 1
            continue
        
        if "FWHM" in line:
            fwhm_pattern = re.compile(r'FWHM\s*[:=]\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)')
            fwhm_match = fwhm_pattern.search(line)
            if fwhm_match:
                try:
                    lcmdata['linewidth'] = float(fwhm_match.group(1))
                except ValueError:
                    raise ValueError("Invalid FWHM value.")
            line_idx += 1
            continue
        
        if "S/N" in line:
            sn_pattern = re.compile(r'S/N\s*[:=]\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)')
            sn_match = sn_pattern.search(line)
            if sn_match:
                try:
                    lcmdata['SNR'] = float(sn_match.group(1))
                except ValueError:
                    raise ValueError("Invalid S/N value.")
            line_idx += 1
            continue
        
        # Parse Data Shift
        if "Data shift" in line:
            data_shift_pattern = re.compile(r'Data shift\s*[:=]\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)')
            data_shift_match = data_shift_pattern.search(line)
            if data_shift_match:
                try:
                    lcmdata['datashift'] = float(data_shift_match.group(1))
                except ValueError:
                    raise ValueError("Invalid Data shift value.")
            line_idx += 1
            continue
        
        # Parse Phasing
        if "Ph:" in line:
            ph_numbers = re.findall(r'[-+]?\d*\.\d+|\d+', line)
            if len(ph_numbers) >= 2:
                try:
                    lcmdata['ph0'] = float(ph_numbers[0])
                    lcmdata['ph1'] = float(ph_numbers[1])
                except ValueError:
                    raise ValueError("Invalid Phasing values.")
            else:
                raise ValueError("Incomplete Phasing values.")
            line_idx += 1
            continue
        
        # Parse Number of Points on ppm-axis
        if "points on ppm-axis" in line:
            match = re.match(r'(\d+(?:\.\d+)?)\s+points on ppm-axis', line)
            if match:
                try:
                    nbpoints = int(float(match.group(1)))
                except ValueError:
                    raise ValueError("Invalid number of points on ppm-axis.")
            else:
                raise ValueError("Number of points on ppm-axis not found.")
            ppm_values = []
            line_idx += 1
            while line_idx < total_lines and len(ppm_values) < nbpoints:
                ppm_line = lines[line_idx].strip()
                if not ppm_line:
                    line_idx += 1
                    continue
                ppm_parts = ppm_line.split()
                for val in ppm_parts:
                    try:
                        ppm_values.append(float(val))
                        if len(ppm_values) == nbpoints:
                            break
                    except ValueError:
                        raise ValueError(f"Invalid ppm value: '{val}'")
                line_idx += 1
            if len(ppm_values) != nbpoints:
                raise ValueError("Mismatch in number of ppm points.")
            lcmdata['ppm'] = ppm_values
            continue
        
        # Parse Spectrum Data
        if "phased data points follow" in line:
            spec_values = []
            line_idx += 1
            while line_idx < total_lines and len(spec_values) < nbpoints:
                spec_line = lines[line_idx].strip()
                if not spec_line:
                    line_idx += 1
                    continue
                spec_parts = spec_line.split()
                for val in spec_parts:
                    try:
                        spec_values.append(float(val))
                        if len(spec_values) == nbpoints:
                            break
                    except ValueError:
                        raise ValueError(f"Invalid spec value: '{val}'")
                line_idx += 1
            if len(spec_values) != nbpoints:
                raise ValueError("Mismatch in number of spec points.")
            lcmdata['spec'] = spec_values
            continue
        
        # Parse Fit Data
        if "points of the fit to the data follow" in line:
            fit_values = []
            line_idx += 1
            while line_idx < total_lines and len(fit_values) < nbpoints:
                fit_line = lines[line_idx].strip()
                if not fit_line:
                    line_idx += 1
                    continue
                fit_parts = fit_line.split()
                for val in fit_parts:
                    try:
                        fit_values.append(float(val))
                        if len(fit_values) == nbpoints:
                            break
                    except ValueError:
                        raise ValueError(f"Invalid fit value: '{val}'")
                line_idx += 1
            if len(fit_values) != nbpoints:
                raise ValueError("Mismatch in number of fit points.")
            lcmdata['fit'] = fit_values
            continue
        
        # Parse Baseline Data
        if "background values follow" in line:
            baseline_values = []
            line_idx += 1
            while line_idx < total_lines and len(baseline_values) < nbpoints:
                baseline_line = lines[line_idx].strip()
                if not baseline_line:
                    line_idx += 1
                    continue
                baseline_parts = baseline_line.split()
                for val in baseline_parts:
                    try:
                        baseline_values.append(float(val))
                        if len(baseline_values) == nbpoints:
                            break
                    except ValueError:
                        raise ValueError(f"Invalid baseline value: '{val}'")
                line_idx += 1
            if len(baseline_values) != nbpoints:
                raise ValueError("Mismatch in number of baseline points.")
            lcmdata['baseline'] = baseline_values
            continue
        
        # Parse Subspectra and Metabolites
        if '=' in line and not any(keyword in line.lower() for keyword in ['file', 'table', 'line', 'input']):
            parts = line.split('=', 1)
            if len(parts) != 2:
                # e.g., utils.log_debug(f"Invalid subspectra format at line {line_idx + 1}")
                line_idx += 1
                continue 
            metab_name = parts[0].strip()
            metab_name = metab_name.replace("Conc.", "").strip()
            subspec_str = parts[1].strip()
            subspec_values = []
            # Extract all numerical values from subspec_str
            subspec_parts = subspec_str.replace(',', ' ').split() 
            for val in subspec_parts:
                val_clean = val.strip(',')
                try:
                    subspec_values.append(float(val_clean))
                except ValueError:
                    pass 
            # If not enough subspec values, read from subsequent lines
            while len(subspec_values) < nbpoints and line_idx + 1 < total_lines:
                line_idx += 1
                additional_line = lines[line_idx].strip()
                if not additional_line:
                    continue
                additional_parts = additional_line.replace(',', ' ').split()
                for val in additional_parts:
                    val_clean = val.strip(',')
                    try:
                        subspec_values.append(float(val_clean))
                        if len(subspec_values) == nbpoints:
                            break
                    except ValueError:
                        pass
            if len(subspec_values) == nbpoints:
                # Subtract baseline
                subspec_corrected = [x - b for x, b in zip(subspec_values, lcmdata['baseline'])]
                lcmdata['subspec'].append(subspec_corrected)
                lcmdata['metab'].append(metab_name)
                lcmdata['nfit'] += 1

            line_idx += 1
            continue

        line_idx += 1

    # Calculate Residue
    if lcmdata['spec'] and lcmdata['fit']:
        if len(lcmdata['spec']) != len(lcmdata['fit']):
            raise ValueError("Spec and Fit data lengths do not match.")
        lcmdata['residue'] = [s - f for s, f in zip(lcmdata['spec'], lcmdata['fit'])]
    else:
        raise ValueError("Spec or Fit data missing.")
    
    return lcmdata

def extract_reference(filename):

    with open(filename, 'r') as file:
        # Read through the file line by line
        for line in file:
            # Skip lines until we find the one starting with "Conc."
            if line.strip().startswith("Conc."):
                # Remove leading/trailing spaces and split by multiple spaces
                parts = line.split()
                
                # The third element in the parts should be the metabolite name
                if len(parts) >= 3:
                    return parts[2]  # The third element should be the metabolite (e.g., /g-ATP)
    return None  # Return None if no valid metabolite line is found
