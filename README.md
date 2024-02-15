# hypso-satpy

## Installation
1. Install Satpy and dependencies
    - [SatPy installation instructions](https://satpy.readthedocs.io/en/stable/install.html)
2. Clone repository
3. Edit ~./profile and update `SATPY_CONFIG_PATH` to point at the git repository directory
    - Example: `export SATPY_CONFIG_PATH=/home/cameron/Projects/hypso-satpy/`
4. Run `source ~/.profile`

## Documentation
- [Satpy Custom Readers](https://satpy.readthedocs.io/en/stable/dev_guide/custom_reader.html)
- [Pyresample Geometry Definitions](https://pyresample.readthedocs.io/en/latest/howtos/geo_def.html)
- [Resampling of Swath Data](https://pyresample.readthedocs.io/en/latest/howtos/swath.html)
- [MultiScene](https://satpy.readthedocs.io/en/stable/multiscene.html)

## Resources
- Online tool for generating boundary boxes (bbox) for AreaDefinitions: [bboxfinder.com](http://bboxfinder.com)
- Pre-defined SatPy AreaDefinitions: [area.yaml](https://github.com/pytroll/satpy/blob/main/satpy/etc/areas.yaml)

## Examples

### HYPSO-1
- See `write_composites.py`

### Sentinel-3
- [Reading OLCI data from Sentinel 3](https://nbviewer.org/github/pytroll/pytroll-examples/blob/main/satpy/OLCI%20L1B.ipynb)
    - TODO: resampling Sentinel-3 and HYPSO using same AreaDefinition