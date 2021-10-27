# -*- coding: utf-8 -*-
"""
MQTT
====
Modified: 2021-07

Dependencies:
-------------
```
from json.decoder import JSONDecodeError
import time
import json
import logging
from typing import Any, Dict
import monitor.imaging.constants as IC
from datetime import datetime, timezone
from AWSIoTPythonSDK.exception import AWSIoTExceptions
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from monitor.models.icb import ICB
from monitor.exceptions.mqtt import ImageTopicError
from monitor.environment.state_manager import StateManager
from monitor.cloud.config import MQTTConfig as conf
from monitor.environment.context_manager import ContextManager
from monitor.events.registry import Registry as events
from monitor.models.imaging_profile import ImagingProfile
from monitor.ui.static.settings import UISettings as uis
from monitor.environment.thread_manager import ThreadManager as tm
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import time
import json
import logging
from typing import Any, Dict
import monitor.imaging.constants as IC

from datetime import datetime, timezone
from json.decoder import JSONDecodeError
from AWSIoTPythonSDK.exception import AWSIoTExceptions
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

from monitor.models.icb import ICB
from monitor.exceptions.mqtt import ImageTopicError
from monitor.environment.state_manager import PropertyCondition, StateManager
from monitor.cloud.config import MQTTConfig as conf
from monitor.environment.context_manager import ContextManager
from monitor.events.registry import Registry as events
from monitor.models.imaging_profile import ImagingProfile
from monitor.ui.static.settings import UISettings as uis
from monitor.environment.thread_manager import ThreadManager as tm


def validate_shadow_init(func):
    def wrapper(self, *args, **kwargs):
        if self.shadow is not None:
            func(self, *args, **kwargs)
        else:
            self._logger.warning("Shadow has not been initialized. Skipping report")
    return wrapper


class MQTT(AWSIoTMQTTShadowClient):
    """
    this class is responsible for cloud operations/communications both reporting and callback notification
    from the shadow service. This object is born in the flask webserver upon starting the flask application
    """

    def __init__(self):
        """
        :param sensors: sensorframe object
        :param clientID: client id required by mqtt
        :param endpoint: endpoint of subscriber channel
        :param credential_path: required credential information
        :param port: port used by cloud service
        """
        # bind logging to config file
        self._logger = logging.getLogger(__name__)
        self.last_calibrated = None
        # for diff checking
        self._delta = {}
        self.shadow = None
        # last long point type publish time
        self.last_lpt_publish = 0
        with StateManager() as state:
            # subscribe to icb setpoint state changes
            state.subscribe_property(
                _type=ICB,
                _property=PropertyCondition[ICB](
                    trigger=lambda old_icb, new_icb:
                        old_icb.tp != new_icb.tp or old_icb.cp != new_icb.cp or old_icb.op != new_icb.op,
                    callback=self.update_setpoints,
                    callback_on_init=True
                )
            )
            state.subscribe(ICB, self._report_telemetry)
            state.subscribe(ImagingProfile, self.update_imaging_settings)
        with ContextManager() as context:
            self.id = context.get_env('ID')
            super().__init__(self.id)
            pem = context.get_env('AWS_PEM')
            key = context.get_env('AWS_KEY')
            cert = context.get_env('AWS_CERT')
            self.aws_tt = context.get_env('AWS_TT')
            self.aws_st = context.get_env('AWS_ST')
            self.aws_ip = context.get_env('AWS_IP')
            # inherited
            self.configureEndpoint(context.get_env('IOT_BASE_URL'), conf.PORT)
        self.configureCredentials(pem, KeyPath=key, CertificatePath=cert)
        self.client = self.getMQTTConnection()
        self._logger.info("Instantiation successful.")

    @tm.threaded(daemon=True)
    def start(self) -> None:
        """
        Entry point for loading cloud assets and beginning telemetry reporting. If the MQTT
        connection fails we retry the connection setup process until the connection is successful
        """
        events.system_status.trigger(msg="Loading Incuvers cloud assets")
        while True:
            try:
                # auto calls on_connect_callback
                self._configure_connection()
                self.shadow_document_init()
            except ConnectionError:
                with StateManager() as state:
                    device = state.device
                    device.connected = False
                    state.commit(device)
                self._logger.warning("Connection to mqtt failed. Entering reconnection phase...")
                time.sleep(conf.RECONNNECT)
            else:
                self._on_connect()
                break

    @tm.set_name("aws-connect")
    @validate_shadow_init
    def _on_connect(self) -> None:
        """
        MQTT connect on callback
        """
        self._logger.info("Connected to MQTT broker")
        self._report_shadow(payload={'state': {'reported': {"is_online": True}}})
        # attempt jwt request
        events.renew_jwt.trigger()
        events.new_device.trigger()
        with StateManager() as state:
            device = state.device
            device.connected = True
            state.commit(device)

    @tm.set_name("aws-discon")
    @validate_shadow_init
    def _on_disconnect(self) -> None:
        """
        MQTT disconnect callback
        """
        self._logger.info("Disconnected from MQTT broker")
        events.system_status.trigger(status=uis.STATUS_OK)
        with StateManager() as state:
            device = state.device
            device.connected = False
            state.commit(device)

    def _configure_connection(self):
        """
        configures the connection required to successfully communicate with the cloud services
        :raises ConnectionError: If connection is unssuccessl indicating the device is offline
        """
        self.configureAutoReconnectBackoffTime(1, 32, 20)
        self.configureConnectDisconnectTimeout(5)  # 5 sec
        self.configureMQTTOperationTimeout(5)  # 5 sec
        self.client.configureOfflinePublishQueueing(-1)
        self.client.configureDrainingFrequency(2)
        # configure connection callbacks
        self.onOnline = self._on_connect
        self.onOffline = self._on_disconnect
        # configure last will payload
        last_will_payload = json.dumps({'state': {'reported': {'is_online': False}}})
        with ContextManager() as context:
            self.configureLastWill(context.get_env('AWS_LWT'), last_will_payload, 0)
        try:
            self.connect(keepAliveIntervalSecond=10)
        except (AWSIoTExceptions.connectTimeoutException, AWSIoTExceptions.connectError) as exc:
            self._logger.warning(
                "Unable to configure a connection with the cloud services: %s", exc)
            raise ConnectionError from exc
        try:
            # creating shadow handler after AWSIoTMQTTShadowClient.connect() as per documentation
            with ContextManager() as context:
                self.shadow = self.createShadowHandlerWithName(context.get_env('ID'), True)
            self.shadow.shadowRegisterDeltaCallback(self._shadow_delta_response)
            # subscribe to imaging preview MQTT channel
            self.client.subscribe(self.aws_ip, 0, self._img_topic_resolver)
        except (AWSIoTExceptions.subscribeTimeoutException, AWSIoTExceptions.subscribeError) as exc:
            self._logger.exception("Subscribe timeout exception detected: %s", exc)
            raise ConnectionError from exc
        self._logger.info("Successfully configured MQTT connection")

    def shadow_document_init(self):
        """
        Verify and initialize the shadow document if not present.

        :raises ConnectionError: if the shadow get method fails
        """
        try:
            if self.shadow is not None:
                self.shadow.shadowGet(self._shadow_get_response, 5)
        except (AWSIoTExceptions.subscribeTimeoutException, AWSIoTExceptions.subscribeError) as exc:
            self._logger.exception("Subscribe timeout exception detected: %s", exc)
            raise ConnectionError from exc
        self._logger.info("Verified shadow documents")

    @tm.set_name("shadow-get-response")
    def _shadow_get_response(self, shadow_document: str, responseStatus: str = None, token=None):
        """
        :param shadow_document: shadow document associated with the device
        :param responseStatus: status will return accepted if it's a valid response
        :param token: returning back the id we passed into the function
        """
        if responseStatus == "accepted":
            shadow: Dict[str, Dict[str, Any]] = json.loads(shadow_document)
            self._logger.debug("Shadow reset parsing on %s", shadow)
            # determine if shadow requires a reset
            if shadow.get('state') is None or "desired" not in shadow['state'].keys():
                self._logger.info(
                    "Shadow document is empty. Repopulating with local shadow template.")
                self._report_shadow(payload={'state': self._generate_shadow_document()})
            elif shadow['state']['desired'].get('refresh') is None:
                self._logger.info(
                    "Shadow document is empty. Repopulating with local shadow template.")
                self._report_shadow(payload={'state': self._generate_shadow_document()})
            else:
                with StateManager() as state:
                    icb = state.icb
                    icb.tp = shadow['state']['desired'].get('TP')
                    icb.op = shadow['state']['desired'].get('OP')
                    icb.cp = shadow['state']['desired'].get('CP')
                    while not icb.initialized:
                        self._logger.warning("ICB state uninitialized. Waiting for initialization ...")
                        time.sleep(1)
                        icb = state.icb
                    # update cached setpoints with previously pushed values
                    state.commit(icb, source=True)
                with StateManager() as state:
                    imaging_profile = state.imaging_profile
                    imaging_profile.setattrs(**shadow['state']['desired'].get('imaging_settings'))
                    state.commit(imaging_profile, source=True)
            # verify IRIS state variables match with MQTT otherwise use the current IRIS settings as the source of truth
        else:
            self._logger.error(
                "Device shadow update request %s rejected with response status: %s", token, responseStatus)

    @tm.threaded(daemon=True)
    def _img_topic_resolver(self, client, userdata, message) -> None:
        """
        Task resolver for the imaging topic related subscriptions
        :param type: job type
        """
        try:
            payload: dict = json.loads(message.payload)
        except (JSONDecodeError, TypeError) as exc:
            raise ImageTopicError from exc
        self._logger.info("Received payload: %s from subscriber topic: %s", payload, message.topic)
        if payload.get('type') == "experiment":
            events.thumbnail_pipeline.begin()
        elif payload.get('type') == "dpc-capture":
            events.preview_pipeline.begin(gfp=False)
        elif payload.get('type') == "gfp-capture":
            events.preview_pipeline.begin(gfp=True)

    @tm.set_name("delta-response")
    def _shadow_delta_response(self, delta_str: str, responseStatus: str, token) -> None:
        """
        Resolves shadow delta trigger into 3 components: JWT refresh, device setting refresh, or a
        setpoint refresh. It then triggers events to be executed which when complete resolve the
        shadow delta. If the process is not completed, the delta will not be resolved and this
        callback will be triggered again.
        :param delta: delta in desired and reported shadow document
        :param responseStatus: aws standard for shadow callback
        :param token: aws standard for shadow callback
        """
        events.cloud_sync.trigger(True)
        if responseStatus != f"delta/{self.id}":
            self._logger.error("Device shadow delta rejected with response: %s", responseStatus)
            return
        _requests = {}
        self._logger.info("Device shadow delta %s accepted and updated with: %s", token, delta_str)
        # enable syncing status
        inbound_delta = json.loads(delta_str)
        delta_state = inbound_delta['state']
        # generate the request delta payload with only new or updated keys
        request_delta = self.filter_delta(self._delta, delta_state)
        self._logger.debug("Request delta: %s", request_delta)
        # update cached delta to match previous inbound delta
        self._delta = delta_state
        # construct request dict
        for key in request_delta:
            self._logger.info("%s in delta", key)
            _requests[key] = request_delta[key]
        self._logger.info("Shadow Delta Requests: %s", _requests)
        # check the delta requests list and apply the resolver if new requests are inbound
        if _requests != {}:
            self._delta_resolver(_requests)
        # disable sync status (keep thread alive for 1 second to show sync status to user)
        time.sleep(1)
        events.cloud_sync.trigger(False)

    @tm.lock(tm.mqtt_lock)
    def _delta_resolver(self, requests: dict) -> None:
        """
        Resolve delta requests through event triggers or state manager commits
        :param requests: new filtered requests from delta 
        :type requests: dict
        """
        # resolve jwt
        if "jwt" in requests:
            with StateManager() as state:
                device = state.device
                device.jwt = requests["jwt"]
                result = state.commit(device)
                # if commit fails do not report success
                if not result:
                    requests.pop("jwt")
        # resolve setpoints
        if "TP" in requests:
            tp = float(requests['TP'])
            with StateManager() as state:
                icb = state.icb
                icb.tp = tp
                result = state.commit(icb)
                # if commit fails do not report success
                if not result:
                    requests.pop("TP")
        if "OP" in requests:
            op = float(requests['OP'])
            with StateManager() as state:
                icb = state.icb
                icb.op = op
                result = state.commit(icb)
                # if commit fails do not report success
                if not result:
                    requests.pop("OP")
        if "CP" in requests:
            cp = float(requests['CP'])
            with StateManager() as state:
                icb = state.icb
                icb.cp = cp
                result = state.commit(icb)
                # if commit fails do not report success
                if not result:
                    requests.pop("CP")
        # resolve refresh flags
        if "refresh" in requests:
            refresh_requests = requests["refresh"]
            if "device" in refresh_requests:
                self.resolve_device_refresh()
            if "experiment" in refresh_requests:
                self.resolve_experiment_refresh()
            if "protocol" in refresh_requests:
                self.resolve_protocol_refresh()
        # resolve imaging settings
        if "imaging_settings" in requests:
            imaging_settings = requests["imaging_settings"]
            with StateManager() as state:
                imaging_profile = state.imaging_profile
                imaging_profile.setattrs(**imaging_settings)
                result = state.commit(imaging_profile)
                # if commit fails do not report success
                if not result:
                    requests.pop("imaging_settings")
        # report completion once all requests are properly resolved
        self._report_shadow(payload={'state': {'reported': requests}})

    @tm.threaded(daemon=True)
    def resolve_device_refresh(self):
        self._logger.info("Starting device refresh resolution")
        events.new_device.trigger()

    @tm.threaded(daemon=True)
    def resolve_experiment_refresh(self) -> None:
        self._logger.info("Starting experiment refresh resolution")
        events.new_experiment.trigger()

    @tm.threaded(daemon=True)
    def resolve_protocol_refresh(self) -> None:
        self._logger.info("Starting protocol refresh resolution")
        events.new_protocol.trigger()

    async def update_setpoints(self, sensorframe: ICB):
        """
        Update setpoint values for telemetry reporting and report setpoint changes on
        the local system to the shadow topic.
        :param sensorframe: sensorframe dict updated from callback function
        """
        # as long as there is one setpoint difference, report to cloud
        setpoint_payload = {
            'TP': sensorframe.tp,
            'OP': sensorframe.op,
            'CP': sensorframe.cp
        }
        # only report setpoint changes to avoid mqtt overload
        state_payload = {
            'state':
            {
                'desired': setpoint_payload,
                'reported': setpoint_payload,
            }
        }
        self._report_shadow(payload=state_payload)

    async def update_imaging_settings(self, imaging_profile: ImagingProfile) -> None:
        """
        Update shadow document with new imaging profile changes.
        """
        # generate payload
        payload = {
            'dpc_exposure': imaging_profile.dpc_exposure,
            'dpc_exposure_min': imaging_profile.dpc_exposure_min,
            'dpc_exposure_max': imaging_profile.dpc_exposure_max,
            'gfp_exposure': imaging_profile.gfp_exposure,
            'gfp_exposure_min': imaging_profile.gfp_exposure_min,
            'gfp_exposure_max': imaging_profile.gfp_exposure_max,
            'dpc_gain': imaging_profile.dpc_gain,
            'gfp_gain': imaging_profile.gfp_gain,
            'gain_min': imaging_profile.gain_min,
            'gain_max': imaging_profile.gain_max,
            'dpc_brightness': imaging_profile.dpc_brightness,
            'gfp_brightness': imaging_profile.dpc_brightness,
            'brightness_min': imaging_profile.brightness_min,
            'brightness_max': imaging_profile.brightness_max,
            'dpc_inner_radius': imaging_profile.dpc_inner_radius,
            'dpc_outer_radius': imaging_profile.dpc_outer_radius
        }
        # this reports the full image settings (overkill when only one changed)
        imaging_settings_payload = {
            'state':
            {
                'desired':
                {
                    'imaging_settings': payload
                },
                'reported':
                {
                    'imaging_settings': payload,
                }
            }
        }
        self._report_shadow(payload=imaging_settings_payload)

    @validate_shadow_init
    def _report_shadow(self, payload: Dict[str, Any]):
        """
        Update the MQTT shadow document with the reported changes
        :param payload: dictionary containing reported entries
        :param qos: AWS client publishing parameter defining caching and retrying failed publishes
        """
        self._logger.debug("Updating shadow document with: %s", payload)
        json_payload = json.dumps(payload)
        if self.shadow is not None:
            self.shadow.shadowUpdate(
                srcJSONPayload=json_payload,
                srcCallback=self._shadow_update_response,
                srcTimeout=conf.SHADOW_UPDATE_TIMEOUT
            )
        # self.client.publish(self.aws_st,json.dumps(payload),qos)
        self._logger.debug("Reported %s to MQTT shadow document", payload)

    def _shadow_update_response(self, payload: str, responseStatus: str, token) -> None:
        """
        Response callback function for shadowUpdate call
        :param payload: shadowUpdate payload
        :type payload: str
        :param responseStatus: response status from aws
        :type responseStatus: str
        :param token: shadowUpdate request identifier
        :type token: [type]
        """
        if responseStatus == "accepted":
            self._logger.info(
                "Device shadow request %s accepted and updated with: %s", token, payload)
        else:
            self._logger.error(
                "Device shadow update request %s rejected with response status: %s", token, responseStatus)

    async def _report_telemetry(self, icb: ICB) -> None:
        """
        Callback for reporting telemetry data to cloud. We have different telemetry point types
        with different ttl values for plotting on the webapp so we package the telemetry based on
        these timings.

        :param qos: AWS client publishing parameter defining caching and retrying failed publishes
        """
        try:
            epoch = round(datetime.now(timezone.utc).timestamp())
            # publish long point once every 15 minutes
            if epoch >= self.last_lpt_publish + (15 * 60):
                save_point = True
                self.last_lpt_publish = epoch
            else:
                save_point = False
            if icb.initialized:
                payload = {
                    'TC': icb.tc,
                    'CC': icb.cc,
                    'OC': icb.oc,
                    'RH': icb.rh,
                    'TP': icb.tp,
                    'CP': icb.cp,
                    'OP': icb.op,
                    'TO': icb.to,
                    'time': icb.timestamp,
                    'exp_id': "-1",
                    'ttl': 0 if save_point else datetime.now(timezone.utc).timestamp() + 120,
                    'point_type': 1 if save_point else 0
                }
                self.client.publish(self.aws_tt, json.dumps(payload), QoS=0)
                self._logger.debug("Published telemetry document %s", payload)
                with StateManager() as state:
                    experiment = state.experiment
                if experiment.initialized and experiment.active:
                    # republish old telemetry, but with exp_id
                    payload['exp_id'] = experiment.id
                    self.client.publish(self.aws_tt, json.dumps(payload), QoS=0)
                    self._logger.debug("Published experiment telemetry document %s", payload)
        except AWSIoTExceptions.publishTimeoutException as exc:
            self._logger.exception("Telemetry document publish timed out %s", exc)

    @staticmethod
    def filter_delta(cache: dict, delta: dict) -> dict:
        """
        Recursive method to compare a cached dict to an incoming dict and generating a dict with
        undiscovered changes from the incoming with respect to the cached copy.
        :param cache: reference delta diff
        :type cache: dict
        :param delta: incoming delta
        :type delta: dict
        :return: dict containing only new updates from delta
        :rtype: dict
        """
        _delta = {}
        # iterate through layer items
        for kvp in delta.items():
            key, value = kvp
            # check for new keys
            if key not in cache.keys():
                _delta[key] = value
            # explore nested structures
            elif isinstance(value, dict):
                diff = MQTT.filter_delta(cache[key], delta[key])
                if diff != {}: _delta[key] = diff
            # check for value diffs
            elif cache[key] != delta[key]:
                _delta[key] = delta[key]
        return _delta

    @staticmethod
    def _generate_shadow_document() -> Dict[str, Any]:
        """
        Compute shadow refresh timestamps and packages payload. This function is used to initialize
        the shadow document in the event it is unset or deleted.
        :returns payload: dict payload to be published to the shadow topic
        """
        with StateManager() as state:
            device = state.device
        jwt = device.jwt
        timestamp = datetime.now(timezone.utc).isoformat()
        shadow_template = {
            "desired":
            {
                "TP": ICB.TP_DEFAULT,
                "CP": ICB.CP_DEFAULT,
                "OP": ICB.OP_DEFAULT,
                "refresh":
                {
                    "device": timestamp,
                    "experiment": timestamp,
                    "customer": timestamp,
                    "protocol": timestamp
                },
                "jwt": jwt,
                "imaging_settings": IC.DEFAULT_IP_PAYLOAD
            },
            "reported":
            {
                "is_online": True,
                "TP": ICB.TP_DEFAULT,
                "CP": ICB.CP_DEFAULT,
                "OP": ICB.OP_DEFAULT,
                "refresh":
                {
                    "device": timestamp,
                    "experiment": timestamp,
                    "customer": timestamp,
                    "protocol": timestamp
                },
                "jwt": jwt,
                "imaging_settings": IC.DEFAULT_IP_PAYLOAD
            }
        }
        return shadow_template
