# LPF Pulse Generator

Generate LPF files that pulse LEDs at a fixed interval. Useful for short-pulse / long-experiment programs that the Iris web tool cannot produce (it forces 10 s resolution for programs >12 h).

## Requirements

Python 3, NumPy, matplotlib (for PDF verification).

## Usage

1. Open `generate_pulse_lpf.py` and edit the **CONFIGURATION** section.
2. Run: `python generate_pulse_lpf.py`

Outputs `program.lpf` (for the SD card) and `program_verification.pdf` (visual check).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PULSE_INTENSITIES` | `[4095, 0]` | Per-channel intensity in GS (0–4095). Ch0=red, Ch1=green. |
| `PULSE_DURATION_S` | `1` | Pulse ON time (seconds) |
| `PULSE_INTERVAL_MIN` | `10` | Time between pulses (minutes) |
| `TOTAL_TIME_MIN` | `1440` | Experiment duration (minutes, 1440 = 24 h) |
| `TIME_STEP_S` | `1` | LPF time resolution (seconds) |
| `PLATE_MAP` | all 1s | Visual 1/0 grid to select active wells |
| `GENERATE_PDF` | `True` | Create a verification PDF |

### Plate map example

```python
#              1  2  3  4  5  6
PLATE_MAP = [
    [ 1, 1, 1, 0, 0, 0 ],   # A
    [ 1, 1, 1, 0, 0, 0 ],   # B
    [ 0, 0, 0, 0, 0, 0 ],   # C
    [ 0, 0, 0, 0, 0, 0 ],   # D
]
```
