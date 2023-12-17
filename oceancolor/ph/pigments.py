""" Pigment data and the like """
import numpy as np

from scipy.interpolate import interp1d
from scipy.optimize import curve_fit

from oceancolor.ph import load_data as load_ph

pig_peak_loc=[406,434,453,470,492,523,550,584,617,
          638,660,675]  
pig_FWHM = [37.68 , 28.26 , 28.26 , 30.615, 37.68 , 
        32.97 , 32.97 , 37.68 , 30.615, 25.905, 
        25.905, 23.55]

def gen_pigment(wave:np.ndarray, idx:int):

    # Gaussian with peak_loc and FWHM
    profile = np.exp(-4*np.log(2)*((wave-pig_peak_loc[idx])/pig_FWHM[idx])**2)
    return profile


def a_chl(wave:np.ndarray, ctype:str='a',
          source:str='bricaud',
          pigment:str=None):
    """
    Load up the chlorophyll absorption coefficient.

    Args:
        wave (np.ndarray): Array of wavelengths.
        ctype (str, optional): Chlorophyll type. Defaults to 'a'.
            Options are: 'a' (default), 'b', 'c12'
        source (str, optional): Data source. Defaults to 'bricaud'.

    Returns:
        np.ndarray: Array of chlorophyll absorption coefficients.
    """
    # Load data
    if source == 'clementson':
        _, df = load_ph.clementson2019()
    elif source == 'bricaud':
        df = load_ph.bricaud()
    else:
        raise IOError(f"Bad input source {source}")

    # Type
    if pigment is not None:
        key = pigment
    else:
        key = f'Chl-{ctype}'

    # Interpolate
    f = interp1d(df.wave, df[key], kind='linear',
                 bounds_error=False, fill_value=0.)

    # Rinish
    return f(wave)


def fit_a_chl(wave:np.ndarray, a_ph:np.ndarray,
              add_pigments:list=None):
    """
    Fits Chl pigments to a presumed a_chl spectrum.

    Args:
        wave (np.ndarray): Array of wavelengths.
            These can be restricted to a subset
        a_ph (np.ndarray): Array of absorption coefficients.

    Returns:
        tuple: A tuple containing the optimized parameters and covariance matrix of the fit.
    """
    chla = a_chl(wave, ctype='a')
    chlb = a_chl(wave, ctype='b')
    chlc = a_chl(wave, ctype='c12')

    nrm_wv = [673.,440.,440.]
    p0 = []
    for wv, pig in zip(nrm_wv, [chla, chlb, chlc]):
        iwv = np.argmin(np.abs(wave-wv))
        nrm = pig[iwv]/a_ph[iwv]
        p0.append(1./nrm)

    # Additoinal pigments??
    if add_pigments is not None:
        for pigment in add_pigments:
            p0.append(10.)

    # Func
    #def func(x, Aa, Ab, Ac):
    def func(*pargs):
        # pargs[0] is not used
        # Chl
        a = pargs[1]*chla + pargs[2]*chlb + pargs[3]*chlc 
        # Others?
        if add_pigments is not None:
            for i, pigment in enumerate(add_pigments):
                a += pargs[4+i]*pigment
        # Return
        return a
    # Fit
    return curve_fit(func, wave, a_ph, p0=p0) #sigma=sig_y, #maxfev=maxfev)
