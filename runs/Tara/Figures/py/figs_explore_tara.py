
import os
import numpy as np
import pandas
import datetime

from matplotlib import pyplot as plt
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.crs as ccrs
import cartopy

import seaborn as sns

from oceancolor.tara import io as tara_io
from oceancolor.tara import measures
from oceancolor.tara import spectra
from oceancolor.tara import explore
from oceancolor.utils import cat_utils
from oceancolor.utils import fig_utils

from IPython import embed

def colored_umap(outfile:str, utype:str, metric:str, log_metric:bool=True,
                 vmnx:tuple=None, cmap='viridis'):

    # Load 
    umap_tbl = tara_io.load_tara_umap(utype)
    tara_db = tara_io.load_tara_db()

    # Add metric(s)
    measures.add_derived(tara_db, quantities=[metric])

    # Metric
    if metric == 'Chla':
        # Merge
        umap_tbl['metric'] = np.maximum(tara_db['Chla'].values[umap_tbl.tara_id], 1e-3)
    elif metric == 'POC':
        umap_tbl['metric'] = np.maximum(tara_db['POC'].values[umap_tbl.tara_id], 1e-3)
    elif metric.startswith('ap'): 
        umap_tbl['metric'] = np.maximum(tara_db[metric].values[umap_tbl.tara_id], 1e-4)
    elif 'rap' in metric: 
        parse = metric.split('-')
        ap_A, _ = spectra.single_value(tara_db, float(parse[1]), wv_delta=7., flavor='ap')
        ap_B, _ = spectra.single_value(tara_db, float(parse[2]), wv_delta=7., flavor='ap')
        umap_tbl['metric'] = (ap_A  / ap_B)[umap_tbl.tara_id]
        bad = np.isnan(umap_tbl['metric'])
        umap_tbl['metric'].values[bad] = 1e-3
    else:
        raise ValueError(f"Bad metric: {metric}")

    # Plot me
    fig = plt.figure(figsize=(8, 8))
    plt.clf()
    ax = plt.gca()

    if log_metric:
        cs = np.log10(umap_tbl.metric)
    else:
        cs = umap_tbl.metric

    if vmnx is None:
        vmnx = [None,None]
    sc = ax.scatter(umap_tbl.U0, umap_tbl.U1,
                c=cs, s=1, cmap=cmap,
                vmin=vmnx[0], vmax=vmnx[1])

    # Color bar
    cbaxes = plt.colorbar(sc, pad=0., fraction=0.030)
    lbl = f'log10 {metric}' if log_metric else f'{metric}'
    cbaxes.set_label(lbl, fontsize=15.)

    ax.set_xlabel('U0')
    ax.set_ylabel('U1')
    
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"Saved {outfile}")
 

def sequencer_spectra(outfile:str, utype:str):

    # Load spectra
    rwv_nm, cull_raph, cull_rsig, tara_tbl = explore.prep_spectra()

    # Load Sequencer table
    seq_tbl = tara_io.load_tara_sequencer(utype)

    rows = cat_utils.match_ids(seq_tbl.tara_id, tara_tbl.index, require_in_match=True)

    # plot the ordered dataset
    reorder_raph = cull_raph[rows, :]

    plt.figure(1, figsize=(15, 8))
    ax = plt.gca()
    plt.title("ordered dataset")
    #plt.pcolormesh(rand_raph, cmap="inferno")
    im = ax.pcolormesh(rwv_nm, np.arange(len(rows))+1, np.log10(reorder_raph), cmap="inferno")
    plt.colorbar(im, label="normalized intensity")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("object index")

    fig_utils.set_fontsize(ax, 15.)

    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"Saved {outfile}")

def sequencer_geo(outfile:str, utype:str):
    tformM = ccrs.Mollweide()
    tformP = ccrs.PlateCarree()

    # Load spectra
    rwv_nm, cull_raph, cull_rsig, tara_tbl = explore.prep_spectra()
    # Load Sequencer table
    seq_tbl = tara_io.load_tara_sequencer(utype)

    # Match
    rows = cat_utils.match_ids(seq_tbl.tara_id, tara_tbl.index, require_in_match=True)
    sub_tbl = tara_tbl.iloc[rows]

    # plot the ordered dataset

    fig = plt.figure(figsize=(12,8))
    plt.clf()

    ax = plt.subplot(projection=tformM)

    img = plt.scatter(
        x=sub_tbl.lon,
        y=sub_tbl.lat,
        c=np.arange(len(sub_tbl)),
        cmap='jet',
        #vmin=0.,
        #vmax=vmax, 
        s=1,
        transform=tformP)

    # Coast lines
    ax.coastlines(zorder=10)
    ax.add_feature(cartopy.feature.LAND, 
        facecolor='lightgray', edgecolor='black')
    ax.set_global()
    #ax.legend(loc='lower left')

    # Colorbar
    cb = plt.colorbar(img, orientation='horizontal', pad=0.)
    lbl = 'Order'
    cb.set_label(lbl, fontsize=15.)
    cb.ax.tick_params(labelsize=17)

    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"Saved {outfile}")


def main(flg):
    if flg== 'all':
        flg= np.sum(np.array([2 ** ii for ii in range(25)]))
    else:
        flg= int(flg)

    # Colored UMAP's
    if flg & (2**0):
        '''
        # Absolute
        colored_umap('Tara_UMAP_abs_chla.png', 'abs', 'Chla')
        '''
        # Normalized with Chla
        colored_umap('Tara_UMAP_norm_chla.png', 'norm', 'Chla', cmap='jet')

        # POC
        colored_umap('Tara_UMAP_norm_POC.png', 'norm', 'POC', cmap='jet')

        # ap425
        #colored_umap('Tara_UMAP_norm_ap425.png', 'norm', 'ap425')

        # ap410 / ap445
        #colored_umap('Tara_UMAP_norm_ap415_ap445.png', 'norm', 'rap-415-445', vmnx=[-0.5, 0.5])#, log_metric=False)

    # Sequencer spectra
    if flg & (2**1):
        sequencer_spectra('Tara_Sequencer_Spectra_abs.png', 'abs')

    # Sequencer geo
    if flg & (2**2):
        sequencer_geo('Tara_Sequencer_Geo_abs.png', 'abs')


# Command line execution
if __name__ == '__main__':
    import sys

    if len(sys.argv) == 1:
        flg_fig = 0
        #flg_fig += 2 ** 0  # Tara UMAP
        #flg_fig += 2 ** 1  # Sequence spectra
        flg_fig += 2 ** 2  # Sequence geo
    else:
        flg_fig = sys.argv[1]

    main(flg_fig)