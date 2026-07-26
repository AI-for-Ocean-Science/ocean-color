"""Loisel+2023 Hydrolight synthetic radiative-transfer outputs.

This ``__init__`` marks ``ocpy.hydrolight`` as a regular package so
``setuptools.find_packages()`` includes it in a wheel build (``pip install
./ocpy``). Without it the directory was dropped from installed (non-editable)
copies of ocpy, breaking ``bing.models.bbnw`` -> ``ocpy.water.scattering`` ->
``ocpy.hydrolight.loisel23`` imports at fit time.
"""
