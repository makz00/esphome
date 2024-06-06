#pragma once

#include <vector>
#include <utility>

#include "esphome/core/automation.h"
#include "esphome/core/component.h"
#include "esphome/core/gpio.h"

extern "C" {
#include "esphome/components/plc/openplc.h"
}

namespace esphome {
namespace plc {

class PLC : public PollingComponent
{
public:
    void setup() override;
    void dump_config() override;
    void update() override;
    float get_setup_priority() const override;
    float get_loop_priority() const override;

    void add_digital_input_pin(GPIOPin *pin, IEC_BOOL *plcVar);
    void add_digital_output_pin(GPIOPin *pin, IEC_BOOL *plcVar);

private:
    void update_input_buffers();
    void update_output_buffers();

protected:
    std::vector<std::pair<GPIOPin *, IEC_BOOL *>> digitalInputPinVarPairs_;
    std::vector<std::pair<GPIOPin *, IEC_BOOL *>> digitalOutputPinVarPairs_;

    uint32_t __tick = 0;
};

}  // plc
}  // esphome
