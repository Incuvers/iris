# Staging Tests

![img](/doc/img/Incuvers-black.png)

Modified: 2021-04

Before performing these checks be sure to test all items in [prerelease tests](/dev/tests/prerelease.md).

The following checklist outlines all the snap staging tests that need to be validated before the snap is deployed to our clients. These tests are carried out on the iris staging client (i.e. as a snap package) pointing to api.staging.incuvers.com.

While performing these tests keep the iris logstream on cloudwatch open and verify these operations are performed correctly.

## Main Menu
 - [ ] Focus Mode
 - [ ] Phase Exposure Mode
 - [ ] GFP Exposure Mode
 - [ ] Shutdown

## Service Menu
 - [ ] Temperature/CO2/O2 Benchmarking
 - [ ] Update Firmware (subsequent tests rely on this step)
 - [ ] Update Software
 - [ ] Reset Networking
 - [ ] Factory Reset
 - [ ] Calibrate Background

## Cloud Interfacing
 - [ ] Instant Preview (in experiment form)
 - [ ] Experiment Monitoring and Capture Validation