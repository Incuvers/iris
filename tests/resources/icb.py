"""
ICB Resources
=============
"""

ARDUINO_STRING = bytes(
    "173~1bfa167e$TS|1132319248&ID|&IV|v1.12 (03)&IR|4&FM|0&TM|1&TP|2000&TC|2231&TD|2163&TO|-\
        10000&TS|--&TA|-&CM|0&CP|500&CC|-10000&CS|-&CA|-&OM|0&OP|520&OC|-10000&OS|-&OA|-&LM|0&LS|\
            -&FM|5336\r", "utf-8")

ICB_CMD_STR = "173~1bfa167e$TS|1132319248&ID|&IV|3407285"
ICB_READLINE = bytes(
    "173~1bfa167e$&IV|3407285&TM|2&TP|3660&TC|3663&TO|50&TA|0&FP|40&FC|4088&HP|100&HC|1&CM|2&CP|500&CC|525&RH|0&CTR|0.00&CS|-&CA|*&CT|37531&OM|2&OP|1780&OC|1777&OS|-&OA|*&OPT1|0\r", 'utf-8')
ICB_READLINE_MALFORMED = bytes(
    "173~1bfa167e$&IV|3407285&TM|&TP|3660&TC|3663&TO|50&TA|0&FP|40&FC|4088&HP|100&HC|1&CM|2&CP|500&CC|525&RH|0&CTR|0.00&CS|-&CA|*&CT|37531&OM|2&OP|1780&OC|1777&OS|-&OA|*&OPT1|0\r", 'utf-8')
ICB_SENSORFRAME = {
    'IV': '3407285',
    'TM': 2,
    'TP': 3660,
    'TC': 3663,
    'TO': 50,
    'TA': 0,
    'FP': 40,
    'FC': 4088,
    'HP': 100,
    'HC': 1,
    'CM': 2,
    'CP': 500,
    'CC': 525,
    'RH': 0,
    'CTR': 0.00,
    'CT': 37531,
    'OM': 2,
    'OP': 1780,
    'OC': 1777,
    'OPT1': 0,
    'timestamp': '2019-10-09 12:32:35.249752+00:00'
}

ICB_SENSORFRAME_2 = {
    'IV': '3407285',
    'TM': 2,
    'TP': 36.60,
    'TC': 36.63,
    'TO': 50,
    'TA': 0,
    'FP': 40,
    'FC': 4088,
    'HP': 100,
    'HC': 1,
    'CM': 2,
    'CP': 5.0,
    'CC': 5.25,
    'RH': 0,
    'CTR': 0.00,
    'CT': 37531,
    'OM': 2,
    'OP': 17.80,
    'OC': 17.77,
    'OPT1': 0,
    'timestamp': '2019-10-09 12:32:35.249752+00:00'
}

ICB_SENSORFRAME_2_CONV = {
    'IV': '3407285',
    'TM': 2,
    'TP': 36.6,
    'TC': 36.6,
    'TO': 50,
    'FP': 40,
    'FC': 4088,
    'HP': 100,
    'CM': 2,
    'CP': 5.0,
    'CC': 5.2,
    'RH': 0,
    'CTR': 0.00,
    'CT': 37531,
    'OM': 2,
    'OP': 17.8,
    'OC': 17.8,
}
