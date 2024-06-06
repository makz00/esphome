from enum import Enum


class PinMap(Enum):
    DigitalIn = 1
    DigitalOut = 2
    AnalogIn = 3
    AnalogOut = 4


ESP8266_PIN_MAP = {
    PinMap.DigitalIn: {
        "__IX0_0": "D4",
        "__IX0_1": "D5",
        "__IX0_2": "D6",
        "__IX0_3": "D7",
    },
    PinMap.DigitalOut: {
        "__QX0_0": "D0",
        "__QX0_1": "D1",
        "__QX0_2": "D2",
        "__QX0_3": "D3",
    },
    PinMap.AnalogIn: {"__IW0": "A0"},
    PinMap.AnalogOut: {"__QW0": "D8"},
}

ESP32_PIN_MAP = {
    PinMap.DigitalIn: {},
    PinMap.DigitalOut: {},
    PinMap.AnalogIn: {},
    PinMap.AnalogOut: {},
}

RP2040_PIN_MAP = {
    PinMap.DigitalIn: {},
    PinMap.DigitalOut: {},
    PinMap.AnalogIn: {},
    PinMap.AnalogOut: {},
}

BK72XX_PIN_MAP = {
    PinMap.DigitalIn: {},
    PinMap.DigitalOut: {},
    PinMap.AnalogIn: {},
    PinMap.AnalogOut: {},
}

RTL87XX_PIN_MAP = {
    PinMap.DigitalIn: {},
    PinMap.DigitalOut: {},
    PinMap.AnalogIn: {},
    PinMap.AnalogOut: {},
}
