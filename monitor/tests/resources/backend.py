"""
Backend Resources
=================
"""

# API
API_BASE_URL = 'api.dev.incuvers.com'
API_BASE_PATH = '/v1'
SAMPLE_JWT = """Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IitVS1gwSFo3UmcycFdSZG1wQXN0U3ExdmJqWXhCZnoxSDVuV
lJZcUlicTg9In0.eyJzdWIiOiJiMjRmMGI4NC0yN2JlLTQyYTYtOWQwNy1iM2M2ODEwYzgwMTAiLCJjdXN0b21lcl9pZCI6MSwic3RhZ2UiOiJkZXYiL
CJhdWQiOiJhMWg2emduZjY4cW1sai1kZXYiLCJ0b2tlbl91c2UiOiJhY2Nlc3MiLCJ0b2tlbl90eXBlIjoiaXJpcyIsImZyZXNoIjp0cnVlLCJpc3MiO
iJJbmN1dmVycyBJbmMuIiwiaWF0IjoxNjE2Nzk2OTU0LCJleHAiOjE2MTY4MDA1NTQsImNzcmYiOiI2MjI0ODY0MjUxODgzNmU3NjdiMzQ1NjQyY2E3O
TIxZTBjOTA0ODc4In0.Rpyu6jh5jjrsCFb2VMHoCwKte0LBSpeL6B6ht_2xpr6bKVn49UPL5ZNzBmwO_vvwRs80j45jrKK4WxR-JVA_RfOk6KDCsZxbP
fgJeWw4S3qYEIKbtqEnqTOZOU8BNxVDcbfIM0IEnZxLvssOlDVPNCXAkJ5DCMhmM0U2oh7noU4myxXFvg_TkzI7Xs7Dl6vvTKT3dSo3kz-VfzYDnIeL4
6L5DQ2gOnLZqctya9W-ebjDIeyeo0IuHf1WM7OkYl8WqsNysKbDkMAGDBwktXZhERYHCGhdWW-bMArBnJ9WVLk9nBr4VnhFHJRJpLy8GrJa58X9KpKxe
0iNjs8LSIreDQ"""
SAMPLE_JWT_PAYLOAD = {
    "sub": "b24f0b84-27be-42a6-9d07-b3c6810c8010",
    "lab_id": 1,
    "stage": "dev",
    "aud": "a1h6zgnf68qmlj-dev",
    "token_use": "access",
    "token_type": "iris",
    "fresh": True,
    "iss": "Incuvers Inc.",
    "iat": 1616796954,
    "exp": 1616800554,
    "csrf": "62248642518836e767b345642ca7921e0c904878"
}

# MQTT
DEFAULT_TELEMETRY_PAYLOAD = {'TC': None, 'CC': None, 'OC': None, 'RH': None, 'TP': 37.5, 'CP': 5.0, 'OP': 20.9,
                             'TO': 0.5, 'time': '2021-05-26T20:20:14+00:00', 'exp_id': '-1', 'ttl': 0, 'point_type': 1}
SHADOW_DOCUMENT = {
    "desired": {
        "TP": 34,
        "CP": 4,
        "OP": 4,
        "refresh": {
            "device": "2021-05-07T19:44:04.876065+00:00",
            "experiment": "2021-04-30T21:54:48.002+00:00",
            "customer": "2021-04-30T21:54:48.002+00:00",
            "protocol": "2021-04-30T21:54:48.002+00:00"
        },
        "jwt": SAMPLE_JWT,
        "imaging_settings": {
            "dpc_brightness": 168,
            "dpc_gain": 4,
            "dpc_exposure": 11840,
            "gfp_brightness": 168,
            "gfp_gain": 60,
            "gfp_exposure": 756438,
            "dpc_inner_radius": 3,
            "dpc_outer_radius": 4,
            "imaging_profile_id": -1,
            "name": "Default Profile",
            "gain_min": 4,
            "gain_max": 63,
            "brightness_min": 0,
            "brightness_max": 4096,
            "gfp_capture": True,
            "gfp_exposure_min": 100000,
            "gfp_exposure_max": 2000000,
            "dpc_exposure_min": 2000,
            "dpc_exposure_max": 15000
        }
    },
    "reported": {
        "is_online": True,
        "TP": 34,
        "CP": 4,
        "OP": 4,
        "refresh": {
            "device": "2021-05-07T19:44:04.876065+00:00",
            "experiment": "2021-04-30T21:54:48.002+00:00",
            "customer": "2021-04-30T21:54:48.002+00:00",
            "protocol": "2021-04-30T21:54:48.002+00:00"
        },
        "jwt": SAMPLE_JWT,
        "imaging_settings": {
            "dpc_brightness": 168,
            "dpc_gain": 4,
            "dpc_exposure": 11840,
            "gfp_brightness": 168,
            "gfp_gain": 60,
            "gfp_exposure": 756438,
            "dpc_inner_radius": 3,
            "dpc_outer_radius": 4,
            "imaging_profile_id": -1,
            "name": "Default Profile",
            "gain_min": 4,
            "gain_max": 63,
            "brightness_min": 0,
            "brightness_max": 4096,
            "gfp_capture": True,
            "gfp_exposure_min": 100000,
            "gfp_exposure_max": 2000000,
            "dpc_exposure_min": 2000,
            "dpc_exposure_max": 15000
        }
    }
}


# Backend Payloads
SAMPLE_POST_PAYLOAD = {
    "name": "Test",
    "value": True
}

EXPERIMENT_PAYLOAD = {
    "cell_types": [
        {
            "cell_id": 11,
            "cell_type": "cell type 1",
            "created_at": "2019-11-07T18:27:26.238408+00:00",
            "lab_id": "1e97753037aef50ab1ea5d70b71b753",
            "is_deleted": False,
            "updated_at": "2019-11-07T18:27:26.238419+00:00"
        },
        {
            "cell_id": 12,
            "cell_type": "another type",
            "created_at": "2019-11-07T18:31:55.897204+00:00",
            "lab_id": "1e97753037aef50ab1ea5d70b71b753",
            "is_deleted": False,
            "updated_at": "2019-11-07T18:31:55.897216+00:00"
        }
    ],
    "created_at": "2019-10-04 20:19:31.740612+00:00",
    "device_id": "1e9781c4b4a51d0ab1ea5d70b71b753",
    "end_at": "2021-10-03T21:18:00+00:00",
    "experiment_id": 8,
    "gfp_capture": False,
    "imaging_profile_id": 1,
    "image_capture_interval": 5,
    "initiated_by": "1e9781495714be0ab1ea5d70b71b753",
    "is_deleted": False,
    "is_finished": False,
    "is_passage": False,
    "experiment_name": "Demo Experiment 1",
    "passage_num": 1,
    "protocol_id": 4,
    "reagents": [
        {
            "created_at": "2019-12-03T21:43:34.439128+00:00",
            "lab_id": "1e97753037aef50ab1ea5d70b71b753",
            "is_deleted": False,
            "reagent_id": 1,
            "reagent_name": "reagent 1",
            "updated_at": "2019-12-03T21:43:34.439169+00:00"
        }
    ],
    "start_at": "2021-10-03T20:18:00+00:00",
    "updated_at": "2021-01-22T23:30:32.636405+00:00",
    "user_lab": "1e97753037aef50ab1ea5d70b71b753",
    "user_notes": "This is a test"
}

PROTOCOL_PAYLOAD = {
    "created_at": "2019-10-09 12:32:35.249752+00:00",
    "is_deleted": False,
    "name": "New Name",
    "id": 45,
    "repeats": 2,
    "setpoints": [
        {
            "CP": 3.6,
            "created_at": "2019-10-21 17:08:36.818729+00:00",
            "duration": 10980,
            "index": 0,
            "is_deleted": False,
            "OP": 20,
            "protocol_id": 45,
            "setpoint_id": 25,
            "TP": 37,
            "updated_at": "2019-10-21 17:37:12.210638+00:00"
        },
        {
            "CP": 4.1,
            "created_at": "2019-10-21 17:08:36.818856+00:00",
            "duration": 90000,
            "index": 1,
            "is_deleted": False,
            "OP": 20,
            "protocol_id": 45,
            "setpoint_id": 26,
            "TP": 37,
            "updated_at": "2019-10-21 17:37:12.144596+00:00"
        },
        {
            "CP": 6.6,
            "created_at": "2019-10-21 17:37:25.773532+00:00",
            "duration": 97200,
            "index": 2,
            "is_deleted": False,
            "OP": 20,
            "protocol_id": 45,
            "setpoint_id": 28,
            "TP": 37,
            "updated_at": "2019-10-21 17:37:25.773543+00:00"
        }
    ],
    "start_at": "2020-10-29 15:15:03.563774+00:00",
    "shared": False,
    "updated_at": "2019-10-21 17:37:03.563774+00:00"
}
