import os
import re

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor, binary_sensor

from esphome.const import (
    CONF_ID,
    CONF_PIN,
    CONF_INPUT,
    CONF_OUTPUT,
    CONF_ANALOG,
    CONF_MODE,
)
from esphome import pins
from esphome.core import CORE, coroutine, EsphomeError

from esphome.helpers import copy_file_if_changed, walk_files
from .enums import IOMode, LocationPrefix, SizePrefix
from .plc_variables import get_located_variables


CODEOWNERS = ["@makz00"]
AUTO_LOAD = ["sensor", "binary_sensor"]
C_LANG_HEADERS = ["openplc.h"]
GENERATED_RESOURCES = []

CONF_MATIEC_INCLUDES_LOCATION = "matiec_includes_location"
CONF_PLC_GENERATED_CODE_LOCATION = "plc_generated_code_location"

CONF_PHYSICAL_ADDRESSING = "physical_addressing"
CONF_DIGITAL_IN = "digital_in"
CONF_DIGITAL_OUT = "digital_out"
CONF_ANALOG_IN = "analog_in"
CONF_ANALOG_OUT = "analog_out"
CONF_LOCATION = "location"

PLC_NS = cg.esphome_ns.namespace("plc")
PLC = PLC_NS.class_("PLC", cg.PollingComponent)
IEC_BOOL = cg.esphome_ns.class_("IEC_BOOL")
IEC_UINT = cg.esphome_ns.class_("IEC_UINT")

DIGITAL_LOCATION_PATTERN = re.compile(r"(%)(I|Q|M)(X)([0-9]+)(\.)([0-9])")
LOCATION_PATTERN = re.compile(r"(%)(I|Q|M)(B|W|D|L)([0-9]+)")


def validate_digital_location(
    most_significant_addr_part: str, least_significant_addr_part: str
) -> None:
    if int(most_significant_addr_part) > 1023:
        raise cv.Invalid(
            "Most significant path of difital location must be no more than 1023."
        )
    if int(least_significant_addr_part) > 7:
        raise cv.Invalid(
            "Least significant path of difital location must be in range 0 to 7."
        )


def validate_location(most_significant_addr_part: str) -> None:
    if int(most_significant_addr_part) > 31:
        # Maximum 32 (for no reason) addresses can be set for all platforms
        raise cv.Invalid(
            "Must be no more than the maximum memory location address for your platform."
        )


# Generate allowed ID according to C/C++ language. ID have to be same as MatIEC generated IDs, so
# '%' is replaced with '__' and '.' is replaced with '_'
def transform_location_to_allowed_id(value):
    if match := DIGITAL_LOCATION_PATTERN.fullmatch(value):
        most_significant_part = match[4]
        least_significant_part = match[6]
        validate_digital_location(most_significant_part, least_significant_part)
        return re.sub(DIGITAL_LOCATION_PATTERN, r"__\2\3\4_\6", value)
    if match := LOCATION_PATTERN.fullmatch(value):
        most_significant_part = match[4]
        validate_location(most_significant_part)
        return re.sub(LOCATION_PATTERN, r"__\2\3\4", value)
    raise cv.Invalid("Address pattern not found")


def validate_address_prefixes(
    value: str, location: LocationPrefix, size: SizePrefix
) -> None:
    for pattern in [DIGITAL_LOCATION_PATTERN, LOCATION_PATTERN]:
        if match := pattern.fullmatch(value):
            location_prefix = match[2]
            size_prefix = match[3]
            if location != LocationPrefix(location_prefix):
                raise cv.Invalid(
                    f"Location prefix must be '{location}',"
                    " but it is '{location_prefix}' for address '{value}'"
                )
            if size != SizePrefix(size_prefix):
                raise cv.Invalid(
                    f"Size prefix must be '{size}',"
                    " but it is '{size_prefix}' for address '{value}'"
                )
            return
    raise cv.Invalid("Address pattern not found")


def declare_address_id(type, expected_location, expected_size):
    def validator(value):
        validate_address_prefixes(value, expected_location, expected_size)
        identifier = transform_location_to_allowed_id(value)
        return cv.declare_id(type)(identifier)

    return validator


def valid_pin_mode(required_options):
    def validator(value):
        mode = value[CONF_MODE]
        for conf_option, expected_value in required_options.items():
            if (conf_option not in mode) or (mode[conf_option] != expected_value):
                raise cv.Invalid(
                    f"For this type of IO the option '{conf_option}' "
                    f"must be set to '{expected_value}'"
                )
        return value

    return validator


def valid_plc_pin(io_mode):
    required_options = {
        IOMode.DIGITAL_IN: {CONF_INPUT: True},
        IOMode.DIGITAL_OUT: {CONF_OUTPUT: True},
        IOMode.ANALOG_IN: {CONF_INPUT: True, CONF_ANALOG: True},
        IOMode.ANALOG_OUT: {CONF_OUTPUT: True},
    }[io_mode]

    return cv.All(
        pins.gpio_pin_schema(required_options), valid_pin_mode(required_options)
    )


def get_located_variable_schema(io_mode):
    arguments_list = {
        IOMode.DIGITAL_IN: [IEC_BOOL, LocationPrefix.IN, SizePrefix.X],
        IOMode.DIGITAL_OUT: [IEC_BOOL, LocationPrefix.Q, SizePrefix.X],
        IOMode.ANALOG_IN: [IEC_UINT, LocationPrefix.IN, SizePrefix.W],
        IOMode.ANALOG_OUT: [IEC_UINT, LocationPrefix.Q, SizePrefix.W],
    }[io_mode]

    return {
        cv.Required(CONF_LOCATION): declare_address_id(*arguments_list),
        cv.Required(CONF_PIN): valid_plc_pin(io_mode),
    }


CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(PLC),
        cv.Required(CONF_MATIEC_INCLUDES_LOCATION): cv.directory,
        cv.Required(CONF_PLC_GENERATED_CODE_LOCATION): cv.directory,
        cv.Optional(CONF_PHYSICAL_ADDRESSING): {
            cv.Optional(CONF_DIGITAL_IN): cv.ensure_list(
                binary_sensor.BINARY_SENSOR_SCHEMA.extend(
                    get_located_variable_schema(IOMode.DIGITAL_IN)
                )
            ),
            cv.Optional(CONF_DIGITAL_OUT): cv.ensure_list(
                binary_sensor.BINARY_SENSOR_SCHEMA.extend(
                    get_located_variable_schema(IOMode.DIGITAL_OUT)
                )
            ),
            cv.Optional(CONF_ANALOG_IN): cv.ensure_list(
                sensor.SENSOR_SCHEMA.extend(
                    get_located_variable_schema(IOMode.ANALOG_IN)
                )
            ),
            cv.Optional(CONF_ANALOG_OUT): cv.ensure_list(
                sensor.SENSOR_SCHEMA.extend(
                    get_located_variable_schema(IOMode.ANALOG_OUT)
                )
            ),
        },
    }
).extend(cv.COMPONENT_SCHEMA)


def copy_file(path, resource_dir_name):
    file_name = os.path.basename(path)
    dst = CORE.relative_src_path(
        "esphome", "components", "plc", resource_dir_name, file_name
    )
    copy_file_if_changed(path, dst)
    GENERATED_RESOURCES.append(f"{resource_dir_name}/{file_name}")


@coroutine
async def add_directory(src_dir_path, resource_dir_name):
    # DIR location is relative to YAML configuration. The goal is to pass absolute path. Then below line will be redundant
    path = CORE.relative_config_path(src_dir_path)
    # When it will not be dependent on YAML config, the check is not needed as user will not influence on the name
    if os.path.isdir(path):
        for file in walk_files(path):
            copy_file(file, resource_dir_name)


def get_located_variable_config(io_mode, plc_used_var_name, config):
    if physical_addressing_config := config.get(CONF_PHYSICAL_ADDRESSING):
        conf_mode = {
            IOMode.DIGITAL_IN: CONF_DIGITAL_IN,
            IOMode.DIGITAL_OUT: CONF_DIGITAL_OUT,
            IOMode.ANALOG_IN: CONF_ANALOG_IN,
            IOMode.ANALOG_OUT: CONF_ANALOG_OUT,
        }[io_mode]
        if physical_addressing_mode_config := physical_addressing_config.get(conf_mode):
            for sensor_config in physical_addressing_mode_config:
                # MatIEC generated variable must match with this PLC component mangled variable
                if str(sensor_config[CONF_LOCATION]) == plc_used_var_name:
                    return sensor_config
    return None


RESOURCE_PLC_LIB = "plc_lib"
RESOURCE_PLC_CODE = "plc_code"


async def to_code(config):
    CORE.add_job(add_directory, config[CONF_MATIEC_INCLUDES_LOCATION], RESOURCE_PLC_LIB)
    CORE.add_job(
        add_directory, config[CONF_PLC_GENERATED_CODE_LOCATION], RESOURCE_PLC_CODE
    )

    cg.add_build_flag(f"-I src/esphome/components/plc/{RESOURCE_PLC_LIB}")
    cg.add_build_flag(f"-I src/esphome/components/plc/{RESOURCE_PLC_CODE}")

    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    plc_methods_map = {
        IOMode.DIGITAL_IN: var.add_digital_input,
        IOMode.DIGITAL_OUT: var.add_digital_output,
        IOMode.ANALOG_IN: var.add_analog_input,
        IOMode.ANALOG_OUT: var.add_analog_output,
    }

    plc_code_dir = config[CONF_PLC_GENERATED_CODE_LOCATION]

    for io_mode, located_var_name in get_located_variables(plc_code_dir):
        located_var = get_located_variable_config(io_mode, located_var_name, config)
        if located_var is None:
            raise EsphomeError(f"Pin must be configured for: '{located_var_name}'")

        pin_config = located_var[CONF_PIN]
        pin = await cg.gpio_pin_expression(pin_config)

        if io_mode in [IOMode.DIGITAL_IN, IOMode.DIGITAL_OUT]:
            sens = await binary_sensor.new_binary_sensor(located_var)
        else:
            sens = await sensor.new_sensor(located_var)

        plc_var = cg.extern_Pvariable(located_var[CONF_LOCATION])

        cg.add(plc_methods_map[io_mode](pin, sens, plc_var))
