# -*- coding: utf-8 -*-
"""
ICB Model
=========
Modified: 2021-05
Model object for Incuvers Control Board sensorframe
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

from typing import Any, Dict, Tuple, Union
from datetime import datetime, timezone
from uuid import uuid4
from enum import IntEnum
from monitor.logs.formatter import pformat
from monitor.models.state import StateModel

Sensorframe = Dict[str, Union[str, float, int]]


class SensorMode(IntEnum):
    """
    0: off
    1: read-only
    2: active
    """
    OFF = 0
    READ = 1
    ACTIVE = 2


class ICB(StateModel):
    """
    This model is initialized to a default state but populated after sensorframe state is modified
    """
    FILENAME = 'telemetry.json'
    # resolution of float values stored in this model
    STORAGE_RESOLUTION = 1
    CONVERSION_RESOLUTION = 2                                       # resolution of int/float conversions
    OPERATING_TEMPERATURE: Tuple[float, float] = (-40.0, 100.0)     # Reasonable operating temp
    OP_RANGE: Tuple[float, float] = (0.1, 21.0)                     # O2 min, max setpoint
    CP_RANGE: Tuple[float, float] = (0.1, 21.0)                     # CO2 min, max setpoint
    TP_RANGE: Tuple[float, float] = (25.0, 40.0)                    # Temperature min, max setpoint
    TP_DEFAULT: float = 37.5                                        # Default temperature setpoint
    OP_DEFAULT: float = 20.9                                        # Default o2 setpoint
    CP_DEFAULT: float = 5.0                                         # Default co2 setpoint
    FP_DEFAULT: int = 20                                            # Default fan speed duty
    HP_DEFAULT: int = 10                                            # Default heater duty

    def __init__(self) -> None:
        super().__init__(
            _id='',
            filename=self.FILENAME
        )
        # set creation timestamp
        self.initialized = False

    def __repr__(self) -> str:
        return "ICB: {}".format(pformat(self.serialize()))

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize object into json compatible dict
        :return: object attributes and values
        :rtype: Dict[str, Any]
        """
        return {
            'id': self.id,
            'tc': self.tc,
            'cc': self.cc,
            'oc': self.oc,
            'rh': self.rh,
            'tp': self.tp,
            'cp': self.cp,
            'op': self.op,
            'to': self.to,
            'ct': self.ct,
            'ctr': self.ctr,
            'tm': self.tm,
            'fp': self.fp,
            'fc': self.fc,
            'hp': self.hp,
            'hc': self.hc,
            'cm': self.cm,
            'om': self.om,
            'iv': self.iv,
            'timestamp': self.timestamp,
        }

    def deserialize(self, **payload: Sensorframe) -> None:
        """
        Perform iterative property set 
        """
        # override local id value
        for k, v in payload.items():
            setattr(self, k, v)
        self.initialized = True

    @property
    def tc(self) -> float:
        """
        Get current temperature (°C) @ storage resolution
        :return: temperature in °C
        :rtype: float
        """
        return self.__tc

    @tc.setter
    def tc(self, value: float) -> None:
        """
        Set current temperature (°C) @ storage resolution
        :param value: temperature in °C
        :type value: float
        """
        candidate = round(value, self.STORAGE_RESOLUTION)
        # Check if candidate is within the valid range
        if self.OPERATING_TEMPERATURE[0] > candidate or candidate > self.OPERATING_TEMPERATURE[1]:
            self._logger.error("Validation check failed for property TC setter with %s", candidate)
            return
        self.__tc = candidate

    @property
    def rh(self) -> float:
        """
        Get current relative humidity concentration (%) @ storage resolution
        :return: current relative humidity concentration in %
        :rtype: float
        """
        return self.__rh

    @rh.setter
    def rh(self, value: float) -> None:
        """
        Set current relative humidity concentration (%) @ storage resolution
        :param value: current relative humidity concentration in %
        :type value: float
        """
        candidate = round(value, self.STORAGE_RESOLUTION)
        # range validation
        if 0.0 > candidate or candidate > 100.0:
            self._logger.error("Validation check failed for property RH setter with %s", candidate)
            return
        self.__rh = candidate

    @property
    def oc(self) -> float:
        """
        Set current o2 concentration (%) @ storage resolution
        :return: current o2 concentration in %
        :rtype: float
        """
        return self.__oc

    @oc.setter
    def oc(self, value: float) -> None:
        """
        Set current o2 concentration (%) @ storage resolution
        :param value: current o2 concentration in %
        :type value: float
        """
        candidate = round(value, self.STORAGE_RESOLUTION)
        # range validation
        if 0.0 > candidate or candidate > 100.0:
            self._logger.error("Validation check failed for property OC setter with %s", candidate)
            return
        self.__oc = candidate

    @property
    def cc(self) -> float:
        """
        Get current co2 concentration (%) @ storage resolution
        :return: co2 concentration in %
        :rtype: float
        """
        return self.__cc

    @cc.setter
    def cc(self, value: float) -> None:
        """
        Set current co2 concentration (%) @ storage resolution
        :param value: co2 concentration in %
        :type value: float
        """
        candidate = round(value, self.STORAGE_RESOLUTION)
        # range validation
        if 0.0 > candidate or candidate > 100.0:
            self._logger.error("Validation check failed for property CC setter with %s", candidate)
            return
        self.__cc = candidate

    @property
    def tp(self) -> float:
        """
        Get temperature setpoint (°C) @ storage resolution
        :return: temperature setpoint in °C
        :rtype: float
        """
        return self.__tp

    @tp.setter
    def tp(self, value: float) -> None:
        """
        Set temperature setpoint (°C) @ storage resolution
        :param value: temperature setpoint in °C
        :type value: float
        """
        candidate = round(value, self.STORAGE_RESOLUTION)
        # range validation
        if self.TP_RANGE[0] > candidate or candidate > self.TP_RANGE[1]:
            self._logger.error("Validation check failed for property TP setter with %s", candidate)
            return
        self.__tp = candidate

    @property
    def to(self) -> float:
        """
        Get temperature offset (°C) @ storage resolution
        :return: temperature offset in °C
        :rtype: float
        """
        return self.__to

    @to.setter
    def to(self, value: float) -> None:
        """
        Set temperature offset (°C) @ storage resolution
        :param value: temperature offset in °C
        :type value: float
        """
        candidate = round(value, self.STORAGE_RESOLUTION)
        self.__to = candidate

    @property
    def cp(self) -> float:
        """
        Get CO2 concentration setpoint (%) @ storage resolution
        :return: CO2 concentration setpoint as %
        :rtype: float
        """
        return self.__cp

    @cp.setter
    def cp(self, value: float) -> None:
        """
        Set CO2 concentration setpoint (%) @ storage resolution
        :param value: CO2 concentration setpoint in %
        :type value: float
        """
        candidate = round(value, self.STORAGE_RESOLUTION)
        # range validation
        if self.CP_RANGE[0] > candidate or candidate > self.CP_RANGE[1]:
            self._logger.error("Validation check failed for property CP setter with %s", candidate)
            return
        self.__cp = candidate

    @property
    def op(self) -> float:
        """
        Get O2 setpoint concentration (%) @ storage resolution
        :return: O2 concentration setpoint as %
        :rtype: float
        """
        return self.__op

    @op.setter
    def op(self, value: float) -> None:
        """
        Set O2 setpoint concentration in (%) @ storage resolution
        :param value: O2 concentration setpoint as %
        :type value: float
        """
        candidate = round(value, self.STORAGE_RESOLUTION)
        # range validation
        if self.OP_RANGE[0] > candidate or candidate > self.OP_RANGE[1]:
            self._logger.error("Validation check failed for property OP setter with %s", candidate)
            return
        self.__op = candidate

    @property
    def hp(self) -> int:
        """
        Get heater duty cycle (%)
        :return: heater duty cycle in percent
        :rtype: int
        """
        return self.__hp

    @hp.setter
    def hp(self, hp: int) -> None:
        """
        Set heater duty cycle (%)
        :param hp: heater duty cycle in percent
        :type hp: int
        """
        if 0 > hp or hp > 100:
            self._logger.error("Validation check failed for property HP setter with %s", hp)
            return
        self.__hp = hp

    @property
    def hc(self) -> bool:
        """
        Get heater status
        :return: heater status
        :rtype: bool
        """
        return self.__hc

    @hc.setter
    def hc(self, hc: bool) -> None:
        """
        Set heater status
        :param hc: heater status
        :type hc: bool
        """
        self.__hc = hc

    @property
    def fp(self) -> int:
        """
        Get fan duty cycle (%)
        :return: fan duty cycle in percent
        :rtype: int
        """
        return self.__fp

    @fp.setter
    def fp(self, fp: int) -> None:
        """
        Set fan duty cycle (%)
        :param fp: fan duty cycle in %
        :type fp: int
        """
        if 0 > fp or fp > 100:
            self._logger.error("Validation check failed for property FP setter with %s", fp)
            return

        self.__fp = fp

    @property
    def fc(self) -> int:
        """
        Get current fan speed (rpm)
        :return: current fan speed in rpm
        :rtype: float
        """
        return self.__fc

    @fc.setter
    def fc(self, fc: int) -> None:
        """
        Set current fan speed (rpm)
        :param fc: current fan speed in rpm
        :type fc: int
        """
        if 0 > fc:
            self._logger.error("Validation check - FC setter less than bound %s", fc)
            return
        self.__fc = fc

    @property
    def ctr(self) -> float:
        """
        Get current COZIR temperature reading (°C)
        :return: COZIR temperature reading in °C
        :rtype: float
        """
        return self.__ctr

    @ctr.setter
    def ctr(self, ctr: float) -> None:
        """
        Set current COZIR temperature reading (°C)
        :param ctr: COZIR temperature reading (°C)
        :type ctr: float
        """
        candidate = round(ctr, 1)
        if self.OPERATING_TEMPERATURE[0] > candidate or candidate > self.OPERATING_TEMPERATURE[1]:
            self._logger.error("Validation check failed for property CTR setter with %s", candidate)
            return
        self.__ctr = ctr

    @property
    def tm(self) -> SensorMode:
        """
        Get temperature controller mode (0 -> off 1 -> read-only 2 -> active)
        :return: temperature controller mode (0 -> off 1 -> read-only 2 -> active)
        :rtype: SensorMode
        """
        return self.__tm

    @tm.setter
    def tm(self, tm: SensorMode) -> None:
        """
        Set temperature controller mode (0 -> off 1 -> read-only 2 -> active)
        :param tm: temperature controller mode (0 -> off 1 -> read-only 2 -> active)
        :type tm: SensorMode
        """
        self.__tm = tm

    @property
    def cm(self) -> SensorMode:
        """
        Get CO2 controller mode (0 -> off 1 -> read-only 2 -> active)
        :return: CO2 controller mode (0 -> off 1 -> read-only 2 -> active)
        :rtype: SensorMode
        """
        return self.__cm

    @cm.setter
    def cm(self, cm: SensorMode) -> None:
        """
        Set CO2 controller mode (0 -> off 1 -> read-only 2 -> active)
        :param cm: CO2 controller mode (0 -> off 1 -> read-only 2 -> active)
        :type cm: int
        """
        self.__cm = cm

    @property
    def om(self) -> SensorMode:
        """
        Get O2 controller mode (0 -> off 1 -> read-only 2 -> active)
        :return: o2 controller mode
        :rtype: SensorMode
        """
        return self.__om

    @om.setter
    def om(self, om: SensorMode) -> None:
        """
        Set O2 controller mode (0 -> off 1 -> read-only 2 -> active)
        :param om: 0 -> off 1 -> read-only 2 -> active
        :type om: SensorMode
        """
        self.__om = om

    @property
    def iv(self) -> str:
        """
        Get icb version string
        :return: icb git sha
        :rtype: str
        """
        return self.__iv

    @iv.setter
    def iv(self, version: str) -> None:
        """
        Set icb version string
        :param version: icb git sha
        :type version: str
        """
        self.__iv = version

    @property
    def timestamp(self) -> str:
        """
        Get timestamp of sensorframe reading as an ISO string
        :return: timestamp of previous sensorframe reading in iso format
        :rtype: str
        """
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, timestamp: str) -> None:
        """
        Set timestamp of sensorframe reading as an ISO string
        :param timestamp: timestamp of sensorframe reading in iso format
        :type timestamp: str
        """
        self.__timestamp = timestamp

    @property
    def ct(self) -> str:
        """
        Get last co2 sensor calibration time as ISO timestamp
        """
        return self.__ct

    @ct.setter
    def ct(self, ct: str) -> None:
        """
        Set co2 calibration time in iso format (UTC)
        :param ct: calibration time in utc iso format
        :type ct: str
        """
        self.__ct = ct

    def int_to_float(self, val: int) -> float:
        """
        Convert int setpoint @ conversion resolution to iris compatible float
        :param val: input integer value
        :type val: int
        :return: output float value
        :rtype: float
        """
        return val / (10 ** self.CONVERSION_RESOLUTION)

    def float_to_int(self, val: float) -> int:
        """
        Convert float setpoint @ conversion resolution to icb compatible integer
        :param val: input float value
        :type val: float
        :return: output integer value
        :rtype: int
        """
        return int(val * (10 ** self.CONVERSION_RESOLUTION))

    @staticmethod
    def calibration_time_to_iso(ct: int) -> str:
        """
        Convert 12hr. unit timestamp to iso datetime format in utc
        :param ct: 12hr. units
        :type ct: int
        :return: iso datetime
        :rtype: str
        """
        return datetime.fromtimestamp(ct * 12 * 60 * 60).isoformat()

    @staticmethod
    def generate_co2_calibration_time() -> int:
        """
        Generate a co2 calibration timestamp in 12hr. units
        :return: calibration timestamp in 12hr. units
        :rtype: int
        """
        return int(datetime.now(timezone.utc).timestamp() / 60 / 60 / 12)

    @staticmethod
    def generate_id() -> str:
        """
        Generate uuid for this instance
        :return: [description]
        :rtype: str
        """
        return uuid4().hex
