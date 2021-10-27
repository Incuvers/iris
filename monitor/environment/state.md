# State Management
Modified: 2021-05

## Functional Requirements
 - Store singleton copies of monitor runtime variables
 - Execute subscriber functions on state changes
   - removes need for large event pipelines for state change updates
 - Perform state validation checks
   - against preconditions (internally in the models)
   - against firmware (TCAM and arduino)
 - Facilitate automated system caching on state changes
 - Facilitate runtime model population from cached models
 - Fully permissive -> any module can access and subscribe to state change events
 - Clean syntactic api
 - thread-safe

## Runtime Models
1. Device -> store device information
2. Experiment -> store experiment timing, linked imaging profile and protocol
3. Protocols -> store protocol timing and setpoint details
4. Sensorframe -> store current sensorframe properties
5. ImagingProfile -> stores mircoscope and lighting properties

## Examples
```py
# setting imaging profile dpc exposure
with StateManager() as state:
    ip = state.checkout_imaging_profile()
    ip.set_dpc_exposure(45)
    state.commit(ip)
```
```py
# getting protocol setpoints 
with StateManager() as state:
    protocol = state.checkout_protocol()
    setpoints = protocol.get_setpoints()
```

In order to make the state manager thread  safe and guard against saving potentially invalid states I will divide the module-state interaction as a two layer process:
1. Runtime Layer - Holds the system runtime models as they represent the current state
2. Checkout Layer - Generates copies of runtime models to distribute externally for modification

## State Transactions
### Checkout
An external module makes a request to the state manager to *checkout* a current runtime model. The state manager accesses the runtime layer and generates a copy of the requested model and forwards it to the external module. The module can make any changes it wants to that module copy and it will not affect the system state. This is desired because the state changes must be validated by the state manager before the state is modified (this includes sending state changes to the firmware to ensure they are accepted since these are independant systems). Remember if a bad state change is saved into the runtime layer, another async request has the potential to read a bad state.
### Configuration
The checked-out copy of the runtime model can then be configured and potentially even malformed with no affect to the state. If something goes wrong during the checkout the copy will simply be dereferenced by the stack as a local variable. The runtime model will have a set of preconditions to validate all setter attributes.
### Commit
Once the desired state changes have been made we can commit our modified copy to the system for state-level validation. The state manager will first apply our modified model to the firmware and try to see if the values are accepted. If the changes are accepted it will immediately update the runtime model and perform callbacks on all registered subscribers to that models state changes. Some models such as `Device` and `Experiment` models may not require any additional validation that extends the preconditions in which case commit will simply skip the firmware validation phase. Once all subscribers are updated with the change the cache is written with the new runtime model state.

## Components
### Independant System Validators (ISVs) 
ISVs describe the firmware transactions that validates whether or not an independant system (TCAM or arduino) has accepted a change. ISVs are not mandated for all runtime models but are critical for use where independant systems are involved. Note that ISVs are generally far slower to execute than native validation, as a result it should be used in regulation.

### Subscribers
Callback executed sequentially when the state manager validates the state change. Any module can subscribe to any runtime model state change. The subscriber functions will have the following schema:
```py
def subscriber(self, model: Union[ImagingProfile, Protocol, Sensorframe, Experiment, Device]) -> None:
```

State subscriptions should be done in module constructors similar to event handler registration:
```py
def __init__(self):
    with StateManager() as state:
        state.subscribe('ImagingProfile', self.report_imaging_shadow)
        state.subscribe('Sensorframe', self.telemetry)

def report_imaging_shadow(self, ip:ImagingProfile) -> None:
    """
    Update some module component with new imaging profile.
    """
    self.report_to_shadow(ip.get_dpc_brightness())

def telemetry(self):
    with StateManager() as state:
        sensorframe = state.checkout_sensorframe()
        ...

```
### Registry
```py
registry {
    ImagingProfile: {
        Microscope.set_exposure                 <ISV>
        CloudController.report_mqtt_imaging     <SUBSCRIBER>
        UI.exposure_stream.set_value            <SUBSCRIBER>
    },
    Device: {
        ...
    }
}
```
## Use Cases
### Setting Exposure on IRIS
1. User opens exposure stream
2. exposure stream plays (already has the latest changes since it is an ISV)
3. user rotates the knob
4. the exposure stream checks out the active imaging profile
5. applies the modification requested to the checkout model
6. checkout model is passed to runtime layer via `state.commit`
7. state applies ISV to microscope
8. state updates runtime model
9. state updates all subscribers of state change -> no module state updates ('IMAGING_PROFILE')
10. state writes new runtime model to cache

Step 3-10 is a significant number of steps with a number of async calls and disk write cycles. The user can rotate the knob fairly rapidly causing this to be an extremely intensive process. To alleviate the write cycles an optional kwarg `no_cache` can be supported for `state.commit` to indicate to the state manager not to cache these commits. The affect this will have is that if the system is turned off during this time the change will not be saved. Which is completely expected behaviour from a user perspective. When the user selects *confirm* however we should udpate the cache to reflect that state change. Here we should provide another mechanism to tell the state to just write the current runtime model to cache without any state changes.


## Property Subscription

```py
{
    'property': 'cancelled',
    'trigger': lambda cached, candidate : candidate.cancelled is True,
    'callback': <function>
}
# {
#     'property': 'cancelled',
#     'trigger': lambda cached, candidate: cached.cancelled != candidate.cancelled,
#     'callback': <function>
# }
# {
#     'property': 'dpc_inner_radius',
#     'trigger': lambda cached, candidate: cached.dpc_inner_radius != candidate.dpc_inner_radius,
#     'callback': <function>
# }
# {
#     'property': 'dpc_outer_radius',
#     'trigger': lambda cached, candidate: cached.dpc_outer_radius != candidate.dpc_outer_radius,
#     'callback': <function>
# }
###############

{
    <function>: [
       lambda cached, candidate: cached.dpc_outer_radius != candidate.dpc_outer_radius,
       lambda cached, candidate: cached.dpc_inner_radius != candidate.dpc_inner_radius, 
    ],
    <function>: [
       lambda cached, candidate: cached.cancelled != candidate.cancelled,
       lambda cached, candidate: cached.cancelled != candidate.cancelled, 
    ], 
}
```