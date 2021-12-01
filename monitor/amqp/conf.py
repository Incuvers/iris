class AMQPConf:
    EXCHANGE = 'device'

    class Routes:
        TELEMETRY = 'telemetry'
        COMMAND = 'command'
        ISR = 'isr'
