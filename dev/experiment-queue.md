# Motivations
1. Reliable design philosophy
2. Precise dispatch timing for image captures and setpoint changes
3. Separation of concerns for experiment level events and hardware scheduling algorithms (image captures and setpoint triggers)
4. Scalable options for handlers with OO approach

# Use Case (Proof of Concept Checks)
The design must be able to handle the following use cases (executed in any order):
 - User starts an experiment
 - User cancels an experiment
 - Experiment expires
 - Experiment is appended
 - Appended experiment is cancelled

# Proposed Architectural Changes
This document is a draft is open to design revisions if there are any suggestions be sure to leave a comment below.

The old `experiment_handler` package is being refactored to a `experiment` package which constitutes a multi-layered design for supporting greater separation of concerns. There are 4 primary classes which make up the package:
1. Experiment Handler
2. Scheduler
3. Imaging (inherits Scheduler)
4. Setpoint (inherits Scheduler)

Below is a high-level UML diagram to show the proposed module relations:

![UML](https://user-images.githubusercontent.com/26971036/82717739-2d61b300-9c6c-11ea-97b2-4be227ee9eb6.png)
For explanation we will use a bottom-up approach.
## Imaging and Setpoint Scheduler
At the lowest level there are 2 distinct events that occur during an experiment: _image capture_ events and _setpoint variation_ events. These events are fetched from the experiment and protocol payload `json` file containing the timing requirements for these hardware devices. In order to ensure precise timing of event dispatches according to the payload data we use a thread-safe scheduler called `threading_sched`. Schedulers require a single thread dedicated to running events placed in the schedulers queue. Currently these threads will be in an idle state if the queue is empty but in the future could have some purpose. The `Imaging` and `Setpoint` scheduler objects one key unique method:
> `trigger(args)` which dispatches the corresponding hardware events through the event scheduler.
This is the callback function for the specific scheduler type (triggering image capture callbacks for imaging and sensor callbacks for setpoint)

`Scheduler` contains the scheduler object and interfacing methods required to use a scheduler:
>`schedule_runner()` contains a daemon thread that continuously executes events in the scheduler queue.
> `purge_queue()` removes all events scheduled in the queue
> `populate()` adds the events extracted from the payload 

The scheduler objects are instantiated by the `Imaging` and `Sensor` initialization and spawn separate runner threads for separate scheduling objects. The reason for the separation is to ensure there is no collision of image capturing and setpoint change events scheduled for the same instance (or +/- the interrupt service routine callback time) causing an event to be executed late or overwritten.

## Experiment Handler
![ExperimentHandler](https://user-images.githubusercontent.com/26971036/85437652-f297b700-b558-11ea-812e-b4b212844e34.png)
The experiment handler is the top level interface for events involving the experiment start, completion and cancellation. On initialization the `ExperimentHandler` creates the `Imaging` and `Sensor` objects which register their own unique schedulers and begin looping the runners. The `ExperimentHandler` has the following methods:
>`start_experiment(payload)` set as a callback for some registered event to trigger. The call requires the payload from the user regarding the experiment information
> `end_experiment()` : listens as a callback for both `Imaging` and `Setpoint` schedulers runner methods notifying the `ExperimentHandler` that the experiment is complete.
> `cancel_experiment()` Forcibly instructs the `Imaging` and `Setpoint` schedulers to `purge_queue()`which in turn causes the runner methods to see the queue is empty triggering a similar return to the aforementioned `end_experiment()` in order to verify the successful termination of the current experiment.

Multiple Experiments can be scheduled simultaneously. Therefore we need a way to bind (tag) experiments in the scheduler so that if the user cancels an experiment happening now or in the future those specific events can be eliminated from the queue (instead of purge_queue() which removes all events)

This can be done with an unused event priority argument which can be bound to each event. The priority tag is an `int` parameter which defines the order of event operations in the case a collision occurs. Due to the separation of the `Imaging` and `Setpoint` events there should be no way collision is possible. This means this parameter is unused in this context. This allows the scheduler to identify all arguments with priority `x` to be linked to experiment id `y`. When a user requests to cancel an event they specify the event id which can then be used by the schedulers to remove target events from the queue and leave the rest untouched.

Alternatively since experiments can never overlap, we can purge all events in the queue which correspond to the intervals set by the experiment. The `ExperimentHandler` needs to be able to track these identifiers as the schedulers are running.

When a start experiment trigger is executed it should point the callback towards the `start_experiment()` method. This method will extract the payload information regarding the timing of each setpoint and capture event and dispatch the relevant information to each scheduler to compute and populate their relative event timing. Since the experiment cannot be modified at this stage (only cancelled) the projected timing parameters for each event can be computed by the respective schedulers (ie `Imaging` or `Setpoint`).  Once the schedulers are populated and return, the method then triggers the `EXPERIMENT_STARTED` event which notifies the system that the experiment is underway.

`end_experiment()` and `cancel_experiment()` work together but achieve different goals. `cancel_experiment()` is one of 2 ways to access the queue as it is running. It allows us to remove events from the queue corresponding to a cancelled experiment. `end_experiment()` is a solution to verify the successful completion of an experiment by cancellation or by time expiry processes. This method listens for a trigger from both `Imaging` and `Setpoint` indicating that the schedulers are empty corresponding to a specific experiment completion. Once both schedulers have triggered `end_experiment()` we can confirm an experiment has ended successfully and we trigger `EXPERIMENT_ENDED`.

# Requirements for Merge
 - [x] provide separation of experiment components into a set of scheduled *imaging* events and a set of *setpoint* events
 - [ ] Implement all experiment-based use cases
 - [ ] Implement dynamic Experiment queueing solution
 - [x] Implement a real-time scheduler policy for experiment components
 - [x] Diverge imaging and setpoint policies for potential post MVP separation of concerns.
 - [ ] README.md explaining the design philosophy