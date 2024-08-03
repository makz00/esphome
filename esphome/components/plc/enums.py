from enum import Enum


class IOMode(Enum):
    DIGITAL_IN = 1
    DIGITAL_OUT = 2
    ANALOG_IN = 3
    ANALOG_OUT = 4


class LocationPrefix(Enum):
    IN = "I"  # Input
    Q = "Q"  # Output
    M = "M"  # Memory


class SizePrefix(Enum):
    X = "X"  # 1 bit
    B = "B"  # 8 bit
    W = "W"  # 16 bit
    D = "D"  # 32 bit
    L = "L"  # 64 bit


ADDRESS_PREFIXES_TO_IO_MODE_MAP = {
    (LocationPrefix.IN, SizePrefix.X): IOMode.DIGITAL_IN,
    (LocationPrefix.Q, SizePrefix.X): IOMode.DIGITAL_OUT,
    (LocationPrefix.IN, SizePrefix.W): IOMode.ANALOG_IN,
    (LocationPrefix.Q, SizePrefix.W): IOMode.ANALOG_OUT,
}
