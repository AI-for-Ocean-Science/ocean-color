""" MCMC module for remote sensing """

import os
from importlib import resources

import numpy as np

import matplotlib.pyplot as plt

import emcee
import corner

import torch

from oceancolor.remote.nn import SimpleNet
from oceancolor.remote import io as remote_io


def log_prob(ab, Rs, model, device):
    pred = model.prediction(ab, device)
    #
    sig = 0.05 * Rs
    #
    return -1*0.5 * np.sum( (pred-Rs)**2 / sig**2)


def run_emcee_nn(nn_model, Rs, nwalkers:int=32, nsteps:int=20000,
                 save_file:str=None):

    # Device for NN
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Init
    ndim = nn_model.ninput
    p0 = np.random.rand(nwalkers, ndim)

    # Set up the backend
    # Don't forget to clear it in case the file already exists
    if save_file is not None:
        backend = emcee.backends.HDFBackend(save_file)
        backend.reset(nwalkers, ndim)
    else:
        backend = None

    sampler = emcee.EnsembleSampler(nwalkers, ndim, log_prob, 
                                    args=[Rs, nn_model, device],
                                    backend=backend)

    # Burn in
    print("Running burn-in")
    state = sampler.run_mcmc(p0, 1000)
    sampler.reset()

    # Run
    print("Running full model")
    sampler.run_mcmc(state, nsteps)

    print(f"All done: Wrote {save_file}")

    # Return
    return sampler

if __name__ == '__main__':

    # Load Hydrolight
    print("Loading Hydrolight data")
    ab, Rs, d_l23 = remote_io.load_loisel_2023_pca()

    # Load model
    model_file = os.path.join(resources.files('oceancolor'), 
                              'remote', 'model_20000.pth')
    print(f"Loading model: {model_file}")
    model = torch.load(model_file)

    # idx=200
    idx = 200
    save_file = f'MCMC_NN_i{idx}.h5'

    run_emcee_nn(model, Rs[idx], save_file=save_file)