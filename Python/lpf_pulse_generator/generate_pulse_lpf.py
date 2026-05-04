#!/usr/bin/env python3
"""
generate_pulse_lpf.py
=====================
Generate an LPF file that pulses an LED at a given intensity for a specified
duration, repeated at a fixed interval, over a total experiment time.

Default: 1-second pulse every 10 minutes for 24 hours on all wells (channel 0).

Usage:
    1. Edit the CONFIGURATION section below.
    2. Run:  python generate_pulse_lpf.py
"""

import sys
import os
import numpy as np

# ---------------------------------------------------------------------------
# CONFIGURATION — edit these values, then run the script
# ---------------------------------------------------------------------------

# Device geometry (standard 24-well LPA)
ROW_NUM = 4
COL_NUM = 6
LEDS_PER_WELL = 2

# Pulse parameters
PULSE_DURATION_S = 1         # Pulse ON duration in seconds.
PULSE_INTERVAL_MIN = 10      # Time between pulse starts, in minutes.
TOTAL_TIME_MIN = 1440        # Total experiment duration in minutes (1440 = 24h).

# LED intensities during pulse, per channel.
# For standard LPA: channel 0 = top LED (red), channel 1 = bottom LED (green).
# Set a channel to 0 to keep it OFF. Set to None to leave it unchanged.
# Examples:
#   [4095, 0]      -> pulse only red at max
#   [0, 2000]      -> pulse only green at 2000 GS
#   [4095, 4095]   -> pulse both LEDs simultaneously at max
#   [2000, 1000]   -> pulse red at 2000, green at 1000
PULSE_INTENSITIES = [4095, 0]  # Greyscale units [0, 4095] per channel.

# Plate map: visual well selection.
# 1 = active (pulsed), 0 = inactive (stays dark).
# Rows = A-D (top to bottom), Columns = 1-6 (left to right).
#
#              1  2  3  4  5  6
PLATE_MAP = [
    [ 1, 1, 1, 1, 1, 1 ],   # A
    [ 1, 1, 1, 1, 1, 1 ],   # B
    [ 1, 1, 1, 1, 1, 1 ],   # C
    [ 1, 1, 1, 1, 1, 1 ],   # D
]

# Time step for the LPF file in seconds.
# 1 s allows 1-second resolution. Smaller values increase file size.
TIME_STEP_S = 1

# Output filename
OUTPUT_FILE = "program.lpf"

# Generate a verification PDF alongside the LPF file.
GENERATE_PDF = True

# ---------------------------------------------------------------------------
# END CONFIGURATION
# ---------------------------------------------------------------------------


def plate_map_to_wells(plate_map):
    """Convert a PLATE_MAP grid to a list of (row, col) tuples.
    Returns None if all wells are active (equivalent to 'all')."""
    rows = len(plate_map)
    cols = len(plate_map[0]) if rows > 0 else 0
    wells = []
    for r in range(rows):
        if len(plate_map[r]) != cols:
            raise ValueError(f"PLATE_MAP row {r} has {len(plate_map[r])} columns, expected {cols}.")
        for c in range(cols):
            if plate_map[r][c]:
                wells.append((r, c))
    if len(wells) == rows * cols:
        return None  # all wells active
    if len(wells) == 0:
        raise ValueError("PLATE_MAP has no active wells (all zeros).")
    return wells



def generate_pulse_lpf(rows, cols, leds_per_well, intensities, pulse_duration_s,
                       interval_min, total_time_min, timestep_s,
                       active_wells, output_file, generate_pdf=True):
    """Build the intensity matrix and write the LPF file."""

    # Add the parent directory to path so we can import LPFEncoder
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, parent_dir)
    import LPFEncoder as lpfe

    # Derived values
    timestep_ms = int(timestep_s * 1000)
    total_time_ms = int(total_time_min * 60 * 1000)
    num_steps = total_time_ms // timestep_ms + 1
    interval_steps = int(interval_min * 60 / timestep_s)
    pulse_steps = max(1, int(pulse_duration_s / timestep_s))

    # Validate intensities list
    if len(intensities) != leds_per_well:
        raise ValueError(f"intensities list must have {leds_per_well} entries (one per LED), got {len(intensities)}.")
    for i, v in enumerate(intensities):
        if v < 0 or v > 4095:
            raise ValueError(f"Intensity for channel {i} must be in [0, 4095], got {v}.")
    if pulse_steps > interval_steps:
        raise ValueError("Pulse duration exceeds the interval between pulses.")

    # Determine which channels are active (intensity > 0)
    active_channels = [(ch, val) for ch, val in enumerate(intensities) if val > 0]

    # Print summary
    print("=" * 60)
    print("LPF Pulse Generator")
    print("=" * 60)
    print(f"  Device:            {rows} x {cols} wells, {leds_per_well} LEDs/well")
    print(f"  Total channels:    {rows * cols * leds_per_well}")
    print(f"  Pulse intensities: {intensities} GS (per channel)")
    print(f"  Active LEDs:       {[f'ch{ch}={val}' for ch, val in active_channels] if active_channels else 'NONE'}")
    print(f"  Pulse duration:    {pulse_duration_s} s ({pulse_steps} time steps)")
    print(f"  Pulse interval:    {interval_min} min ({interval_steps} time steps)")
    print(f"  Total time:        {total_time_min} min ({num_steps} time steps)")
    print(f"  Time step:         {timestep_s} s ({timestep_ms} ms)")
    print(f"  Active wells:      {'ALL' if active_wells is None else active_wells}")
    est_size_mb = (32 + num_steps * rows * cols * leds_per_well * 2) / (1024 * 1024)
    print(f"  Est. file size:    {est_size_mb:.1f} MB")
    print(f"  Output file:       {output_file}")
    print("=" * 60)

    # Build intensity matrix: [time][row][col][channel]
    gsints = np.zeros((num_steps, rows, cols, leds_per_well), dtype=np.int16)

    # Determine which wells are active
    if active_wells is None:
        wells = [(r, c) for r in range(rows) for c in range(cols)]
    else:
        wells = active_wells

    # Apply pulses
    num_pulses = 0
    t = 0
    while t < num_steps:
        pulse_end = min(t + pulse_steps, num_steps)
        for (r, c) in wells:
            for ch, val in active_channels:
                gsints[t:pulse_end, r, c, ch] = val
        num_pulses += 1
        t += interval_steps

    print(f"  Total pulses:      {num_pulses} per well")

    # Device params for LPFEncoder
    dp = {
        'channelNum': rows * cols * leds_per_well,
        'numSteps': num_steps,
        'timeStep': timestep_ms,
    }

    # Write LPF
    lpfe.LPFEncoder(gsints, dp, output_file)
    actual_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"\n  SUCCESS: wrote '{output_file}' ({actual_size_mb:.1f} MB)")

    # Generate verification PDF
    if generate_pdf:
        from verify_lpf import generate_verification_pdf
        pdf_path = os.path.splitext(output_file)[0] + "_verification.pdf"
        generate_verification_pdf(
            gsints=gsints,
            rows=rows,
            cols=cols,
            leds_per_well=leds_per_well,
            intensities=intensities,
            pulse_duration_s=pulse_duration_s,
            interval_min=interval_min,
            total_time_min=total_time_min,
            timestep_s=timestep_s,
            active_wells=active_wells,
            output_pdf=pdf_path,
        )


def main():
    generate_pulse_lpf(
        rows=ROW_NUM,
        cols=COL_NUM,
        leds_per_well=LEDS_PER_WELL,
        intensities=PULSE_INTENSITIES,
        pulse_duration_s=PULSE_DURATION_S,
        interval_min=PULSE_INTERVAL_MIN,
        total_time_min=TOTAL_TIME_MIN,
        timestep_s=TIME_STEP_S,
        active_wells=plate_map_to_wells(PLATE_MAP),
        output_file=OUTPUT_FILE,
        generate_pdf=GENERATE_PDF,
    )


if __name__ == "__main__":
    main()
