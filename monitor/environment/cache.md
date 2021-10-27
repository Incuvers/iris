# Caching Architecture for State Variables
Modified: 2021-05

## Navigation
1. [Payload Caching](#payload-caching)
2. [Caveats](#caveats)
3. [Request Caching](#request-caching-methodology)

## Payload Caching
The purpose of this package is to introduce a method of saving the api payloads locally so that IRIS can be more robust. There are two use cases this approach is effective at solving. 

First, in the case where IRIS boots with no cloud connectivity we can extract the last saved: experiment, protocol, imaging profile and device info and load it to resume a near identical runtime context. This means the system will maintain an almost unnoticable change in the event of a power cycle. Without this architecture, we would lose all of: experiment, protocol, imaging profile and device info.

Second, if instead, IRIS booted and connected to the cloud, we would have to still manually hit all endpoints to check to see if there are and experiments, protocols, imaging profiles and device information. This is because the shadow would not create a delta even though the IRIS system has no api information.

## Architecture
There is only a single case the cache must handle which is the set accessors. When the cache is active it will be instructed to set some payload into the cache. Whether it is instructed to to so as a result of a successful API request or the exception handle to save the default settings to the cache. The cache sequencing is performed as follows:
1. Registered set event inbound with args: `(payload:json)`
2. Save the payload as a `.json` object
3. Generate a runtime object from the payload: `(device:Device)`, `(imaging_profile: ImagingProfile)`, `(experiment:Experiment)`, `(protocol:Protocol)`
4. Dispatch event holding generated runtime object. The advantage of this approach is that the entire system is abstracted from the complex json parsing process and can use system specific getters for each object.
### Rules
 - We save our Runtime Objects in a universally accessible class for accessors and type checking.
 - We do not modify any system runtime objects unless we do so through the cache set accessor sequence.

# Trade-offs
The tradeoff is that we increase the number of disk R/W cycles but reduce the overhead of making new api requests each time the system connection is re-established. 

We want to limit R/W cycles to increase the device longevity, while also ensuring the system has a low chance of powering off during a R/W cycle risking permenant damage to the RPi. On the other hand, without a local cache, we would have to fetch all api payloads each time the device reconnects online from a boot state. This is an operation requiring a large amount of overhead and uncertainity with web calls.

Due to the projected number of FETCH events from the api, we anticipate a minute number of R/W cycles neccesary to satisfy the architecture requirements.

