# API & Proxy Architecture
Modified: 2021-05

## Navigation
1. [Payload Caching](#payload-caching)
2. [Caveats](#caveats)
3. [Request Caching](#request-caching-methodology)

DeviceSettings API Request Methods:
```python
    # Caller: CloudController._on_connect_callback()
    def request_jwt(self) -> None:
    # Caller: CloudController._delta_callback():
    def get_device_info_and_avatar(self) -> DEVICE_AVATAR_FETCHED, DEVICE_FETCHED:
    def get_protocol(self, protocol_id:int) -> PROTOCOL_FETCHED:
    def get_experiment(self) -> EXPERIMENT_FETCHED, IMAGING_PROFILE_FETCHED:
    # Caller: Event CALIBRATION_INFO_UPDATED
    def _send_co2_calibration_time(self, calibration_time:str) -> None:
    # Caller: Event DPC_CAPTURE_COMPLETED:
    def _upload_dpc_images(self, capture:Capture) -> None:
```
We need some sort of feedback loop to determine if a request passed or failed. Currently we have a try catch surrounding all ApiHandler() function calls. If catch an exception we know that the API Request failed and begin caching requests. Even for multi-layered requests, one exception is enough to throw out the entire function call and restart from scratch Once a specific request goes through successfully we know we can re-execute other cached requests. We send a signal that calls these functions again which can then be fed back into the cache if the request fails again.

### Rules
1. Functions that make api calls are going to be reffered to as request wrappers
2. Wrappers must be fully reversible. Take for example a multi-layered request:
    ```python
    # raises ConnectionError and ReferenceError
    device_info = self._api_handler.get_device_info()
    # perform check on registration
    lab_id = device_info['lab_id']
    self.event_handler.trigger('REGISTRATION_STATUS_UPDATED', lab_id)
    if device_info['lab_id'] is None:
        lab_id = ' '
        registration_key = self._api_handler.get_registration_key()
        self.event_handler.trigger('REGISTRATION_KEY_FETCHED', registration_key)
    self._logger.info("Device registered to lab: %s", lab_id)
    self.write_local_lab_id(str(lab_id))
    # broadcast payload for caching
    self.event_handler.trigger('DEVICE_FETCHED', device_info)
    # here we do not want to propagate device avatar fetch failure since we can simply
    # fallback to the default
    try:
        response = self._api_handler.get_device_avatar()
    except (ConnectionError, KeyError) as exc:
        self._logger.error("Problem while fetching device avatar: %s", exc)
        self._logger.warning("Using default avatar")
    else:
        try:
            with ContextManager() as context:
                avatar_path = context.get_env('SNAP_COMMON') + '/device_avatar.png'
                with open(avatar_path, 'wb') as avatar:
                    avatar.write(response)
        except IOError as exc:
            self._logger.exception("Unable to write the new device image to disk - Error: %s", exc)
        else:
            self._logger.info("Saved device avatar to %s", avatar_path)
            # trigger for UI to update device avatar
            self.event_handler.trigger('DEVICE_AVATAR_FETCHED')
    ```
    If the call to `self._api_handler.get_device_avatar()` fails we want to throw out the entire function and restart the process. However we have already executed an external call: `self.event_handler.trigger('REGISTRATION_STATUS_UPDATED', lab_id)` to update the registration status. To avoid this we must enforce smaller functions with better seperation of concerns.
3. Wrappers are the functions to be cached since they contain the neccessary control logic for multi-layered api requests and system responses to api calls. All the logic must be re-evaluated if the api request fails
4. Wrappers cannot return directly to an external caller. Wrappers must fire an event containing the payload information. This restricts the returns to specific registered callback functions designed for multi-threaded operation.

## Wrapper Schema:
The goal is to keep the function design simple and scalable while maintaining its ability to be reversible. Its comprised of 3 parts:
1. API Request
2. General Logic
3. External System Call

A general schema is detailed below:
```python
@cache # decorator that tells the system to cache this function if the request fails
def sample_request_wrapper(self, *argv, **kwargs) -> None:
    # pre setup (if required) external modifiers not allowed at this stage (get calls ok)
    exp_id = self.experiment.get_id()
    # First job is to make api request. If this raises specific errors it is caught by the cache decorator
    payload = self._api_handler.request(exp_id)
    # General payload logic and setup
    payload = payload[1:9]
    # Last action is to trigger external system call
    self.event_handler.trigger('EVENT', payload)
```
