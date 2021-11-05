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
import ssl
import paho.mqtt.client as mqtt

from datetime import datetime, timezone
from json.decoder import JSONDecodeError

# from monitor.models.icb import ICB
from monitor.exceptions.mqtt import ImageTopicError
from monitor.environment.state_manager import StateManager
from monitor.cloud.config import MQTTConfig as conf
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis
from monitor.environment.thread_manager import ThreadManager as tm


class MQTT():
    """
    this class is responsible for cloud operations/communications both reporting and callback notification
    from the shadow service. This object is born in the flask webserver upon starting the flask application
    """

    def __init__(self, **kwargs):
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
        # self.shadow = None
        self._error_msg = ""
        # last long point type publish time
        self.last_lpt_publish = 0

        if 'device_id' in kwargs:
            device_id = kwargs['device_id']
        else:
            self._logger.critical("No client ID")

        self.aws_tt = f"aws/things/{device_id}/telemetry/"
        self.topic_desired = f"aws/things/{device_id}/desired/"
        self.aws_ip = f"aws/things/{device_id}/new_image/"
        self.iot_endpoint = "a1h6zgnf68qmlj-ats.iot.ca-central-1.amazonaws.com"

        self.client = mqtt.Client(client_id=device_id)
        self._configure_credentials(**kwargs)

        self._logger.info("Instantiation successful.")

    def _configure_credentials(self, **kwargs) -> None:
        ca_path = "./secrets/AmazonRootCA1.pem"
        cert_path = "./secrets/certificate.pem.crt"
        private_key_path = "./secrets/private.pem.key"

        try:
            # debug print opnessl version
            ssl_context = ssl.create_default_context()
            ssl_context.set_alpn_protocols(["x-amzn-mqtt-ca"])
            ssl_context.load_verify_locations(cafile=ca_path)
            ssl_context.load_cert_chain(certfile=cert_path, keyfile=private_key_path)
            self.client.tls_set_context(context=ssl_context)

        except Exception as exc:
            self._logger.error("exception _configure_credentials(): %s", exc)
            raise exc

    @tm.threaded(daemon=True)
    def start(self) -> None:
        """
        Entry point for loading cloud assets and beginning telemetry reporting. If the MQTT
        connection fails we retry the connection setup process until the connection is successful
        """
        events.system_status.trigger(msg="Loading Incuvers cloud assets")
        while True:
            try:
                # auto calls on_connect_callback (if set)
                # self.client.connect(self.iot_endpoint, port=conf.PORT)
                self.client.connect(self.iot_endpoint, port=443)
                self.client.loop_start()
                self._configure_connection()
                self._logger.info('connect ok.')

            except ConnectionError:
                with StateManager() as state:
                    device = state.device
                    device.mqtt_status = False
                    state.commit(device)
                self._logger.warning("Connection to mqtt failed. Entering reconnection phase...")
                time.sleep(conf.RECONNNECT)
            else:
                self._report_telemetry()
                break

    @tm.set_name("mqtt-con")
    def _on_connect(self, *args) -> None:
        """
        MQTT connect on callback
        """
        self._logger.info("Connected to MQTT broker")

        # subscribe to mulitple topics
        res = self.client.subscribe(self.topic_desired, 0)
        self._logger.info("subscribe results: %s", res)
        self.client.message_callback_add(self.topic_desired, self._desired_topic_resolver)

        res = self.client.subscribe(self.aws_ip, 0)
        self._logger.info("subscribe results: %s", res)
        self.client.message_callback_add(self.aws_ip, self._img_topic_resolver)

        # really gotta make sure the subscribe is finilized before attempting a jwt renew...
        self.client.loop()

        # attempt jwt request
        events.renew_jwt.trigger()
        events.new_device.trigger()
        with StateManager() as state:
            device = state.device
            device.mqtt_status = True
            state.commit(device)

    @tm.set_name("mqtt-discon")
    def _on_disconnect(self, *args) -> None:
        """
        MQTT disconnect callback
        """
        self._logger.info("Disconnected from MQTT broker")
        events.system_status.trigger(status=uis.STATUS_OK)
        with StateManager() as state:
            device = state.device
            device.mqtt_status = False
            state.commit(device)

    def _configure_connection(self):
        """
        configures the connection required to successfully communicate with the cloud services
        :raises ConnectionError: If connection is unssuccessl indicating the device is offline
        """
        self.client.on_connect = self._on_connect
        self._logger.info("Successfully configured MQTT connection")

    def _generate_shadow_document(self) -> dict:
        """Construct a dictionary having the reported part of the shadow document
        Note that the shadow is no longer used in the AWS-style (using a shoado service).
        Instead we are generating and publishing the full contents continuously over telemetry.

        :return: The reported section of a classic shadow document
        :rtype: dict
        """
        # populate everythiing the shadow used to have, including redundant data.
        # Just naively duplicate everything first before pruning.
        # shadow skeleton
        shadow_payload = {'state': {'reported': {}}}
        # JWT --- no need, not including
        # Refresh --- no need, not including
        # Setpoints --- can be pruned out later
        with StateManager() as state:
            icb = state.icb
            shadow_payload['state']['reported']['TP'] = icb.tp
            shadow_payload['state']['reported']['PP'] = icb.op
            shadow_payload['state']['reported']['CP'] = icb.cp
        # Imaging settings
        with StateManager() as state:
            imaging_profile = state.imaging_profile
            imaging_payload = {
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
            shadow_payload['state']['reported']['imaging_payload'] = imaging_payload
            return shadow_payload

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

    @tm.threaded(daemon=True)
    def _desired_topic_resolver(self, client, userdata, message) -> None:
        """
        Task resolver for the desired/write topic subscriptions
        """
        self._logger.info("Received payload from desired topic")

        try:
            payload: dict = json.loads(message.payload)
        except (JSONDecodeError, TypeError) as exc:
            raise ImageTopicError from exc
        self._logger.info("Received payload: %s from subscriber topic: %s", payload, message.topic)
        req_id = payload.get('req_id')
        if req_id is None:
            self._logger.info("Missing req_id, ignoring.")
            return
        self._delta_resolver(json.loads(message.payload)['state']['desired'], req_id)

    @tm.lock(tm.mqtt_lock)
    def _delta_resolver(self, requests: dict, req_id: str) -> None:
        """
        Resolve delta requests through event triggers or state manager commits
        :param requests: new filtered requests from delta
        :type requests: dict
        """
        self._logger.info("got request: %s", requests)
        # resolve jwt
        if "jwt" in requests:
            self._logger.info("got JWT request!")

            with StateManager() as state:
                device = state.device
                device.jwt = requests["jwt"]
                result = state.commit(device)
                # if commit fails do not report success
                if not result:
                    err_status = "Failed to resolve JWT\n"
                    self._logger.warning(err_status)
                    self._error_msg += err_status
        # resolve setpoints
        if "TP" in requests:
            tp = float(requests['TP'])
            with StateManager() as state:
                icb = state.icb
                icb.tp = tp
                result = state.commit(icb)
                # if commit fails do not report success
                if not result:
                    err_status = f"REQ:{req_id}: Failed to resolve TP\n"
                    self._logger.warning(err_status)
                    self._error_msg += err_status
        if "OP" in requests:
            op = float(requests['OP'])
            with StateManager() as state:
                icb = state.icb
                icb.op = op
                result = state.commit(icb)
                # if commit fails do not report success
                if not result:
                    err_status = f"REQ:{req_id}: Failed to resolve OP\n"
                    self._logger.warning(err_status)
                    self._error_msg += err_status
        if "CP" in requests:
            cp = float(requests['CP'])
            with StateManager() as state:
                icb = state.icb
                icb.cp = cp
                result = state.commit(icb)
                # if commit fails do not report success
                if not result:
                    err_status = f"REQ:{req_id}: Failed to resolve CP\n"
                    self._logger.warning(err_status)
                    self._error_msg += err_status

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
                imaging_profile.deserialize(**imaging_settings)
                result = state.commit(imaging_profile)
                # if commit fails do not report success
                if not result:
                    err_status = f"REQ:{req_id}: Failed to resolve imaging_settings\n"
                    self._logger.warning(err_status)
                    self._error_msg += err_status

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

    @tm.threaded(daemon=True)
    def _report_telemetry(self) -> None:
        """
        Callback for reporting telemetry data to cloud. We have different telemetry point types
        with different ttl values for plotting on the webapp so we package the telemetry based on
        these timings.

        :param qos: AWS client publishing parameter defining caching and retrying failed publishes
        """
        # TODO: check timestamps to see if data is old
        while True:
            with StateManager() as state:
                icb = state.icb
            try:
                epoch = round(datetime.now(timezone.utc).timestamp())
                self._logger.info("reporting telemetry results: %s", epoch)
                self.client.publish(self.aws_tt, json.dumps({"tele_test": epoch}), qos=0)

                # publish long point once every 15 minutes
                if epoch >= self.last_lpt_publish + (15 * 60):
                    save_point = True
                    self.last_lpt_publish = epoch
                else:
                    save_point = False
                if icb.initialized:
                    # classic minimal telemetry payload
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
                    # full state payload
                    payload['shadow'] = self._generate_shadow_document()
                    payload['errors'] = self._error_msg

                    self.client.publish(self.aws_tt, json.dumps(payload), qos=0)
                    self._logger.debug("Published telemetry document %s", payload)
                    with StateManager() as state:
                        experiment = state.experiment
                    if experiment.active:
                        # republish old telemetry, but with exp_id
                        payload['exp_id'] = experiment.id
                        self.client.publish(self.aws_tt, json.dumps(payload), qos=0)
                        self._logger.debug("Published experiment telemetry document %s", payload)
                    # reset the error_msgs
                    self._error_msg = ""
            except (ValueError, TypeError) as exc:
                self._logger.exception("Telemetry document publish failed: %s", exc)
            time.sleep(5)
