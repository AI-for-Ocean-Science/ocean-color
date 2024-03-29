""" Module for spectral analysis of Tara Oceans data. """

import numpy as np
import pandas
from scipy.interpolate import interp1d

from IPython import embed

def parse_wavelengths(inp, flavor:str='ap'):
    """ Parse wavelengths from a row/table of the Tara Oceans database. 

    Args:
        inp (pandas.Series or pandas.DataFrame):
            One row or table of the Tara Oceans database.
        flavor (str, optional):
            Flavor of spectrum to load [ap, cp]

    Returns:
        tuple: wavelengths (nm) [np.ndarray], keys [np.ndarray]
    """
    keys, wv_nm = [], []

    for key in inp.keys():
        if key[0:2] == flavor:
            keys.append(key)
            # Wavelength
            wv_nm.append(float(key[2:]))

    # Recast
    wv_nm = np.array(wv_nm)
    keys = np.array(keys)

    # Sort
    srt = np.argsort(wv_nm)
    wv_nm = wv_nm[srt]
    keys = keys[srt]

    # Return
    return wv_nm, keys

def spectbl_from_keys(tbl:pandas.DataFrame, keys:np.ndarray):
    # Read
    values, err_vals = [], []
    for key in keys:
        for ilist, ikey in zip([values,err_vals], 
                               [key, 'sig_'+key]):
            # Slurp
            val = tbl[ikey].values
            # Masked?
            val[np.isclose(val, -9999.)] = np.nan
            ilist.append(val)

    # Concatenate
    values = np.reshape(np.concatenate(values), 
                    (len(keys), len(tbl)))
    err_vals = np.reshape(np.concatenate(err_vals), 
                    (len(keys), len(tbl)))

    return values, err_vals

def spectra_from_table(tbl:pandas.DataFrame, flavor:str='ap'):
    """ Load spectra from a table of the Tara Oceans database.

    Args:
        tbl (pandas.DataFrame): 
            Table of the Tara Oceans database.
        flavor (str, optional): 
            Flavor of spectrum to load [ap, cp]

    Returns:
        tuple: wavelengths (nm), values, error
    """

    # Wavelengths
    wv_nm, keys = parse_wavelengths(tbl, flavor=flavor)

    # Do it
    values, err_vals = spectbl_from_keys(tbl, keys)

    # Return
    return wv_nm, values, err_vals

def average_spectrum(tbl:pandas.DataFrame, flavor:str='ap'):
    """ Average spectrum from a table of the Tara Oceans database.

    Note that NaN in the data are ignored.

    Args:
        tbl (pandas.DataFrame): 
            Table of the Tara Oceans database.
        flavor (str, optional): 
            Flavor of spectrum to load [ap, cp]

    Returns:
        tuple: wavelengths (nm), values, error
    """
    wv_nm, values, err_vals = spectra_from_table(tbl, flavor=flavor)

    # Average
    avg_vals = np.nanmean(values, axis=1)
    avg_error = np.nanmean(err_vals, axis=1)

    # Cut
    gd_spec = np.isfinite(avg_vals)
    wv_nm = wv_nm[gd_spec]
    avg_vals = avg_vals[gd_spec]
    avg_error = avg_error[gd_spec]

    # Return
    return wv_nm, avg_vals, avg_error

def spectrum_from_row(row:pandas.Series, flavor:str='ap',
                      keep_nan:bool=False):
    """ Load a spectrum from a row in the Tara Oceans database.

    Args:
        row (pandas.Series): 
            One row from the Tara Oceans database.
        flavor (str, optional): 
            Flavor of spectrum to load [ap, cp]  
            Defaults to 'ap'.
        keep_nan (bool, optional):
            Keep NaN values in the spectrum.  Default is False

    Returns:
        tuple: wavelength (nm), values, error
    """
    # Wavelengths
    wv_nm, keys = parse_wavelengths(row, flavor=flavor)

    # Read
    values, err_vals = [], []
    for key in keys:
        for ilist, ikey in zip([values,err_vals], 
                               [key, 'sig_'+key]):
            val = row[ikey]
            # Mask?
            val = np.nan if np.isclose(val, -9999.) else val
            # Save
            ilist.append(val)

    # Recast
    values = np.array(values)
    err_vals = np.array(err_vals)

    # Cut down
    if not keep_nan:
        gd_spec = np.isfinite(values)
        wv_nm = wv_nm[gd_spec]
        values = values[gd_spec]
        err_vals = err_vals[gd_spec]

    
    # Return
    return wv_nm, values, err_vals

def single_value(tbl:pandas.DataFrame, wv_cen:float, 
                 wv_delta:float=10., flavor:str='ap'):
    """ Return ap or cp at a single wavelength from a table of the Tara Oceans database

    This is generated by taking an average of 
     +/- wv_delta/2. around wv_cen

    Args:
        tbl (pandas.DataFrame): Table of the Tara Oceans database.
        wv_cen (float): Central wavelength (nm)
        wv_delta (float, optional): Range of wavelength to average over. Defaults to 10..
        flavor (str, optional): 
            Flavor of spectrum [ap, cp]  
            Defaults to 'ap'.

    Returns:
        tuple: value, error [np.ndarray, np.ndarray]
    """
    # Wavelengths
    wv_nm, keys = parse_wavelengths(tbl, flavor=flavor)

    # Cut
    gd_wv = np.where((wv_nm >= wv_cen-wv_delta/2.) & (
        wv_nm <= wv_cen+wv_delta/2.))[0]
    gd_keys = keys[gd_wv]

    # Build
    values, err_vals = spectbl_from_keys(tbl, gd_keys)

    # Average
    value = np.nanmean(values, axis=0)
    sig = np.nanmean(err_vals, axis=0)
    
    # Return
    return value, sig

def interpolate_to_grid(wv_nm:np.ndarray, values:np.ndarray, 
                  err_vals:np.ndarray, wv_grid:np.ndarray):
    """ Rebin a spectrum to a new wavelength grid.

    Args:
        wv_nm (np.ndarray): Wavelengths (nm)
        values (np.ndarray): Values
        err_vals (np.ndarray): Error values
        wv_grid (np.ndarray): New wavelength grid

    Returns:
        tuple: values, error [np.ndarray, np.ndarray]
    """
    # Interpolate
    f_values = interp1d(wv_nm, values, 
        bounds_error=False, fill_value=np.nan)
    f_err = interp1d(wv_nm, err_vals, 
        bounds_error=False, fill_value=np.nan)

    # Evaluate
    new_values = f_values(wv_grid)
    new_err = f_err(wv_grid)

    # Return
    return new_values, new_err

def rebin_to_grid(wv_nm:np.ndarray, values:np.ndarray, 
                  err_vals:np.ndarray, wv_grid:np.ndarray):
    """ Rebin spectra to a new wavelength grid.

    Simple nearest neighbor binning (no interpolation)

    Args:
        wv_nm (np.ndarray): Wavelengths (nm)
        values (np.ndarray): Values
        err_vals (np.ndarray): Error values
        wv_grid (np.ndarray): New wavelength grid

    Returns:
        tuple: wave, values, error [np.ndarray (nwv), np.ndarray (nspec,nwv), np.ndarray]
    """
    gd_values = np.isfinite(values)
    mask = gd_values.astype(int)

    # Loop on wv_grid
    rebin_values = np.zeros((values.shape[1], wv_grid.size-1))
    rebin_err = np.zeros((values.shape[1], wv_grid.size-1))
    rebin_wave = np.zeros(wv_grid.size-1)
    
    for iwv in range(wv_grid.size-1):
        w0 = wv_grid[iwv]
        w1 = wv_grid[iwv+1]
        rebin_wave[iwv] = (w0+w1)/2.
        # In grid?
        gd = np.where((wv_nm >= w0) & (wv_nm < w1))[0]

        # Add em in
        isum = np.nansum(values[gd]*mask[gd], axis=0) / np.sum(mask[gd],axis=0)
        esum = np.nansum(err_vals[gd]*mask[gd], axis=0) / np.sum(mask[gd],axis=0)

        # Fill
        rebin_values[:,iwv] = isum
        rebin_err[:,iwv] = esum

    # Return
    return rebin_wave, rebin_values, rebin_err
