#!/usr/bin/env python
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

from typing import Any, Dict, Tuple
from datetime import datetime, timezone
from uuid import uuid4
from monitor.logs.formatter import pformat
from monitor.models.state import StateModel

class ICB(StateModel):
    """
    This model is initialized to a default state but populated after sensorframe state is modified
    """
    STORAGE_RESOLUTION = 1                                          # resolution of float values stored in this model
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
            filename='icb.json'
        )
        self._tc_set = False
        self._rh_set = False
        self._oc_set = False
        self._cc_set = False
        self._tp_set = False
        self._to_set = False
        self._cp_set = False
        self._op_set = False
        self._hp_set = False
        self._fp_set = False
        self._fc_set = False
        self._ctr_set = False
        self._tm_set = False
        self._cm_set = False
        self._om_set = False
        self._iv_set = False
        self._ct_set = False
        self._timestamp_set = False

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
            'TC': self.tc,
            'CC': self.cc,
            'OC': self.oc,
            'RH': self.rh,
            'TP': self.tp,
            'CP': self.cp,
            'OP': self.op,
            'TO': self.to,
            'CT': self.ct,
            'CTR': self.ctr,
            'TM': self.tm,
            'FP': self.fp,
            'FC': self.fc,
            'HP': self.hp,
            'CM': self.cm,
            'OM': self.om,
            'IV': self.iv,
            'timestamp': self.timestamp,
        }

    def deserialize(self, **kwargs) -> None:
        """
        Iteratively set object properties
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def initialized(self) -> bool:
        """
        Check if all properties have been initialized successfully

        :return: sensorframe init status
        :rtype: bool
        """
        return all(
            [
                self._tc_set,
                self._rh_set,
                self._oc_set,
                self._cc_set,
                self._tp_set,
                self._to_set,
                self._cp_set,
                self._op_set,
                self._hp_set,
                self._fp_set,
                self._fc_set,
                self._ctr_set,
                self._tm_set,
                self._cm_set,
                self._om_set,
                self._iv_set,
                self._ct_set,
                self._timestamp_set,
            ]
        )

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
        # range validation
        if self.OPERATING_TEMPERATURE[0] <= candidate <= self.OPERATING_TEMPERATURE[1]:
            self.__tc = candidate
            self._tc_set = True

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
        if 0.0 <= candidate <= 100.0:
            self.__rh = candidate
            self._rh_set = True

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
        if 0.0 <= candidate <= 100.0:
            self.__oc = candidate
            self._oc_set = True

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
        if 0.0 <= candidate <= 100.0:
            self.__cc = candidate
            self._cc_set = True

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
        if self.TP_RANGE[0] <= candidate <= self.TP_RANGE[1]:
            self.__tp = candidate
            self._tp_set = True

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
        self._to_set = True

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
        if self.CP_RANGE[0] <= candidate <= self.CP_RANGE[1]:
            self.__cp = candidate
            self._cp_set = True

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
        if self.OP_RANGE[0] <= candidate <= self.OP_RANGE[1]:
            self.__op = candidate
            self._op_set = True

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
        if 0 <= hp <= 100:
            self.__hp = hp
            self._hp_set = True

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
        if 0 <= fp <= 100:
            self.__fp = fp
            self._fp_set = True

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
        if 0 <= fc:
            self.__fc = fc
            self._fc_set = True

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
        if self.OPERATING_TEMPERATURE[0] <= candidate <= self.OPERATING_TEMPERATURE[1]:
            self.__ctr = ctr
            self._ctr_set = True

    @property
    def tm(self) -> int:
        """
        Get temperature controller mode (0 -> off 1 -> read-only 2 -> active)

        :return: temperature controller mode (0 -> off 1 -> read-only 2 -> active)
        :rtype: int
        """
        return self.__tm

    @tm.setter
    def tm(self, tm: int) -> None:
        """
        Set temperature controller mode (0 -> off 1 -> read-only 2 -> active)

        :param tm: temperature controller mode (0 -> off 1 -> read-only 2 -> active)
        :type tm: int
        """
        if tm in [0, 1, 2]:
            self.__tm = tm
            self._tm_set = True

    @property
    def cm(self) -> int:
        """
        Get CO2 controller mode (0 -> off 1 -> read-only 2 -> active)

        :return: CO2 controller mode (0 -> off 1 -> read-only 2 -> active)
        :rtype: int
        """
        return self.__cm

    @cm.setter
    def cm(self, cm: int) -> None:
        """
        Set CO2 controller mode (0 -> off 1 -> read-only 2 -> active)

        :param cm: CO2 controller mode (0 -> off 1 -> read-only 2 -> active)
        :type cm: int
        """
        if cm in [0, 1, 2]:
            self.__cm = cm
            self._cm_set = True

    @property
    def om(self) -> int:
        """
        Get O2 controller mode (0 -> off 1 -> read-only 2 -> active)

        :return: o2 controller mode
        :rtype: int
        """
        return self.__om

    @om.setter
    def om(self, om: int) -> None:
        """
        Set O2 controller mode (0 -> off 1 -> read-only 2 -> active)

        :param om: 0 -> off 1 -> read-only 2 -> active
        :type om: int
        """
        if om in [0, 1, 2]:
            self.__om = om
            self._om_set = True

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
        self._iv_set = True

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
        self._timestamp_set = True

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
        self._ct_set = True

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
    def generate_timestamp() -> str:
        """
        Generate iso timestamp (UTC)

        :return: iso format timestamp in base utc
        :rtype: str
        """
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

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
