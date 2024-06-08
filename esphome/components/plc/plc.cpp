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

namespace {
void dump_config_pin_var_pairs(std::vector<std::pair<GPIOPin *, IEC_BOOL *>> digitalPinVarPairs) {
  for (const auto &[pin, plcVar] : digitalPinVarPairs) {
    LOG_PIN("  Pin: ", pin);
  }
}

void setup_pin_var_pairs(std::vector<std::pair<GPIOPin *, IEC_BOOL *>> digitalPinVarPairs) {
  for (const auto &[pin, _] : digitalPinVarPairs) {
    pin->setup();
  }
}
}  // namespace

void PLC::setup() {
  set_update_interval((uint32_t) (common_ticktime__ / 1000000));

  config_init__();

  setup_pin_var_pairs(digitalInputPinVarPairs_);
  setup_pin_var_pairs(digitalOutputPinVarPairs_);
}

void PLC::dump_config() {
  ESP_LOGCONFIG(TAG, "PLC:");
  LOG_UPDATE_INTERVAL(this);

  dump_config_pin_var_pairs(digitalInputPinVarPairs_);
  dump_config_pin_var_pairs(digitalOutputPinVarPairs_);
}

void PLC::update() {
  update_input_buffers();
  config_run__(__tick++);  // PLC Logic
  update_output_buffers();
  updateTime();
}

float PLC::get_setup_priority() const { return setup_priority::IO; }

float PLC::get_loop_priority() const {
  return 20.0f;  // before other loop components and before WiFi component
}

void PLC::add_digital_input_pin(GPIOPin *pin, IEC_BOOL *plcVar) {
  digitalInputPinVarPairs_.push_back(std::make_pair(pin, plcVar));
}

void PLC::add_digital_output_pin(GPIOPin *pin, IEC_BOOL *plcVar) {
  digitalOutputPinVarPairs_.push_back(std::make_pair(pin, plcVar));
}

void PLC::update_input_buffers() {
  for (const auto &[pin, plcVar] : digitalInputPinVarPairs_) {
    *plcVar = pin->digital_read();
  }
}

void PLC::update_output_buffers() {
  for (const auto &[pin, plcVar] : digitalOutputPinVarPairs_) {
    pin->digital_write(*plcVar);
  }
}

}  // namespace plc
}  // namespace esphome
