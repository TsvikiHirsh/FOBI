#!/usr/bin/env python3
"""
Verification Script for FOBI Bug Fixes
=======================================

Run this script to verify that both bugs are fixed:
1. Filter kernel array broadcasting error
2. Empty plots due to incorrect wavelength range

Usage:
    python verify_fixes.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import fobi

print("=" * 70)
print("FOBI Bug Fix Verification")
print("=" * 70)

# Generate test data
np.random.seed(42)
L = 9
tmax = 10000
nrep = 8
nbins = 1000 * nrep
t = np.linspace(0, tmax, nbins)

# Create realistic transmission with Bragg edges
wavelength_true = 3.956 * (t / 1000) / L
edges = [(2.027, 0.10, 0.25), (2.866, 0.12, 0.20), (4.050, 0.15, 0.30)]
transmission_true = np.ones_like(wavelength_true) * 0.6
for pos, width, height in edges:
    transmission_true += height / (1 + np.exp(-(wavelength_true - pos) / width))

openbeam_base = np.ones_like(t) * 1000
openbeam = openbeam_base + np.random.randn(len(t)) * 0.02 * openbeam_base
signal_base = transmission_true * openbeam_base
signal = signal_base + np.random.randn(len(t)) * 0.02 * signal_base

print("\nTest Data Generated:")
print(f"  Time range: [0, {tmax}] µs")
print(f"  Expected wavelength range: [0, {3.956 * tmax/1000/L:.3f}] Å")
print(f"  Bragg edges at: 2.027, 2.866, 4.050 Å")

# ============================================================================
# BUG FIX 1: Test all filter types (previously crashed)
# ============================================================================
print("\n" + "=" * 70)
print("Testing Bug Fix #1: Filter Kernel Array Broadcasting")
print("=" * 70)

filters = ['none', 'LowPass', 'LowPassBu', 'LowPassGa']
all_filters_work = True

for filt in filters:
    try:
        result = (fobi.Workflow
            .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
            .interpolate(tmax=tmax, nrep=nrep)
            .convolve(chopper="POLDI", noise_level=0.1, filter_type=filt)
            .reconstruct())
        print(f"  ✓ Filter '{filt:12s}' works! ({len(result.transmission)} points)")
    except Exception as e:
        print(f"  ✗ Filter '{filt:12s}' FAILED: {e}")
        all_filters_work = False

if all_filters_work:
    print("\n✅ Bug Fix #1: SUCCESS - All filters work correctly!")
else:
    print("\n❌ Bug Fix #1: FAILED - Some filters still broken!")

# ============================================================================
# BUG FIX 2: Test wavelength range and plot visibility
# ============================================================================
print("\n" + "=" * 70)
print("Testing Bug Fix #2: Wavelength Range and Plot Visibility")
print("=" * 70)

result = (fobi.Workflow
    .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
    .interpolate(tmax=tmax, nrep=nrep)
    .convolve(chopper="POLDI", noise_level=0.1)
    .reconstruct())

print(f"\nWavelength Calculation:")
print(f"  Reconstructed wavelength range: [{result.wavelength.min():.3f}, {result.wavelength.max():.3f}] Å")
print(f"  Expected wavelength range:      [0.000, {3.956 * tmax/1000/L:.3f}] Å")

wavelength_correct = result.wavelength.max() > 4.0
if wavelength_correct:
    print(f"  ✓ Wavelength range is correct!")
else:
    print(f"  ✗ Wavelength range is too small - plots will be empty!")

# Check data visibility in typical plot range
visible_range = (2, 6)  # Typical Bragg edge viewing range
in_range = (result.wavelength >= visible_range[0]) & (result.wavelength <= visible_range[1])
num_visible = in_range.sum()

print(f"\nPlot Visibility Check:")
print(f"  Typical plot range: {visible_range} Å")
print(f"  Data points in range: {num_visible} / {len(result.wavelength)}")

plots_will_work = num_visible > 100
if plots_will_work:
    print(f"  ✓ Sufficient data points - plots will show content!")
else:
    print(f"  ✗ Insufficient data points - plots will appear empty!")

# Create actual plot
fig, ax = plt.subplots(figsize=(12, 6))

# Plot true transmission
true_trans_interp = np.interp(result.wavelength, wavelength_true, transmission_true)
ax.plot(result.wavelength, true_trans_interp, 'k-', linewidth=2.5,
        label='True Transmission', alpha=0.7)

# Plot reconstruction
ax.plot(result.wavelength, result.transmission, 'r-', linewidth=2,
        label='FOBI Reconstruction', alpha=0.8)

# Mark Bragg edges
for edge_pos, _, _ in edges:
    ax.axvline(edge_pos, color='gray', linestyle='--', alpha=0.5)
    ax.text(edge_pos, ax.get_ylim()[1] * 0.95, f'{edge_pos:.3f} Å',
            ha='center', fontsize=9, color='gray')

ax.set_xlabel('Wavelength (Å)', fontsize=12)
ax.set_ylabel('Transmission', fontsize=12)
ax.set_title('FOBI Reconstruction: Verification Test', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
ax.set_xlim(1.5, 5)

plt.tight_layout()
plt.savefig('verification_plot.png', dpi=150, bbox_inches='tight')

print(f"\nPlot saved to: verification_plot.png")
print(f"  X-axis range: {ax.get_xlim()}")
print(f"  Y-axis range: {ax.get_ylim()}")

if plots_will_work:
    print(f"  ✓ Plot should show clear Bragg edges!")
else:
    print(f"  ✗ Plot may appear empty!")

if wavelength_correct and plots_will_work:
    print("\n✅ Bug Fix #2: SUCCESS - Wavelength and plots work correctly!")
else:
    print("\n❌ Bug Fix #2: FAILED - Wavelength or plots still broken!")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)

overall_success = all_filters_work and wavelength_correct and plots_will_work

print(f"\nBug Fix #1 (Filters):      {'✅ PASS' if all_filters_work else '❌ FAIL'}")
print(f"Bug Fix #2 (Wavelength):   {'✅ PASS' if wavelength_correct else '❌ FAIL'}")
print(f"Bug Fix #2 (Plot Visibility): {'✅ PASS' if plots_will_work else '❌ FAIL'}")

print("\n" + "=" * 70)
if overall_success:
    print("🎉 ALL BUGS FIXED - FOBI IS WORKING CORRECTLY! 🎉")
    print("=" * 70)
    print("\nYou can now:")
    print("  • Run the tutorial notebook: jupyter notebook notebooks/tutorial.ipynb")
    print("  • Launch Streamlit app: streamlit run streamlit_app_1d.py")
    print("  • Use the new Workflow API for your data")
else:
    print("⚠️  SOME ISSUES REMAIN - PLEASE REPORT!")
    print("=" * 70)
    print("\nPlease check:")
    print("  • Ensure you're using the latest code")
    print("  • Run: pytest tests/test_workflow.py tests/test_plotting.py -v")

print()
