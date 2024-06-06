#include "plc.h"
#include "esphome/core/log.h"
#include "esphome/core/helpers.h"
#include "esphome/core/component.h"

extern "C" {
#include "esphome/components/plc/openplc.h"
}

namespace esphome {
namespace plc {

static const char *const TAG = "plc";

void PLC::setup() {
    set_update_interval((uint32_t)(common_ticktime__ / 1000000));

    config_init__();

    for (const auto& [pin, _] : digitalInputPinVarPairs_)
        pin->setup();

    for (const auto& [pin, _] : digitalOutputPinVarPairs_)
        pin->setup();
}

void PLC::dump_config() {
    ESP_LOGCONFIG(TAG, "PLC:");
    LOG_UPDATE_INTERVAL(this);
}

void PLC::update() {
    update_input_buffers();
    config_run__(__tick++);  //PLC Logic
    update_output_buffers();
    updateTime();
}

float PLC::get_setup_priority() const {
    return setup_priority::IO;
}

float PLC::get_loop_priority() const {
    return 20.0f;  // before other loop components and before WiFi component
}

void PLC::add_digital_input_pin(GPIOPin *pin, IEC_BOOL *plcVar)
{
    digitalInputPinVarPairs_.push_back(std::make_pair(pin, plcVar));
}

void PLC::add_digital_output_pin(GPIOPin *pin, IEC_BOOL *plcVar)
{
    digitalOutputPinVarPairs_.push_back(std::make_pair(pin, plcVar));
}

void PLC::update_input_buffers()
{
    for (const auto& [pin, plcVar] : digitalInputPinVarPairs_)
        *plcVar = pin->digital_read();
}

void PLC::update_output_buffers()
{
    for (const auto& [pin, plcVar] : digitalInputPinVarPairs_)
        pin->digital_write(*plcVar);
}

}  // plc
}  // esphome
