import os

from esphome.core import CORE


def get_os_specific_path_slash() -> str:
    return "\\" if os.name == "nt" else "/"


def is_used_variable_name_correct(var_name: str) -> bool:
    legal_variable_prefixes = ["IX", "QX", "IW", "QW"]
    return any(map(lambda prefix: prefix in var_name, legal_variable_prefixes))


def get_plc_used_variables(plc_generated_code_location) -> list[str]:
    used_variables = []
    base_path = (
        CORE.relative_config_path(plc_generated_code_location)
        + get_os_specific_path_slash()
    )
    located_vars_file = open(base_path + "LOCATED_VARIABLES.h")

    for located_var in located_vars_file.readlines():
        if "__LOCATED_VAR" not in located_var:
            continue
        located_var = located_var.split("(")[1].split(")")[0]
        var_data = located_var.split(",")
        if len(var_data) < 2:
            continue
        var_name = var_data[1]
        if is_used_variable_name_correct(var_name):
            used_variables.append(var_name)

    return used_variables
