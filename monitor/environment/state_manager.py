# -*- coding: utf-8 -*-
"""
State Manager
=============
Modified: 2021-05

Dependancies
------------
```
import logging
import asyncio
from typing import Any, Coroutine, Optional, Type, TypeVar, Callable, List, Union

from monitor.models.icb import ICB
from monitor.models.device import Device
from monitor.models.protocol import Protocol
from monitor.models.experiment import Experiment
from monitor.models.imaging_profile import ImagingProfile
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import copy
import logging
import asyncio
import traceback
from typing import Any, Coroutine, Dict, Generic, Tuple, Type, TypeVar, Callable, List, Union

from monitor.models.icb import ICB
from monitor.models.device import Device
from monitor.models.protocol import Protocol
from monitor.models.experiment import Experiment
from monitor.models.imaging_profile import ImagingProfile
from monitor.environment.registry import CallbackRegistry as cr
from monitor.environment.registry import StateRegistry as sr
from monitor.sys.helpers import clear_thumbnail, write_lab_id, read_lab_id

StateModel = Union[ICB, Experiment, Device, Protocol, ImagingProfile]

# generic runtime model type
_S = TypeVar('_S', bound=StateModel)


class PropertyCondition(Generic[_S]):

    def __init__(self, trigger: Callable[[_S, _S], bool], callback: Callable[[_S], Coroutine[Any, Any, None]],
                 callback_on_init=False) -> None:
        self.trigger = trigger
        self.callback = callback
        self.callback_on_init = callback_on_init

    @property
    def trigger(self) -> Callable[[_S, _S], bool]:
        return self.__trigger

    @trigger.setter
    def trigger(self, trigger: Callable[[_S, _S], bool]):
        self.__trigger = trigger

    @property
    def callback(self) -> Callable[[_S], Coroutine[Any, Any, None]]:
        return self.__callback

    @callback.setter
    def callback(self, callback: Callable[[_S], Coroutine[Any, Any, None]]):
        self.__callback = callback

    @property
    def callback_on_init(self) -> bool:
        return self.__callback_on_init

    @callback_on_init.setter
    def callback_on_init(self, value: bool):
        self.__callback_on_init = value


class StateManager:

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def device(self) -> Device:
        """
        Get device runtime model

        :return: device runtime model
        :rtype: Device
        """
        return copy.deepcopy(sr.device)

    @device.setter
    def device(self, device: Device) -> None:
        """
        Set device runtime model

        :param device: device runtime model
        :type device: Device
        """
        sr.device.deserialize(**device.__dict__)

    @property
    def imaging_profile(self) -> ImagingProfile:
        """
        Get imaging profile runtime model

        :return: imaging profile runtime model
        :rtype: ImagingProfile
        """
        return copy.deepcopy(sr.imaging_profile)

    @imaging_profile.setter
    def imaging_profile(self, imaging_profile: ImagingProfile) -> None:
        """
        Set imaging profile runtime model

        :param imaging_profile: imaging profile runtime model
        :type imaging_profile: ImagingProfile
        """
        sr.imaging_profile.deserialize(**imaging_profile.__dict__)

    @property
    def protocol(self) -> Protocol:
        """
        Get protocol runtime model

        :return: protocol runtime model
        :rtype: Protocol
        """
        return copy.deepcopy(sr.protocol)

    @protocol.setter
    def protocol(self, protocol: Protocol) -> None:
        """
        Set protocol runtime model

        :param protocol: protocol runtime model
        :type protocol: Protocol
        """
        sr.protocol.deserialize(**protocol.__dict__)

    @property
    def experiment(self) -> Experiment:
        """
        Get experiment runtime model

        :return: experiment runtime model
        :rtype: Experiment
        """
        return copy.deepcopy(sr.experiment)

    @experiment.setter
    def experiment(self, experiment: Experiment) -> None:
        """
        Set experiment runtime model

        :param experiment: experiment runtime model
        :type experiment: Experiment
        """
        sr.experiment.deserialize(**experiment.__dict__)

    @property
    def icb(self) -> ICB:
        """
        Get icb runtime model

        :return: icb runtime model
        :rtype: ICB
        """
        return copy.deepcopy(sr.icb)

    @icb.setter
    def icb(self, icb: ICB) -> None:
        """
        Set icb runtime model

        :param icb: icb runtime model
        :type icb: ICB
        """
        sr.icb.deserialize(**icb.serialize())

    def _load_runtime_models(self) -> None:
        """
        Load in runtime models from cache
        """
        # read state vars from cache
        self.protocol.load()
        self.device.load()
        self.experiment.load()
        self.imaging_profile.load()
        # commit device cache to system
        self.commit(self.device, initial=True, cache=False)
        # conditionally commit optional states based on initialization state
        self.commit(self.protocol, initial=True, cache=False)
        self.commit(self.experiment, initial=True, cache=False)
        self.commit(self.imaging_profile, initial=True, cache=False)

    def commit(self, state: StateModel, initial: bool = False, source: bool = False, cache: bool = True) -> bool:
        """
        Commiting a state variable change requires up to 3 steps:
          1. Independant system validation (for external system state changes)
          2. Update state variable in runtime layer (here)
          3. Notify subscribers of state change

        :param state: proposed state variable change
        :type state: StateModel
        :param initial: flag indicating this is the initial commit for this runtime model. This acts as
                        an override for the model initialization check
        :type initial: bool
        :param source: flag indicating the source module is pushing these changes (do not call validator)
        :type source: bool
        :param cache: flag which indicates the commit should update the system cache, defaults to True
        :type cache: bool, optional
        :return: commit status
        :rtype: bool
        """
        if initial:
            self._logger.info("Initial model commit for %s", state)
        # filter by runtime model
        if isinstance(state, ImagingProfile):
            # await validators if state change is not from source
            if not source:
                try:
                    self._isv_runner(state, cr.ip_isv)
                except RuntimeError as exc:
                    self._logger.warning("State change validation failed: %s", exc)
                    return False
            # cache old model
            cached = copy.deepcopy(self.imaging_profile)
            # await update state
            self.imaging_profile = state
            # async update subscribers
            self._resolve_subscriptions(initial, cr.ip, cr.ip_properties, cached, state)
        elif isinstance(state, ICB):
            # await validators
            if not source:
                try:
                    self._isv_runner(state, cr.icb_isv)
                except RuntimeError as exc:
                    self._logger.warning("State change validation failed: %s", exc)
                    return False
            # cache old model
            cached = copy.deepcopy(self.icb)
            # await update state
            self.icb = state
            # async update subscribers
            self._resolve_subscriptions(initial, cr.icb, cr.icb_properties, cached, state)
        elif isinstance(state, Experiment):
            # clear thumbnail for new inbound experiments
            clear_thumbnail()
            # cache old model
            cached = copy.deepcopy(self.experiment)
            # await update state
            self.experiment = state
            # async update subscribers
            self._resolve_subscriptions(initial, cr.experiment,
                                        cr.experiment_properties, cached, state)
        elif isinstance(state, Protocol):
            # cache old model
            cached = copy.deepcopy(self.protocol)
            # await update state
            self.protocol = state
            # async update subscribers
            self._resolve_subscriptions(initial, cr.protocol, cr.protocol_properties, cached, state)
        elif isinstance(state, Device):
            # cache old model
            cached = copy.deepcopy(self.device)
            # await update state
            self.device = state
            # update lab_id if delta
            if state.lab_id != read_lab_id():
                write_lab_id(state.lab_id)
            # async update subscribers
            self._resolve_subscriptions(initial, cr.device, cr.device_properties, cached, state)
        # write all state variables to cache for all runtime
        # models (ICB exempt) if cache flag is set.
        if cache and not isinstance(state, ICB): state.cache()
        self._logger.info("State change commit for %s successful", state)
        return True

    def _resolve_subscriptions(self, initial: bool, state_registry: List[Callable[[_S], Coroutine[Any, Any, None]]],
                               state_properties: Dict[Callable[[_S], Coroutine[Any, Any, None]],
                                                      List[Tuple[Callable[[_S, _S], bool], bool]]],
                               cached: _S, state: _S) -> None:
        """
        State and property level subscription resolver

        :param initial: initial state commit flag
        :type initial: bool
        :param state_registry: state model subscription registry
        :type state_registry: List[Callable[[_S], Coroutine[Any, Any, None]]]
        :param state_properties: state property subscription registry
        :type state_properties: Dict[Callable[[_S], Coroutine[Any, Any, None]], 
                                List[Tuple[Callable[[_S, _S], bool], bool]]]
        :param cached: previous state model
        :type cached: _S
        :param state: active state model
        :type state: _S
        """
        if state_registry:
            asyncio.run(self._subscriber_runner(state, state_registry))
        prop_callbacks: List[Callable[[_S], Coroutine[Any, Any, None]]] = []
        for callback, trigger_list in state_properties.items():
            # if any triggers are true then the callback is appended to the callback list
            for trigger, callback_on_init in trigger_list:
                if initial and callback_on_init:
                    self._logger.debug(
                        "First commit for model %s, and callback_on_init is set.\
                        Appending %s to property subscription callbacks", cached, callback)
                    prop_callbacks.append(callback)
                elif trigger(cached, state):
                    self._logger.debug(
                        "Trigger condition met.  Appending %s property subscription", callback)
                    prop_callbacks.append(callback)
                    break
        if prop_callbacks:
            asyncio.run(self._subscriber_runner(state, prop_callbacks))

    def subscribe(self, state_type: Type[_S],
                  callback: Callable[[_S], Coroutine[Any, Any, None]]) -> None:
        """
        Subscribe an asynchronous state change listener to a designated runtime model

        :param state_type: runtime type to subscribe to
        :type state_type: Type[T]
        :param callback: state change listener callback
        :type callback: Callable[[T], Coroutine[Any, Any, None]]
        """
        if state_type is ImagingProfile: cr.ip.append(callback)
        elif state_type is Device: cr.device.append(callback)
        elif state_type is Protocol: cr.protocol.append(callback)
        elif state_type is Experiment: cr.experiment.append(callback)
        elif state_type is ICB: cr.icb.append(callback)

    def subscribe_property(self, _type: Type[_S], _property: PropertyCondition[_S]) -> None:
        """
        Subscribe an asynchronous state change listener to a designated runtime model property

        :param _property: property to subscribe to
        :type _property: str
        :param callback: state change listener callback
        :type callback: Callable[[_S], Coroutine[Any, Any, None]]
        :raises RuntimeError: if the requested property does not exist in the provided state
        """
        # TODO: It would be nice to derive the Generic type from the property condition however this
        # is currently unsupported as o python 3.8
        if _type is ImagingProfile: prop_callbacks = cr.ip_properties
        elif _type is Device: prop_callbacks = cr.device_properties
        elif _type is Protocol: prop_callbacks = cr.protocol_properties
        elif _type is Experiment: prop_callbacks = cr.experiment_properties
        else: prop_callbacks = cr.icb_properties
        if _property.callback in prop_callbacks.keys():
            prop_callbacks[_property.callback].append(
                (_property.trigger, _property.callback_on_init))
        else:
            prop_callbacks[_property.callback] = [(_property.trigger, _property.callback_on_init)]

    def subscribe_isv(self, state_type: Type[_S], callback: Callable[[_S], bool]) -> None:
        """
        Subscribe a synchronous state change validator to a designated runtime model

        :param state_type: isv subscription to state variable of type state_type
        :type state_type: Type[_S]
        :param callback: independant system validator function
        :type callback: Callable[[_S], bool]
        """
        # only a single isv for each type can exist simultaneously so overwrite if one exists
        if state_type is ImagingProfile:
            if len(cr.ip_isv) == 0: cr.ip_isv.append(callback)
            else: cr.ip_isv[0] = callback
        elif state_type is ICB:
            if len(cr.icb_isv) == 0: cr.icb_isv.append(callback)
            else: cr.icb_isv[0] = callback

    def _isv_runner(self, state_var: _S, registry: List[Callable[[_S], bool]]) -> None:
        """
        Synchrounous runner for independant system validator callbacks. If the validator
        fails, raise a runtime error

        :param state_var: proposed runtime model for independant system validation
        :type state_var: T
        :param registry: list of isv callbacks
        :type registry: List[Callable[[T], bool]]
        :raises RuntimeError: if a validator callback encounters an exception
                             or if the validator returns False
        """
        # skip if registry is empty
        if len(registry) == 0: return None
        # iterate through validators checking for pass
        validator = registry[0]
        try:
            result = validator(state_var)
        except BaseException as exc:
            self._logger.exception(
                "An exception was encountered during %s isv call: %s", state_var, exc)
            raise RuntimeError
        if not result: raise RuntimeError

    async def _subscriber_runner(self, state_var: _S,
                                 registry: List[Callable[[_S], Coroutine[Any, Any, None]]]) -> None:
        """
        Async runner that executes all subscriber coroutines with new runtime model state changes.

        :param state_var: pre-validated runtime model to pass to subscribers
        :type state_var: T
        :param registry: list of subscriber coroutines
        :type registry: List[Callable[[T], Awaitable[None]]]
        """
        # construct coroutine lists
        tasks = [subscriber(state_var) for subscriber in registry]
        # return results from coroutines with exceptions if any
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # reformat tasks to display only the name
        operations = tuple(zip(map(lambda x: x.__qualname__, tasks), results))
        self._logger.debug("%s Subscriber operations: %s", type(state_var).__name__, operations)
        # filter by operations which yielded an exception
        exceptions: List[Tuple[str, Exception]] = list(
            filter(lambda x: x[1] is not None, operations))
        for func, exc in exceptions:
            self._logger.exception("Subscriber function: %s encountered an exception: %s", func,
                                   "".join(traceback.format_exception(
                                       etype=type(exc), value=exc, tb=exc.__traceback__
                                   )))
