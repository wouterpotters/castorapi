#!/bin/sh
anaconda login

# USER + PASS input

# Build and publish to https://anaconda.org/wouterpotters/castorapi:
cd ~/to/folder/with/castorapi_conda/folder
conda-build castorapi_conda
conda-build --python 3.7 castorapi_conda
conda-build --python 3.6 castorapi_conda
conda-build --python 3.5 castorapi_conda

conda convert --platform all ~/opt/anaconda3/conda-bld/osx-64/castorapi*.bz2 -o ~/opt/anaconda3/conda-bld/
anaconda upload --skip-existing ~/opt/anaconda3/conda-bld/*/castorapi*.bz2