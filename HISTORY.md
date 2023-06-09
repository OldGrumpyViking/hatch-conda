# History

-----

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 09/06/2023

### Fixed
- Enter shell should now work correctly.

## [0.3.1] - 30/09/2022

### Fixed
- Fixed bug on windows where environment variables containing % failed to be passed correctly to the conda environment.

## [0.3.0] - 26/09/2022

### Added
- Environment Variables are now passed on to the conda environment.

## [0.2.0] - 12/08/2022

### Added

 - Trove classifier for hatch framework.
 - Option to use mamba.
 - Option to disable `conda-forge` index.

### Fixed

 - Fixed entry point name.
 - Unneccesary `Activate` and `Deactivate` calls removed.


## [0.1.0] - 12/08/2022

### Added

 - Conda environment type for hatch.
