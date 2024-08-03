#include "plc.h"
#include "esphome/core/log.h"

#ifdef USE_ESP8266
#include <Arduino.h>
#include <core_esp8266_waveform.h>

static const uint8_t ADC_RESOLUTION = 10;
#endif

namespace esphome {
namespace plc {

static const char *const TAG = "plc";

void PLC::setup() {
  set_update_interval((uint32_t) (common_ticktime__ / 1000000));

  config_init__();  // PLC Logic

  for (const auto &[pin, sensor, plcVar] : digitalInputs_) {
    pin->setup();
  }

  for (const auto &[pin, sensor, plcVar] : digitalOutputs_) {
    pin->setup();
  }

  for (const auto &[pin, sensor, plcVar] : analogInputs_) {
    setup_analog_input(pin);
  }

  for (const auto &[pin, sensor, plcVar, dedup] : analogOutputs_) {
    setup_analog_output(pin);
  }
}

#ifdef USE_ESP8266
void PLC::setup_analog_input(InternalGPIOPin *pin) { pin->setup(); }
#endif

#ifdef USE_ESP8266
void PLC::setup_analog_output(InternalGPIOPin *pin) { pin->setup(); }
#endif

void PLC::dump_config() {
  ESP_LOGCONFIG(TAG, "PLC:");
  LOG_UPDATE_INTERVAL(this);

  for (const auto &[pin, sensor, plcVar] : digitalInputs_) {
    LOG_PIN("  Digital input pin: ", pin);
  }

  for (const auto &[pin, sensor, plcVar] : digitalOutputs_) {
    LOG_PIN("  Digital output pin: ", pin);
  }

  for (const auto &[pin, sensor, plcVar] : analogInputs_) {
    LOG_SENSOR("", "ADC Sensor", sensor);
    LOG_PIN("  Analog input pin: ", pin);
  }

  for (const auto &[pin, sensor, plcVar] : analogInputs_) {
    LOG_SENSOR("", "PWM Sensor", sensor);
    LOG_PIN("  Analog output pin: ", pin);
  }
}

void PLC::update() {
  update_input_buffers();
  config_run__(__tick++);  // PLC Logic
  update_output_buffers();
  updateTime();

  for (const auto &[pin, sensor, plcVar] : digitalInputs_) {
    if (sensor) {
      sensor->publish_state(*plcVar);
    }
  }

  for (const auto &[pin, sensor, plcVar] : digitalOutputs_) {
    if (sensor) {
      sensor->publish_state(*plcVar);
    }
  }

  for (const auto &[pin, sensor, plcVar] : analogInputs_) {
    if (sensor) {
      sensor->publish_state(*plcVar);
    }
  }

  for (const auto &[pin, sensor, plcVar, dedup] : analogOutputs_) {
    if (sensor) {
      sensor->publish_state(*plcVar);
    }
  }
}

float PLC::get_setup_priority() const { return setup_priority::IO; }

float PLC::get_loop_priority() const {
  return 20.0f;  // before other loop components and before WiFi component
}

void PLC::add_digital_input(GPIOPin *pin, binary_sensor::BinarySensor *sensor, IEC_BOOL *plcVar) {
  digitalInputs_.push_back(std::make_tuple(pin, sensor, plcVar));
}

void PLC::add_digital_output(GPIOPin *pin, binary_sensor::BinarySensor *sensor, IEC_BOOL *plcVar) {
  digitalOutputs_.push_back(std::make_tuple(pin, sensor, plcVar));
}

void PLC::add_analog_input(InternalGPIOPin *pin, sensor::Sensor *sensor, IEC_UINT *plcVar) {
  analogInputs_.push_back(std::make_tuple(pin, sensor, plcVar));
}

void PLC::add_analog_output(InternalGPIOPin *pin, sensor::Sensor *sensor, IEC_UINT *plcVar) {
  analogOutputs_.push_back(std::make_tuple(pin, sensor, plcVar, Deduplicator<IEC_UINT>{}));
}

void PLC::update_input_buffers() {
  for (const auto &[pin, sensor, plcVar] : digitalInputs_) {
    *plcVar = pin->digital_read();
  }

  for (const auto &[pin, sensor, plcVar] : analogInputs_) {
    auto adc_sample = get_adc_sample(pin);
    if (pin->is_inverted()) {
      adc_sample -= (1 << ADC_RESOLUTION);
    }
    *plcVar = adc_sample;
  }
}

#ifdef USE_ESP8266
uint16_t PLC::get_adc_sample(InternalGPIOPin *pin) {
  return analogRead(pin->get_pin());  // NOLINT
}
#endif

void PLC::update_output_buffers() {
  for (const auto &[pin, sensor, plcVar] : digitalOutputs_) {
    pin->digital_write(*plcVar);
  }

  for (auto &[pin, sensor, plcVar, dedup] : analogOutputs_) {
    if (dedup.next(*plcVar)) {
      float state = *plcVar / float{UINT16_MAX};
      if (pin->is_inverted()) {
        state = 1.0f - state;
      }
      enable_pwm(pin, state);
    }
  }
}

#ifdef USE_ESP8266
void PLC::enable_pwm(InternalGPIOPin *pin, float state) {
  float frequency{1000.0};  // PWM frequency is 1kHz by default
  auto total_time_us = static_cast<uint32_t>(roundf(1e6f / frequency));
  auto duty_on = static_cast<uint32_t>(roundf(total_time_us * state));
  uint32_t duty_off = total_time_us - duty_on;

  if (duty_on == 0) {
    stopWaveform(pin->get_pin());
    pin->digital_write(pin->is_inverted());
  } else if (duty_off == 0) {
    stopWaveform(pin->get_pin());
    pin->digital_write(!pin->is_inverted());
  } else {
    startWaveform(pin->get_pin(), duty_on, duty_off, 0);
  }
}
#endif

}  // namespace plc
}  // namespace esphome
