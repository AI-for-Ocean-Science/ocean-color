""" PCA this and that in Remote Sensing """

import os
import numpy as np

from sklearn import decomposition

import xarray

def reconstruct(pca_fit, vec):
    Y = pca_fit.transform(vec)
    recon = np.dot(Y, pca_fit.components_)
    # Return
    return recon[0] # Flatten

def l23_hydrolight(X:int, Y:int, Na:int, Nb:int,
                   save_outputs:str=None):
    """_summary_

    Data may be downloaded from:
    https://datadryad.org/stash/dataset/doi:10.6076/D1630T

    Args:
        X (int): _description_
        Y (int): _description_
        Na (int): _description_
        Nb (int): _description_
        save_outputs (str, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """

    # Load up the data
    l23_path = os.path.join(os.getenv('OS_COLOR'),
                            'data', 'Loisel2023')
    variable_file = os.path.join(l23_path, 
                                 f'Hydrolight{X}{Y:02d}.nc')
    ds = xarray.load_dataset(variable_file)

    # Fit
    pca_fit_a = decomposition.PCA(n_components=Na).fit(ds.a.data)
    pca_fit_b = decomposition.PCA(n_components=Nb).fit(ds.b.data)

    # Save?
    if save_outputs:
        a_coeff = pca_fit_b.transform(ds.a.data)
        b_coeff = pca_fit_b.transform(ds.b.data)
        
        # 
        np.savez(save_outputs,
                 a=a_coeff,
                 b=b_coeff,
                 Rs=ds.Rrs.data)
        print(f'Wrote: {save_outputs}')
        

    # All done
    return pca_fit_a, pca_fit_b


if __name__ == '__main__':
    l23_path = os.path.join(os.getenv('OS_COLOR'),
                            'data', 'Loisel2023')
    outfile = os.path.join(l23_path, 'pca_ab_33_Rrs.npz')
    l23_hydrolight(4, 0, 3, 3, save_outputs=outfile)