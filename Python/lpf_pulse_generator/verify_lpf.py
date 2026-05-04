#!/usr/bin/env python3
"""
verify_lpf.py
=============
Generate a multi-page PDF verification report for a pulse LPF program.
Can be used standalone to verify an existing configuration, or called
from generate_pulse_lpf.py automatically after LPF creation.

Pages:
  1. Plate layout – which wells are active, LED intensities per channel.
  2. Zoomed time-course – first few pulses in detail for a representative well.
  3. Full time-course – entire experiment duration overview.

Requires: numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, FancyBboxPatch
from matplotlib.colors import Normalize
import matplotlib.gridspec as gridspec


def generate_verification_pdf(gsints, rows, cols, leds_per_well, intensities,
                              pulse_duration_s, interval_min, total_time_min,
                              timestep_s, active_wells, output_pdf):
    """
    Generate a PDF verification report for the pulse program.

    Parameters
    ----------
    gsints : np.ndarray
        Intensity matrix [time][row][col][channel], dtype int16.
    rows, cols : int
        Device geometry.
    leds_per_well : int
        Number of LED channels per well.
    intensities : list of int
        Configured pulse intensity per channel.
    pulse_duration_s : float
        Pulse ON duration in seconds.
    interval_min : float
        Interval between pulses in minutes.
    total_time_min : float
        Total experiment duration in minutes.
    timestep_s : float
        Time step in seconds.
    active_wells : list or None
        List of (row, col) tuples, or None for all wells.
    output_pdf : str
        Path to save the PDF.
    """

    num_steps = gsints.shape[0]
    times_min = np.arange(num_steps) * timestep_s / 60.0

    # Determine active/inactive wells
    if active_wells is None:
        wells = [(r, c) for r in range(rows) for c in range(cols)]
    else:
        wells = active_wells
    well_set = set(wells)

    # Channel labels
    ch_labels = ["Ch0 (Red/Top)", "Ch1 (Green/Bot)"] if leds_per_well == 2 else [f"Ch{i}" for i in range(leds_per_well)]
    ch_colors = ['#e41a1c', '#4daf4a', '#377eb8', '#984ea3', '#ff7f00', '#a65628'][:leds_per_well]

    with PdfPages(output_pdf) as pdf:
        # === PAGE 1: Plate Layout ===
        fig = plt.figure(figsize=(11, 8.5))
        fig.suptitle("LPF Verification Report – Plate Layout", fontsize=14, fontweight='bold', y=0.97)

        # Summary text
        summary = (
            f"Device: {rows}×{cols} wells, {leds_per_well} LEDs/well\n"
            f"Pulse intensities: {intensities} GS\n"
            f"Pulse duration: {pulse_duration_s} s | Interval: {interval_min} min | Total: {total_time_min} min\n"
            f"Time step: {timestep_s} s | Active wells: {'ALL' if active_wells is None else len(wells)}/{rows*cols}"
        )
        fig.text(0.5, 0.90, summary, ha='center', va='top', fontsize=10,
                 family='monospace', bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.8))

        # Draw plate grid
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.72])
        ax.set_xlim(-0.5, cols - 0.5)
        ax.set_ylim(rows - 0.5, -0.5)
        ax.set_aspect('equal')
        ax.set_xticks(range(cols))
        ax.set_xticklabels([str(c + 1) for c in range(cols)], fontsize=11)
        ax.set_yticks(range(rows))
        ax.set_yticklabels([chr(ord('A') + r) for r in range(rows)], fontsize=11)
        ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)
        ax.set_frame_on(False)
        ax.tick_params(length=0)

        for r in range(rows):
            for c in range(cols):
                is_active = (r, c) in well_set
                if is_active:
                    facecolor = '#d4edda'
                    edgecolor = '#28a745'
                    lw = 2
                else:
                    facecolor = '#f8f8f8'
                    edgecolor = '#cccccc'
                    lw = 1

                circle = Circle((c, r), 0.4, facecolor=facecolor, edgecolor=edgecolor, lw=lw)
                ax.add_patch(circle)

                if is_active:
                    # Show per-channel intensity inside the well
                    label_parts = []
                    for ch in range(leds_per_well):
                        if intensities[ch] > 0:
                            label_parts.append(f"{intensities[ch]}")
                        else:
                            label_parts.append("OFF")
                    label = "\n".join(label_parts)
                    ax.text(c, r, label, ha='center', va='center', fontsize=7, fontweight='bold')
                else:
                    ax.text(c, r, "OFF", ha='center', va='center', fontsize=7, color='#999999')

        # Legend
        legend_text = "  ".join([f"● {ch_labels[i]}: {intensities[i]} GS" if intensities[i] > 0 else f"○ {ch_labels[i]}: OFF" for i in range(leds_per_well)])
        ax.set_xlabel(legend_text, fontsize=10, labelpad=15)

        pdf.savefig(fig)
        plt.close(fig)

        # === PAGE 2: Zoomed Time-Course (first few pulses) ===
        fig, axes = plt.subplots(leds_per_well, 1, figsize=(11, 8.5), sharex=True)
        if leds_per_well == 1:
            axes = [axes]
        fig.suptitle("LPF Verification – Zoomed Time-Course (First Pulses)", fontsize=14, fontweight='bold')

        # Pick a representative well
        rep_well = wells[0]
        r_rep, c_rep = rep_well
        well_label = f"{chr(ord('A') + r_rep)}{c_rep + 1}"

        # Show first 3-4 pulse intervals
        zoom_end_min = min(interval_min * 3.5, total_time_min)
        zoom_mask = times_min <= zoom_end_min

        for ch_idx in range(leds_per_well):
            ax = axes[ch_idx]
            trace = gsints[zoom_mask, r_rep, c_rep, ch_idx].astype(float)
            ax.step(times_min[zoom_mask], trace, where='post',
                    color=ch_colors[ch_idx], lw=1.5, label=ch_labels[ch_idx])
            ax.set_ylabel("Intensity (GS)", fontsize=10)
            ax.set_ylim(-200, 4500)
            ax.axhline(0, color='#cccccc', lw=0.5)
            ax.legend(loc='upper right', fontsize=9)
            ax.set_title(f"Well {well_label} – {ch_labels[ch_idx]}", fontsize=11)
            ax.grid(True, alpha=0.3)

            # Annotate pulse duration and interval
            if intensities[ch_idx] > 0 and len(trace) > 0:
                # Find first pulse start
                pulse_indices = np.where(trace > 0)[0]
                if len(pulse_indices) > 0:
                    t_start = times_min[zoom_mask][pulse_indices[0]]
                    t_end = t_start + pulse_duration_s / 60.0
                    ax.axvspan(t_start, t_end, alpha=0.15, color=ch_colors[ch_idx])
                    ax.annotate(f"{pulse_duration_s}s pulse", xy=(t_start, intensities[ch_idx]),
                                xytext=(t_start + interval_min * 0.1, intensities[ch_idx] * 0.8),
                                fontsize=8, arrowprops=dict(arrowstyle='->', color='gray'))

        axes[-1].set_xlabel("Time (min)", fontsize=10)
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        pdf.savefig(fig)
        plt.close(fig)

        # === PAGE 3: Full Time-Course Overview ===
        fig, axes = plt.subplots(leds_per_well, 1, figsize=(11, 8.5), sharex=True)
        if leds_per_well == 1:
            axes = [axes]
        fig.suptitle("LPF Verification – Full Time-Course Overview", fontsize=14, fontweight='bold')

        for ch_idx in range(leds_per_well):
            ax = axes[ch_idx]
            trace = gsints[:, r_rep, c_rep, ch_idx].astype(float)

            # For long programs, downsample for plotting speed
            if num_steps > 10000:
                # Keep every Nth point but ensure pulses are visible
                # Use max-pooling over small windows
                window = max(1, num_steps // 5000)
                n_windows = num_steps // window
                trace_ds = trace[:n_windows * window].reshape(n_windows, window).max(axis=1)
                times_ds = times_min[:n_windows * window].reshape(n_windows, window).mean(axis=1)
            else:
                trace_ds = trace
                times_ds = times_min

            ax.step(times_ds, trace_ds, where='post',
                    color=ch_colors[ch_idx], lw=0.8, label=ch_labels[ch_idx])
            ax.set_ylabel("Intensity (GS)", fontsize=10)
            ax.set_ylim(-200, 4500)
            ax.axhline(0, color='#cccccc', lw=0.5)
            ax.legend(loc='upper right', fontsize=9)
            ax.set_title(f"Well {well_label} – {ch_labels[ch_idx]} (full duration)", fontsize=11)
            ax.grid(True, alpha=0.3)

            # Count pulses annotation
            n_pulses = int(np.sum(np.diff((trace > 0).astype(int)) == 1)) + (1 if trace[0] > 0 else 0)
            ax.text(0.98, 0.5, f"{n_pulses} pulses total",
                    transform=ax.transAxes, ha='right', va='center',
                    fontsize=9, color='gray', style='italic')

        # Time axis in hours if program is long
        if total_time_min >= 120:
            axes[-1].set_xlabel("Time (min)  [total: {:.1f} h]".format(total_time_min / 60), fontsize=10)
        else:
            axes[-1].set_xlabel("Time (min)", fontsize=10)

        fig.tight_layout(rect=[0, 0, 1, 0.95])
        pdf.savefig(fig)
        plt.close(fig)

    print(f"  Verification PDF: '{output_pdf}'")
