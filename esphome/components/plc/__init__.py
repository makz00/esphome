import os

import esphome.codegen as cg
import esphome.config_validation as cv

from esphome.const import (
    CONF_ID,
    CONF_PIN,
    CONF_NUMBER,
    CONF_MODE,
    CONF_INPUT,
    CONF_OUTPUT,
    CONF_ANALOG,
    PLATFORM_ESP32,
    PLATFORM_ESP8266,
    PLATFORM_RP2040,
    PLATFORM_BK72XX,
    PLATFORM_RTL87XX,
)
from esphome import pins
from esphome.core import CORE, coroutine, EsphomeError

from .plc_variables import get_plc_used_variables
from .plc_pin_map import (
    PinMap,
    ESP8266_PIN_MAP,
    ESP32_PIN_MAP,
    RP2040_PIN_MAP,
    BK72XX_PIN_MAP,
    RTL87XX_PIN_MAP,
)
from esphome.helpers import copy_file_if_changed, walk_files


CODEOWNERS = ["@makz00"]
C_LANG_HEADERS = ["openplc.h"]

# Constant values section BEGIN

CONF_PLC_VAR_NAME = "plc_variable_name"
CONF_PLC_VAR_TO_PIN_MAP = "plc_variable_to_pin_map"
CONF_MATIEC_INCLUDES_LOCATION = "matiec_includes_location"
CONF_PLC_GENERATED_CODE_LOCATION = "plc_generated_code_location"

PLATFORM_TO_PINS_MAP = {
    PLATFORM_ESP8266: ESP8266_PIN_MAP,
    PLATFORM_ESP32: ESP32_PIN_MAP,
    PLATFORM_RP2040: RP2040_PIN_MAP,
    PLATFORM_BK72XX: BK72XX_PIN_MAP,
    PLATFORM_RTL87XX: RTL87XX_PIN_MAP,
}

# Constant values section END


PLC_NS = cg.esphome_ns.namespace("plc")
PLC = PLC_NS.class_("PLC", cg.PollingComponent)
IEC_BOOL = cg.esphome_ns.class_("IEC_BOOL")


def update_defaults_with_pins(defaults_list, spec_var_to_pin, input, analog):
    for variable_name, pin_number in spec_var_to_pin.items():
        defaults_list.append(
            {
                CONF_PLC_VAR_NAME: variable_name,
                CONF_PIN: {
                    CONF_NUMBER: pin_number,
                    CONF_MODE: {
                        CONF_INPUT: "true" if input else "false",
                        CONF_OUTPUT: "false" if input else "true",
                        CONF_ANALOG: "true" if analog else "false",
                    },
                },
            }
        )


def get_all_defaults_with_pins(var_to_pin):
    result = []
    update_defaults_with_pins(result, var_to_pin[PinMap.DigitalIn], True, False)
    update_defaults_with_pins(result, var_to_pin[PinMap.DigitalOut], False, False)
    update_defaults_with_pins(result, var_to_pin[PinMap.AnalogIn], True, True)
    update_defaults_with_pins(result, var_to_pin[PinMap.AnalogOut], False, False)
    return result


def get_default_var_to_pin_map():
    return get_all_defaults_with_pins(PLATFORM_TO_PINS_MAP[CORE.target_platform])


CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(PLC),
        cv.Required(CONF_MATIEC_INCLUDES_LOCATION): cv.directory,
        cv.Required(CONF_PLC_GENERATED_CODE_LOCATION): cv.directory,
        cv.Optional(
            CONF_PLC_VAR_TO_PIN_MAP, default=get_default_var_to_pin_map()
        ): cv.All(
            cv.ensure_list(
                {
                    cv.Required(CONF_PLC_VAR_NAME): cv.declare_id(IEC_BOOL),
                    cv.Required(CONF_PIN): pins.gpio_output_pin_schema,
                }
            ),
            cv.Length(min=0, max=32),
        ),
    }
).extend(cv.COMPONENT_SCHEMA)


def get_plc_var_to_pin_entry(plc_var, plc_var_to_pin_map):
    for var_to_pin_entry in plc_var_to_pin_map:
        # Cast to str() as here we have class ID
        if str(var_to_pin_entry[CONF_PLC_VAR_NAME]) == plc_var:
            return var_to_pin_entry


def get_plc_variable_expression(plc_var_id):
    return cg.extern_Pvariable(plc_var_id)


def is_digital_input_variable(plc_var_name):
    return (
        str(plc_var_name)
        in PLATFORM_TO_PINS_MAP[CORE.target_platform][PinMap.DigitalIn]
    )


def add_digital_pin_to_plc(var, pin, plc_var):
    if is_digital_input_variable(plc_var):
        cg.add(var.add_digital_input_pin(pin, plc_var))
    else:
        cg.add(var.add_digital_output_pin(pin, plc_var))


def extract_configured_plc_vars(plc_var_to_pin_map):
    return [
        str(var_to_pin_entry[CONF_PLC_VAR_NAME])
        for var_to_pin_entry in plc_var_to_pin_map
    ]


def copy_file(path, basename):
    parts = basename.split(os.path.sep)
    dst = CORE.relative_src_path(*parts)
    copy_file_if_changed(path, dst)


@coroutine
async def add_directory(dir_path):
    path = CORE.relative_config_path(dir_path)
    if os.path.isdir(path):
        for p in walk_files(path):
            basename = os.path.relpath(p, os.path.dirname(path))
            copy_file(p, basename)


async def to_code(config):
    CORE.add_job(add_directory, config[CONF_MATIEC_INCLUDES_LOCATION])
    CORE.add_job(add_directory, config[CONF_PLC_GENERATED_CODE_LOCATION])

    cg.add_build_flag(f"-I src/{str(config[CONF_MATIEC_INCLUDES_LOCATION])}")
    cg.add_build_flag(f"-I src/{str(config[CONF_PLC_GENERATED_CODE_LOCATION])}")

    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    plc_var_to_pin_map = config[CONF_PLC_VAR_TO_PIN_MAP]
    configured_plc_vars = extract_configured_plc_vars(plc_var_to_pin_map)

    for plc_var_name in get_plc_used_variables(
        config[CONF_PLC_GENERATED_CODE_LOCATION]
    ):
        if plc_var_name not in configured_plc_vars:
            raise EsphomeError(
                f"Pin has not been configured for PLC variable '{plc_var_name}'"
            )

        var_to_pin_config = get_plc_var_to_pin_entry(plc_var_name, plc_var_to_pin_map)

        pin = await cg.gpio_pin_expression(var_to_pin_config[CONF_PIN])
        plc_var = get_plc_variable_expression(var_to_pin_config[CONF_PLC_VAR_NAME])

        add_digital_pin_to_plc(var, pin, plc_var)
