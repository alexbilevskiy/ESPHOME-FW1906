# ESPHome FW1906 External Component

ESPHome external component for **FW1906** 6-channel RGB+CCT LED chips: RGB + Cold White + Warm White + 1 unused channel, 6-byte frame per IC.

This is a derivative of [ESPHOME-WS2805](https://github.com/babeinlovexd/ESPHOME-WS2805) by [@Babeinlovexd](https://github.com/babeinlovexd) (CC BY-NC-SA 4.0). The code is adapted from it — **all options, features, examples and documentation live in the upstream README**, see it first. The only thing that matters here:

## `channel_order`

On FW1906 strips one of the six channels is not wired to an LED, and its position in the frame is **not** always the last byte. WLED (and the upstream component's fixed orders) always zero the last byte and don't work on such strips.

Here `channel_order` is a free-form permutation of:

| Letter | Logical channel |
|--------|-----------------|
| `R`    | Red             |
| `G`    | Green           |
| `B`    | Blue            |
| `C`    | Cold white      |
| `W`    | Warm white      |
| `X`    | Unused channel  |

To figure out your strip's order: set the default `GRBCWX`, pick single colors in Home Assistant and note which LED color actually lights up — each probe tells you where that logical channel landed. After a few probes the full physical mapping is known; write the order reversed. Example: a strip probing as `[warm white, unused, green, red, blue, cold white]` → `channel_order: WXGRBC`.

The validator enforces exactly one of each letter, so a bad order fails at config validation.

## Usage

```yaml
external_components:
  - source:
      type: git
      url: https://github.com/alexbilevskiy/ESPHOME-FW1906
      ref: main
    components: [ fw1906 ]

light:
  - platform: fw1906
    name: "FW1906 Strip"
    pin: GPIO4
    num_leds: 60
    channel_order: WXGRBC
```

Other differences from upstream: timing defaults follow the FW1906 datasheet (360/970/720/610 ns, reset 300 µs) and the WS2805 `fdin_pin` backup data line is not supported (the FW1906 has a single data input).

## License

[CC BY-NC-SA 4.0](LICENSE) — inherited from the upstream project.
