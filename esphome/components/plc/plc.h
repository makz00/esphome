#pragma once

#include <vector>
#include <utility>

#include "esphome/core/component.h"
#include "esphome/core/gpio.h"
#include "esphome/core/helpers.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/binary_sensor/binary_sensor.h"

extern "C" {
#include "esphome/components/plc/openplc.h"
}

namespace esphome {
namespace plc {

class PLC : public PollingComponent {
 public:
  void setup() override;
  void dump_config() override;
  void update() override;
  float get_setup_priority() const override;
  float get_loop_priority() const override;

  void add_digital_input(GPIOPin *pin, binary_sensor::BinarySensor *sensor, IEC_BOOL *plcVar);
  void add_digital_output(GPIOPin *pin, binary_sensor::BinarySensor *sensor, IEC_BOOL *plcVar);
  void add_analog_input(InternalGPIOPin *pin, sensor::Sensor *sensor, IEC_UINT *plcVar);
  void add_analog_output(InternalGPIOPin *pin, sensor::Sensor *sensor, IEC_UINT *plcVar);

 private:
  void update_input_buffers();
  void update_output_buffers();

  void setup_analog_input(InternalGPIOPin *pin);
  void setup_analog_output(InternalGPIOPin *pin);

  uint16_t get_adc_sample(InternalGPIOPin *pin);
  void enable_pwm(InternalGPIOPin *pin, float state);

 protected:
  std::vector<std::tuple<GPIOPin *, binary_sensor::BinarySensor *, IEC_BOOL *>> digitalInputs_;
  std::vector<std::tuple<GPIOPin *, binary_sensor::BinarySensor *, IEC_BOOL *>> digitalOutputs_;
  std::vector<std::tuple<InternalGPIOPin *, sensor::Sensor *, IEC_UINT *>> analogInputs_;
  std::vector<std::tuple<InternalGPIOPin *, sensor::Sensor *, IEC_UINT *, Deduplicator<IEC_UINT>>> analogOutputs_;

  uint32_t __tick = 0;
};

}  // namespace plc
}  // namespace esphome
