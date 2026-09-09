""" Tests for ocpy.pace.io """

import numpy as np
from netCDF4 import Dataset

from ocpy.pace import io as pace_io


def write_iop_file(fn, with_unc_442: bool = True):
    """Write a tiny synthetic PACE L2 IOP file (3x3 pixels, 3 bands)."""
    nx, ny, nw = 3, 3, 3
    with Dataset(fn, "w") as ds:
        ds.setncattr("title", "synthetic IOP")
        ds.createDimension("number_of_lines", nx)
        ds.createDimension("pixels_per_line", ny)
        ds.createDimension("wavelength_3d", nw)
        dims2d = ("number_of_lines", "pixels_per_line")
        dims3d = dims2d + ("wavelength_3d",)

        nav = ds.createGroup("navigation_data")
        lat2d = np.repeat(np.linspace(44.0, 44.2, nx)[:, None], ny, axis=1)
        lon2d = np.repeat(np.linspace(-31.0, -30.8, ny)[None, :], nx, axis=0)
        nav.createVariable("latitude", "f4", dims2d)[:] = lat2d
        nav.createVariable("longitude", "f4", dims2d)[:] = lon2d

        sbp = ds.createGroup("sensor_band_parameters")
        sbp.createVariable("wavelength_3d", "f4", ("wavelength_3d",))[:] = [
            440.0, 470.0, 500.0]

        gd = ds.createGroup("geophysical_data")
        gd.createVariable("l2_flags", "i4", dims2d)[:] = 0
        for name in ("a", "bb", "aph"):
            gd.createVariable(name, "f4", dims3d)[:] = 0.05
        scalars = {
            "adg_s": 0.018, "adg_442": 0.03, "bbp_442": 0.004,
            "bbp_unc_442": 0.0005, "bbp_s": 1.2,
        }
        if with_unc_442:
            scalars["aph_unc_442"] = 0.01
            scalars["adg_unc_442"] = 0.006
        for name, val in scalars.items():
            gd.createVariable(name, "f4", dims2d)[:] = val


def test_load_iop_l2_reads_unc_442(tmp_path):
    fn = str(tmp_path / "iop.nc")
    write_iop_file(fn, with_unc_442=True)
    xds, flags = pace_io.load_iop_l2(fn)
    assert flags.shape == (3, 3)
    for name in ("a", "bb", "aph", "adg_s", "adg_442", "bbp_442",
                 "bbp_unc_442", "bbp_s", "aph_unc_442", "adg_unc_442"):
        assert name in xds
    assert float(xds["aph_unc_442"].values[1, 1]) == np.float32(0.01)
    assert float(xds["adg_unc_442"].values[1, 1]) == np.float32(0.006)
    assert xds["adg_unc_442"].dims == ("x", "y")


def test_load_iop_l2_tolerates_missing_unc_442(tmp_path):
    fn = str(tmp_path / "iop_no_unc.nc")
    write_iop_file(fn, with_unc_442=False)
    xds, _ = pace_io.load_iop_l2(fn)
    assert "aph_unc_442" not in xds and "adg_unc_442" not in xds
    assert "bbp_unc_442" in xds
