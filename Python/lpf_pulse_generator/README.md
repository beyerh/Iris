# LPF Pulse Generator

A simple, configurable Python script to generate LPF files that pulse an LED at a fixed interval.

## Default Behavior

Pulses **all wells**, channel 0 (top LED), at **max intensity (4095 GS)** for **1 second** every **10 minutes** for **24 hours**.

## Requirements

- Python 3
- NumPy

## Usage

```bash
# Run with defaults (1s pulse, every 10min, 24h, red LED at max)
python generate_pulse_lpf.py

# Custom: 2s pulse, every 5 minutes, 12 hours, red at half intensity
python generate_pulse_lpf.py --intensities 2048 0 --pulse_duration 2 --interval 5 --total_time 720

# Pulse the green LED only at intensity 2000
python generate_pulse_lpf.py --intensities 0 2000

# Pulse both LEDs simultaneously (red=4095, green=3000)
python generate_pulse_lpf.py --intensities 4095 3000

# See all options
python generate_pulse_lpf.py --help
```

## Configuration

You can either:
1. Pass command-line arguments (shown above), or
2. Edit the `CONFIGURATION` section at the top of `generate_pulse_lpf.py` directly.

### Key Parameters

| Parameter | CLI flag | Default | Description |
|-----------|----------|---------|-------------|
| Intensities | `--intensities` | 4095 0 | Pulse intensity per channel in GS (0–4095). One value per LED. |
| Pulse duration | `--pulse_duration` | 1 | How long the LED stays ON per pulse (seconds) |
| Interval | `--interval` | 10 | Time between pulse starts (minutes) |
| Total time | `--total_time` | 1440 | Total experiment duration (minutes); 1440 = 24h |
| Time step | `--timestep` | 1 | LPF time resolution in seconds |
| Output file | `--output` | program.lpf | Output filename |

### LED Channel Examples

The `--intensities` flag takes one value per LED channel (space-separated):

```bash
--intensities 4095 0       # red only at max
--intensities 0 2000       # green only at 2000 GS
--intensities 4095 4095    # both LEDs at max
--intensities 2000 1000    # red at 2000, green at 1000
```

### Selecting Specific Wells

By default all wells are pulsed. To pulse only specific wells, edit the `ACTIVE_WELLS` variable in the script:

```python
# Only pulse wells A1 and B3 (0-indexed row, col)
ACTIVE_WELLS = [(0, 0), (1, 2)]
```

Or to configure per-channel intensities directly in the script:

```python
PULSE_INTENSITIES = [4095, 4095]   # both LEDs at max during pulse
```

## Output

The script produces a `program.lpf` file (~8 MB for 24h at 1s resolution) that can be placed on the SD card for the LPA hardware.

## Why not use Iris or the notebook?

- **Iris web tool**: Automatically increases time step to 10s for programs >12h, making 1-second pulses impossible.
- **ProduceLPFDemo.ipynb**: Demonstrates PWM but is complex and not easily configurable for this simple use case.
- **This script**: Directly addresses the "short pulse, long experiment" scenario with clear parameters.
