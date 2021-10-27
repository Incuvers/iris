# Pre-Release Tests

![img](/doc/img/Incuvers-black.png)

Modified: 2021-04

Pre-release sanity checklist. These tests are carried out on the development environment built by `make dev` (i.e. as a python package). Note that some of these features differ in functionality as a snap so they will need to be retested upon being upgraded to staging. See the [staging tests](/dev/tests/staging.md).

The purpose of these set of prerelease checks is to reduce the number of broken snap builds that couldve been circumvented by a set of rudimentary functional tests saving us time waiting for snap builds and also effort in re-releasing with minor patches. <b>The only time we should have to patch a release is if a feature doesnt work specifically as a snap.</b>

While performing these tests keep the iris logstream open and verify these operations are performed correctly.

## Main Menu
 - [ ] Environment Controls (Setpoints) test bounds
 - [ ] Focus Mode **
 - [ ] Phase Exposure Mode **
 - [ ] GFP Exposure Mode **
 - [ ] System Info (verify the version string is updated)
 - [ ] Shutdown **
 - [ ] Home

## Service Menu
 - [ ] Temperature/CO2/O2 Benchmarking
 - [ ] Calibrate Background **
 - [ ] Update Firmware **
 - [ ] Update Software **
 - [ ] Reset Networking **
 - [ ] Factory Reset **

## Cloud Interfacing
 - [ ] Update Avatar
 - [ ] Update Device Name
 - [ ] Environment Controls (Setpoints) test bounds
 - [ ] Instant Preview (in experiment form) **
 - [ ] Experiment Monitoring and Capture Validation **
 - [ ] Protocol scheduling