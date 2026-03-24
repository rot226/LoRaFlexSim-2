# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

_No notable changes for now._

## [1.0.1] - 2025-09-30
### Added
- Added the "fast" execution profile for MNE3SD scripts to automatically reduce sweep sizes and apply associated presets (nodes, replicas, Class C RX intervals).
### Changed
- Traffic generators (CLI simulator, full nodes, and configuration loader) now rely on `traffic.exponential.sample_interval` to sample a strictly exponential distribution aligned with OMNeT++, and only defer transmissions when the interval remains shorter than the previous transmission duration.
- The `adr_standard_1` profile now enables a more severe degraded channel (noise, fading, and advanced capture) by default to reflect radio validation conditions.
- LoRa processing gain is no longer implicitly added to SNR calculation; it is now opt-in through the `processing_gain` parameter.
### Fixed
- Periodic Class C node windows stop polling when no downlink is pending, preventing the infinite loops observed during MNE3SD campaigns while still guaranteeing final delivery.
- MNE3SD density sweeps can force the Class C node polling interval, with a reduced value automatically applied for the "fast" profile to speed up iterations.

## [Draft]
_Brouillon conservé pour une refonte majeure envisagée mais jamais publiée._

### Added
- Complete rewrite of the LoRa network simulator in Python.
- Command-line interface and interactive dashboard.
- FastAPI REST and WebSocket API.
- Advanced propagation models with fading, mobility and obstacle support.
- LoRaWAN implementation with ADR logic, classes B and C, and AES-128 security.
- CSV export and detailed metrics.
- Unit tests with pytest and analysis scripts.

## [1.0.0] - 2025-08-26
### Added
- Initial public release of LoRaFlexSim, offering a flexible LoRa network simulator.
- Command-line interface with example scenarios.
- Documentation and basic unit tests.
