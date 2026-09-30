import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import light, esp32
from esphome.components.esp32 import const
from esphome import pins
from esphome.core import CORE
from esphome.const import (
    CONF_OUTPUT_ID,
    CONF_PIN,
    CONF_NUM_LEDS,
    CONF_COLOR_INTERLOCK,
    CONF_COLD_WHITE_COLOR_TEMPERATURE,
    CONF_WARM_WHITE_COLOR_TEMPERATURE,
    CONF_CONSTANT_BRIGHTNESS,
    CONF_NUMBER
)

CONF_CHANNEL_ORDER = "channel_order"
CONF_ISR_PRIORITY = "isr_priority"

# FW1906 frame: 6 bytes per IC. channel_order is a free-form permutation of
# R, G, B, C (cold white), W (warm white) and X (unused channel, always 0).
# X may sit at ANY position — e.g. mid-frame on strips where the chip's B1
# channel is not wired to an LED.
CHANNEL_ORDER_ALPHABET = "RGBCWX"


def validate_channel_order(value):
    value = cv.string_strict(value).upper()
    if len(value) != len(CHANNEL_ORDER_ALPHABET):
        raise cv.Invalid(
            f"channel_order must be exactly {len(CHANNEL_ORDER_ALPHABET)} characters, got '{value}'"
        )
    if sorted(value) != sorted(CHANNEL_ORDER_ALPHABET):
        raise cv.Invalid(
            f"channel_order must be a permutation of '{CHANNEL_ORDER_ALPHABET}' "
            f"(R, G, B, C = cold white, W = warm white, X = unused/zero channel), got '{value}'"
        )
    return value


CODEOWNERS = ["@alexbilevskiy"]
DEPENDENCIES = ["esp32"]

fw1906_ns = cg.esphome_ns.namespace("fw1906")
FW1906LightOutput = fw1906_ns.class_("FW1906LightOutput", light.AddressableLight)

def validate_rmt_usage(config):
    variant = esp32.get_esp32_variant()
    if variant == const.VARIANT_ESP32:
        max_channels = 8
    elif variant in (const.VARIANT_ESP32S2, const.VARIANT_ESP32S3):
        max_channels = 4
    elif variant in (const.VARIANT_ESP32C3, const.VARIANT_ESP32C6):
        max_channels = 2
    else:
        max_channels = 8

    if "fw1906" not in CORE.data:
        CORE.data["fw1906"] = 0
    CORE.data["fw1906"] += 1

    if CORE.data["fw1906"] > max_channels:
        raise cv.Invalid(
            f"Too many FW1906 instances ({CORE.data['fw1906']}) for {variant}. "
            f"The hardware supports a maximum of {max_channels} RMT channels."
        )

    return config

CONFIG_SCHEMA = cv.All(
    light.ADDRESSABLE_LIGHT_SCHEMA.extend({
    cv.GenerateID(CONF_OUTPUT_ID): cv.declare_id(FW1906LightOutput),
    cv.Required(CONF_PIN): pins.internal_gpio_output_pin_schema,
    cv.Required(CONF_NUM_LEDS): cv.positive_int,
    cv.Optional(CONF_CHANNEL_ORDER, default="GRBCWX"): validate_channel_order,
    cv.Optional(CONF_COLOR_INTERLOCK, default=False): cv.boolean,
    cv.Optional(CONF_COLD_WHITE_COLOR_TEMPERATURE, default="153 mireds"): cv.color_temperature,
    cv.Optional(CONF_WARM_WHITE_COLOR_TEMPERATURE, default="500 mireds"): cv.color_temperature,
    cv.Optional(CONF_CONSTANT_BRIGHTNESS, default=False): cv.boolean,
    cv.Optional("cct_transition_speed", default="3s"): cv.positive_time_period_milliseconds,
    cv.Optional("dithering", default=False): cv.boolean,
    # Advanced RMT bit timing — defaults center in the FW1906 datasheet ranges
    # (T0H 0.36us, T1H 0.72us, bit period >= 1.25us, reset >= 200us).
    # The RMT resolution is auto-detected per build target, so no clock divider
    # is exposed here.
    cv.Optional("bit0_high_ns", default=360): cv.positive_int,
    cv.Optional("bit0_low_ns", default=970): cv.positive_int,
    cv.Optional("bit1_high_ns", default=720): cv.positive_int,
    cv.Optional("bit1_low_ns", default=610): cv.positive_int,
    cv.Optional("reset_pulse_us", default=300): cv.positive_int,
    cv.Optional(CONF_ISR_PRIORITY, default=3): cv.int_range(min=1, max=3),
}).extend(cv.COMPONENT_SCHEMA),
    validate_rmt_usage
)

async def to_code(config):
    esp32.include_builtin_idf_component("esp_driver_rmt")
    pin_value = config[CONF_PIN]
    var = cg.new_Pvariable(config[CONF_OUTPUT_ID], config[CONF_NUM_LEDS], pin_value[CONF_NUMBER])
    await cg.register_component(var, config)
    await light.register_light(var, config)

    cg.add(var.set_color_interlock(config[CONF_COLOR_INTERLOCK]))
    cg.add(var.set_cold_white_temperature(config[CONF_COLD_WHITE_COLOR_TEMPERATURE]))
    cg.add(var.set_warm_white_temperature(config[CONF_WARM_WHITE_COLOR_TEMPERATURE]))
    cg.add(var.set_constant_brightness(config[CONF_CONSTANT_BRIGHTNESS]))

    order = config[CONF_CHANNEL_ORDER]
    positions = {channel: index for index, channel in enumerate(order)}
    cg.add(var.set_channel_order(
        positions["R"], positions["G"], positions["B"], positions["W"], positions["C"], positions["X"]
    ))

    if "cct_transition_speed" in config:
        cg.add(var.set_transition_speed(config["cct_transition_speed"]))
    if "dithering" in config:
        cg.add(var.set_dithering(config["dithering"]))
    if "bit0_high_ns" in config:
        cg.add(var.set_bit0_high_ns(config["bit0_high_ns"]))
    if "bit0_low_ns" in config:
        cg.add(var.set_bit0_low_ns(config["bit0_low_ns"]))
    if "bit1_high_ns" in config:
        cg.add(var.set_bit1_high_ns(config["bit1_high_ns"]))
    if "bit1_low_ns" in config:
        cg.add(var.set_bit1_low_ns(config["bit1_low_ns"]))
    if "reset_pulse_us" in config:
        cg.add(var.set_reset_pulse_us(config["reset_pulse_us"]))

    if CONF_ISR_PRIORITY in config:
        cg.add(var.set_isr_priority(config[CONF_ISR_PRIORITY]))
