"""
Monitor Runtime Models
======================
"""
from datetime import datetime
from monitor.tests.resources.backend import SAMPLE_JWT, SAMPLE_JWT_PAYLOAD

ISO_DATETIME_START = "2020-10-29 15:15:03.563774+00:00"
ISO_DATETIME_END = "2020-10-30 15:15:03.563774+00:00"

# System Runtime Models
DEVICE_MODEL = {
    "id": "djksaldnkalndklsandla",
    "name": "Welcome to IRIS",
    "lab_id": 1,
    "jwt": SAMPLE_JWT,
    "jwt_payload": SAMPLE_JWT_PAYLOAD,
    "connected": True
}

IMAGING_PROFILE_MODEL = {
    "id": 1,
    "name": "Default Profile",
    "dpc_brightness": 168,
    "dpc_gain": 4,
    "dpc_exposure": 8500,
    "gfp_brightness": 168,
    "gfp_gain": 60,
    "gfp_exposure": 1050000,
    "dpc_inner_radius": 3.0,
    "dpc_outer_radius": 4.0,
    "gfp_capture": False
}

PROTOCOL_MODEL = {
    "name": "Protocol Model",
    "id": 45,
    "repeats": 2,
    "start_at": datetime.fromisoformat("2020-10-29 15:15:03.563774+00:00"),
    "setpoints": [
        {
            "CP": 3.6,
            "duration": 10980,
            "index": 0,
            "OP": 20,
            "TP": 37,
        },
        {
            "CP": 4.1,
            "duration": 90000,
            "index": 1,
            "OP": 20,
            "TP": 37,
        },
        {
            "CP": 6.6,
            "duration": 97200,
            "index": 2,
            "OP": 20,
            "TP": 37,
        }
    ],
}

PROTOCOL_SERIALIZED = {
    "name": "Protocol Model",
    "id": 45,
    "repeats": 2,
    "start_at": ISO_DATETIME_START,
    "setpoints": [
        {
            "CP": 3.6,
            "duration": 10980,
            "index": 0,
            "OP": 20,
            "TP": 37,
        },
        {
            "CP": 4.1,
            "duration": 90000,
            "index": 1,
            "OP": 20,
            "TP": 37,
        },
        {
            "CP": 6.6,
            "duration": 97200,
            "index": 2,
            "OP": 20,
            "TP": 37,
        }
    ],
}

EXPERIMENT_MODEL = {
    "name": "Experiment Model",
    "id": 452,
    "protocol_id": 45,
    "imaging_profile_id": 23,
    "image_capture_interval": 600,
    "start_at": datetime.fromisoformat(ISO_DATETIME_START),
    "end_at": datetime.fromisoformat(ISO_DATETIME_END),
    "stop_at": None
}

EXPERIMENT_SERIALIZED = {
    "name": "Experiment Model",
    "id": 452,
    "protocol_id": 45,
    "imaging_profile_id": 23,
    "image_capture_interval": 600,
    "start_at": ISO_DATETIME_START,
    "end_at": ISO_DATETIME_END,
    "stop_at": None
}
