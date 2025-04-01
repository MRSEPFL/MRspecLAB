import os
from inout.read_mrs import load_file

def group_files_by_header(filepaths, preferred_vendor=None):
    """
    Group files by header metadata.

    Parameters:
      filepaths (list): List of file paths.
      preferred_vendor (str): Optional, if you want to restrict to a certain vendor's grouping logic (e.g., 'Siemens').

    Returns:
      dict: Dictionary where keys are the grouping identifiers and values are lists of file paths.
    """
    groups = {}
    for filepath in filepaths:
        try:
            # load_file returns: data, header, dtype, vendor
            data, header, dtype, vendor = load_file(filepath)
        except Exception as e:
            # If header reading fails, fallback on the parent folder as key.
            header = {}
        
        # If a preferred vendor is provided, check that the current file matches.
        if preferred_vendor is not None and vendor is not None:
            if vendor.lower() != preferred_vendor.lower():
                # Skip or handle differently if not the vendor of interest.
                group_key = os.path.dirname(filepath)
            else:
                group_key = None
        else:
            group_key = None

        if header:
            # For Siemens files, try to use SeriesInstanceUID first.
            if vendor and vendor.lower() == 'siemens':
                group_key = header.get("SeriesInstanceUID")
                # If not available, try using "Sequence" since that is how your reader names it.
                if not group_key:
                    group_key = header.get("Sequence")
            else:
                
                group_key = header.get("ProtocolName") or header.get("Sequence")
        
        # If no grouping key was found, fallback on the parent folder (or a filename heuristic)
        if not group_key:
            group_key = os.path.dirname(filepath)
        
        # Append the file to the appropriate group.
        groups.setdefault(group_key, []).append(filepath)
    
    return groups

def group_water_files_by_header(water_filepaths):
    """
    Group water files by header metadata.
    
    This function works similarly to group_files_by_header(), but you can
    adjust it if water references have their own unique header fields.
    
    Parameters:
      water_filepaths (list): List of water file paths.
    
    Returns:
      dict: Dictionary with grouping keys and corresponding water file lists.
    """
    groups = {}
    for filepath in water_filepaths:
        try:
            # load_file returns: data, header, dtype, vendor
            data, header, dtype, vendor = load_file(filepath)
        except Exception as e:
            header = {}
        
        # Here you might check for a water‐specific field.
        # For example, if water references are stored with a specific sequence name:
        group_key = header.get("Sequence")
        # If there is no water-specific key, fall back on a heuristic
        if not group_key:
            group_key = os.path.dirname(filepath)
        
        groups.setdefault(group_key, []).append(filepath)
    return groups