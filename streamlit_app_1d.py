#!/usr/bin/env python3
"""
FOBI 1D Streamlit App
=====================

Interactive web application for 1D neutron transmission spectrum reconstruction
using the new FOBI Workflow API.

Run with:
    streamlit run streamlit_app_1d.py
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import io

# Import FOBI Workflow
import fobi


# Configure page
st.set_page_config(
    page_title="FOBI 1D Reconstruction",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def generate_iron_data(L=9, tmax=10000, nrep=8, noise_std=0.02):
    """Generate synthetic iron powder data with multiple Bragg edges."""
    nbins = 1000 * nrep
    t = np.linspace(0, tmax, nbins)
    wavelength = 3.956 * (t / 1000) / L

    # Iron BCC structure edges
    edges = [
        (2.027, 0.10, 0.25),  # (110)
        (2.866, 0.12, 0.20),  # (200)
        (4.050, 0.15, 0.30),  # (211)
    ]

    transmission = np.ones_like(wavelength) * 0.6
    for pos, width, height in edges:
        transmission += height / (1 + np.exp(-(wavelength - pos) / width))

    # Open beam
    openbeam_base = np.ones_like(t) * 1000
    openbeam = openbeam_base + np.random.randn(len(t)) * noise_std * openbeam_base

    # Sample signal
    signal_base = transmission * openbeam_base
    signal = signal_base + np.random.randn(len(t)) * noise_std * signal_base

    return t, signal, openbeam, transmission


def generate_custom_data(L=9, tmax=10000, nrep=8,
                        edge_positions=[4.0], edge_widths=[0.15],
                        edge_heights=[0.3], base_transmission=0.7,
                        noise_std=0.02):
    """Generate custom data with user-specified Bragg edges."""
    nbins = 1000 * nrep
    t = np.linspace(0, tmax, nbins)
    wavelength = 3.956 * (t / 1000) / L

    transmission = np.ones_like(wavelength) * base_transmission

    for pos, width, height in zip(edge_positions, edge_widths, edge_heights):
        transmission += height / (1 + np.exp(-(wavelength - pos) / width))

    # Open beam
    openbeam_base = np.ones_like(t) * 1000
    openbeam = openbeam_base + np.random.randn(len(t)) * noise_std * openbeam_base

    # Sample signal
    signal_base = transmission * openbeam_base
    signal = signal_base + np.random.randn(len(t)) * noise_std * signal_base

    return t, signal, openbeam, transmission


def main():
    """Main Streamlit application."""

    # Title and description
    st.title("📊 FOBI 1D Reconstruction")

    st.markdown("""
    Interactive tool for reconstructing 1D neutron transmission spectra using the **FOBI Workflow API**.

    **New Features:**
    - Simple method chaining API
    - Easy parameter exploration
    - CSV import/export
    - Interactive visualization

    **Reference:** [Carminati et al., Nature Sci. Rep. (2020)](https://www.nature.com/articles/s41598-020-71705-4)
    """)

    # Sidebar
    st.sidebar.header("⚙️ Configuration")

    # Mode selection
    mode = st.sidebar.radio(
        "Data Source",
        ["Real Iron Powder Example", "Generate Synthetic Data", "Upload CSV Files"],
    )

    # ========================================================================
    # 1. Data Loading
    # ========================================================================
    st.header("1️⃣ Data Input")

    if mode == "Real Iron Powder Example":
        st.subheader("Real Iron Powder Data")

        st.warning("""
        **⚠️ Important**: This is **direct time-of-flight data** (not chopper-modulated).

        For direct TOF data, transmission is simply calculated as:
        **T(λ) = Sample / OpenBeam**

        FOBI reconstruction is **not needed** for this data type.
        """)

        st.info("""
        **Real neutron transmission data from iron powder**

        - Measurement: Direct TOF (pulsed source)
        - Flight path: 9 meters
        - Time step: 10 µs per stack
        - Expected Bragg edges: Fe (110) at 2.027 Å, Fe (200) at 2.866 Å, Fe (211) at 4.050 Å
        """)

        # Check if data files exist
        iron_file = Path("notebooks/iron_powder.csv")
        openbeam_file = Path("notebooks/openbeam.csv")

        if iron_file.exists() and openbeam_file.exists():
            col1, col2 = st.columns(2)

            with col1:
                wavelength_min = st.number_input("Min wavelength (Å)", 0.5, 10.0, 1.0, 0.5)
            with col2:
                wavelength_max = st.number_input("Max wavelength (Å)", 1.0, 15.0, 10.0, 0.5)

            if st.button("📂 Load Real Data (Direct TOF)", type="primary"):
                with st.spinner("Loading and processing real data..."):
                    import pandas as pd

                    signal_df = pd.read_csv(iron_file)
                    openbeam_df = pd.read_csv(openbeam_file)

                    # Calculate time and wavelength
                    time_step = 10  # µs
                    L = 9  # meters
                    stack = signal_df['stack'].values
                    time_full = stack * time_step
                    wavelength_full = 3.956 * (time_full / 1000) / L

                    # Filter to desired wavelength range
                    mask = (wavelength_full >= wavelength_min) & (wavelength_full <= wavelength_max)

                    time = time_full[mask] - time_full[mask].min()  # Reset to start at 0
                    signal = signal_df['counts'].values[mask]
                    openbeam = openbeam_df['counts'].values[mask]

                    # Calculate direct transmission for display
                    direct_trans = signal / openbeam

                    # Store in session state
                    st.session_state['t'] = time
                    st.session_state['signal'] = signal
                    st.session_state['openbeam'] = openbeam
                    st.session_state['true_trans'] = direct_trans  # Store direct transmission
                    st.session_state['L'] = L
                    st.session_state['tmax'] = float(time.max())
                    st.session_state['nrep'] = 1  # Direct TOF, no repetitions
                    st.session_state['is_direct_tof'] = True

                    st.success(f"✅ Loaded {len(time)} data points ({wavelength_min}-{wavelength_max} Å)")
                    st.info("This is direct TOF data. The 'true transmission' shows the simple ratio: Sample/OpenBeam")
        else:
            st.warning(f"⚠️ Data files not found:\n- {iron_file}\n- {openbeam_file}")
            st.info("Please ensure the iron_powder.csv and openbeam.csv files are in the notebooks/ folder.")

    elif mode == "Generate Synthetic Data":
        st.subheader("Synthetic Data Generator")

        data_type = st.radio(
            "Select data type",
            ["Iron Powder (realistic)", "Custom Edges"],
        )

        col1, col2 = st.columns(2)

        with col1:
            L = st.number_input("Flight path length (m)", 1.0, 50.0, 9.0, 0.5)
            tmax = st.number_input("Max time-of-flight (µs)", 1000, 50000, 10000, 1000)
            nrep = st.number_input("Chopper repetitions", 1, 20, 8)

        with col2:
            noise_std = st.slider("Noise level", 0.0, 0.1, 0.02, 0.001)

        if data_type == "Custom Edges":
            st.markdown("**Define Bragg Edges:**")

            n_edges = st.number_input("Number of edges", 1, 5, 1)

            edge_positions = []
            edge_widths = []
            edge_heights = []

            cols = st.columns(n_edges)
            for i, col in enumerate(cols):
                with col:
                    st.markdown(f"**Edge {i+1}**")
                    pos = st.number_input(f"Position (Å)", 1.0, 10.0, 4.0 + i, 0.1, key=f"pos_{i}")
                    width = st.number_input(f"Width (Å)", 0.01, 1.0, 0.15, 0.01, key=f"width_{i}")
                    height = st.number_input(f"Height", 0.0, 1.0, 0.3, 0.05, key=f"height_{i}")
                    edge_positions.append(pos)
                    edge_widths.append(width)
                    edge_heights.append(height)

            base_transmission = st.slider("Base transmission", 0.1, 1.0, 0.7, 0.05)

        if st.button("🎲 Generate Data", type="primary"):
            with st.spinner("Generating data..."):
                if data_type == "Iron Powder (realistic)":
                    t, signal, openbeam, true_trans = generate_iron_data(L, tmax, nrep, noise_std)
                else:
                    t, signal, openbeam, true_trans = generate_custom_data(
                        L, tmax, nrep, edge_positions, edge_widths,
                        edge_heights, base_transmission, noise_std
                    )

                # Store in session state
                st.session_state['t'] = t
                st.session_state['signal'] = signal
                st.session_state['openbeam'] = openbeam
                st.session_state['true_trans'] = true_trans
                st.session_state['L'] = L
                st.session_state['tmax'] = tmax
                st.session_state['nrep'] = nrep

                st.success("✅ Data generated successfully!")

    else:  # Upload CSV
        st.subheader("Upload CSV Files")

        col1, col2 = st.columns(2)

        with col1:
            signal_file = st.file_uploader("Sample signal CSV", type=['csv'])
            st.caption("Expected columns: 'time', 'signal'")

        with col2:
            openbeam_file = st.file_uploader("Open beam CSV", type=['csv'])
            st.caption("Expected columns: 'time', 'signal'")

        col1, col2 = st.columns(2)
        with col1:
            L = st.number_input("Flight path length (m)", 1.0, 50.0, 9.0, 0.5, key="upload_L")
            tmax = st.number_input("Max time-of-flight (µs)", 1000, 50000, 10000, 1000, key="upload_tmax")
        with col2:
            nrep = st.number_input("Chopper repetitions", 1, 20, 8, key="upload_nrep")

        if signal_file and openbeam_file:
            if st.button("📂 Load CSV Files", type="primary"):
                with st.spinner("Loading files..."):
                    # Read CSVs
                    signal_df = pd.read_csv(signal_file)
                    openbeam_df = pd.read_csv(openbeam_file)

                    # Extract data
                    t = signal_df['time'].values
                    signal = signal_df['signal'].values
                    openbeam = openbeam_df['signal'].values

                    # Store in session state
                    st.session_state['t'] = t
                    st.session_state['signal'] = signal
                    st.session_state['openbeam'] = openbeam
                    st.session_state['L'] = L
                    st.session_state['tmax'] = tmax
                    st.session_state['nrep'] = nrep
                    st.session_state['true_trans'] = None

                    st.success(f"✅ Loaded {len(t)} data points")

    # Display raw data if available
    if 't' in st.session_state:
        st.subheader("📈 Raw Data Preview")

        t = st.session_state['t']
        signal = st.session_state['signal']
        openbeam = st.session_state['openbeam']

        fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

        axes[0].plot(t, signal, linewidth=0.5, alpha=0.7)
        axes[0].set_ylabel('Sample Signal')
        axes[0].grid(True, alpha=0.3)
        axes[0].set_title('Raw Data')

        axes[1].plot(t, openbeam, linewidth=0.5, alpha=0.7, color='orange')
        axes[1].set_ylabel('Open Beam')
        axes[1].grid(True, alpha=0.3)

        axes[2].plot(t, signal/openbeam, linewidth=0.5, alpha=0.7, color='green')
        axes[2].set_ylabel('Raw Transmission')
        axes[2].set_xlabel('Time-of-Flight (µs)')
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # ========================================================================
    # 2. FOBI Reconstruction
    # ========================================================================
    if 't' in st.session_state:
        st.header("2️⃣ FOBI Reconstruction")

        st.markdown("### Reconstruction Parameters")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Chopper Settings**")
            chopper = st.selectbox("Chopper configuration", ['POLDI', '4x10', '5x8', '3x14'])
            st.caption("POLDI: 8 slits, 4x10: 10 slits, etc.")

        with col2:
            st.markdown("**Wiener Filter**")
            noise_level = st.slider("Noise level (regularization)", 0.001, 2.0, 0.1, 0.001, format="%.3f")
            st.caption("Higher = more smoothing")

        with col3:
            st.markdown("**Advanced**")
            filter_type = st.selectbox("Frequency filter", ['none', 'LowPass', 'LowPassBu', 'LowPassGa'])
            roll = st.number_input("Circular shift", -100, 100, 0)

        if st.button("🔄 Run Reconstruction", type="primary", use_container_width=True):
            with st.spinner("Running FOBI Workflow..."):
                # Get data
                t = st.session_state['t']
                signal = st.session_state['signal']
                openbeam = st.session_state['openbeam']
                L = st.session_state['L']
                tmax = st.session_state['tmax']
                nrep = st.session_state['nrep']

                # Run workflow with method chaining
                result = (fobi.Workflow
                    .load_arrays(signal=signal, openbeam=openbeam, time=t, L=L)
                    .interpolate(tmax=tmax, nrep=nrep)
                    .convolve(chopper=chopper, noise_level=noise_level, filter_type=filter_type)
                    .reconstruct(roll=roll))

                # Store result
                st.session_state['result'] = result

                st.success("✅ Reconstruction complete!")

                # Display parameters
                st.info(f"""
                **Reconstruction Info:**
                - Chopper: {result.metadata['chopper']}
                - Noise level: {result.metadata['noise_level']}
                - Filter: {result.metadata['filter_type']}
                - Spectral points: {len(result.time)}
                """)

    # ========================================================================
    # 3. Results Visualization
    # ========================================================================
    if 'result' in st.session_state:
        st.header("3️⃣ Results")

        result = st.session_state['result']

        # Plotting options
        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown("**Plot Options**")
            x_axis = st.radio("X-axis", ["time", "wavelength"])
            what = st.radio("Show", ["transmission", "signal", "openbeam", "all"])

            wavelength_range = st.slider(
                "Wavelength range (Å)",
                float(result.wavelength[0]),
                float(result.wavelength[-1]),
                (2.0, 6.0) if result.wavelength is not None else (float(result.wavelength[0]), float(result.wavelength[-1]))
            ) if result.wavelength is not None else None

        with col2:
            # Create plot
            if what == "all":
                fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

                x = result.wavelength if x_axis == "wavelength" else result.time
                x_label = "Wavelength (Å)" if x_axis == "wavelength" else "Time-of-Flight (µs)"

                axes[0].plot(x, result.transmission, linewidth=2)
                axes[0].set_ylabel("Transmission", fontsize=11)
                axes[0].grid(True, alpha=0.3)
                axes[0].set_title("FOBI Reconstruction Results", fontsize=13, fontweight='bold')

                axes[1].plot(x, result.signal, linewidth=2, color='orange')
                axes[1].set_ylabel("Sample Signal", fontsize=11)
                axes[1].grid(True, alpha=0.3)

                axes[2].plot(x, result.openbeam, linewidth=2, color='green')
                axes[2].set_ylabel("Open Beam", fontsize=11)
                axes[2].set_xlabel(x_label, fontsize=11)
                axes[2].grid(True, alpha=0.3)

                if wavelength_range and x_axis == "wavelength":
                    for ax in axes:
                        ax.set_xlim(wavelength_range)

                plt.tight_layout()
            else:
                fig, ax = plt.subplots(figsize=(12, 6))

                data_map = {
                    "transmission": (result.transmission, "Transmission"),
                    "signal": (result.signal, "Sample Signal"),
                    "openbeam": (result.openbeam, "Open Beam"),
                }

                data, ylabel = data_map[what]
                x = result.wavelength if x_axis == "wavelength" else result.time
                x_label = "Wavelength (Å)" if x_axis == "wavelength" else "Time-of-Flight (µs)"

                ax.plot(x, data, linewidth=2)
                ax.set_xlabel(x_label, fontsize=12)
                ax.set_ylabel(ylabel, fontsize=12)
                ax.set_title(f"FOBI Reconstruction: {ylabel}", fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3)

                if wavelength_range and x_axis == "wavelength":
                    ax.set_xlim(wavelength_range)

                plt.tight_layout()

            st.pyplot(fig)
            plt.close()

        # Compare with true transmission if available
        if st.session_state.get('true_trans') is not None:
            st.subheader("📊 Comparison with True Transmission")

            true_trans = st.session_state['true_trans']
            t_orig = st.session_state['t']
            L = st.session_state['L']

            wavelength_orig = 3.956 * (t_orig / 1000) / L
            true_trans_interp = np.interp(result.wavelength, wavelength_orig, true_trans)

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(result.wavelength, true_trans_interp, 'k-', linewidth=2.5,
                   label='True Transmission', alpha=0.7)
            ax.plot(result.wavelength, result.transmission, 'r-', linewidth=2,
                   label='FOBI Reconstruction', alpha=0.8)
            ax.set_xlabel('Wavelength (Å)', fontsize=12)
            ax.set_ylabel('Transmission', fontsize=12)
            ax.set_title('Reconstruction Quality', fontsize=14, fontweight='bold')
            ax.legend(fontsize=11)
            ax.grid(True, alpha=0.3)

            if wavelength_range:
                ax.set_xlim(wavelength_range)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            # Calculate error metrics
            mse = np.mean((result.transmission - true_trans_interp)**2)
            mae = np.mean(np.abs(result.transmission - true_trans_interp))

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Mean Squared Error", f"{mse:.6f}")
            with col2:
                st.metric("Mean Absolute Error", f"{mae:.6f}")

    # ========================================================================
    # 4. Export Results
    # ========================================================================
    if 'result' in st.session_state:
        st.header("4️⃣ Export")

        result = st.session_state['result']

        col1, col2 = st.columns(2)

        with col1:
            # CSV export
            df = pd.DataFrame({
                'time': result.time,
                'wavelength': result.wavelength if result.wavelength is not None else np.zeros_like(result.time),
                'transmission': result.transmission,
                'signal': result.signal,
                'openbeam': result.openbeam,
            })

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)

            st.download_button(
                label="📥 Download CSV",
                data=csv_buffer.getvalue(),
                file_name="fobi_reconstruction.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            # Numpy export
            data_dict = {
                'time': result.time,
                'transmission': result.transmission,
                'signal': result.signal,
                'openbeam': result.openbeam,
                'wavelength': result.wavelength,
                'metadata': result.metadata,
            }

            npy_buffer = io.BytesIO()
            np.save(npy_buffer, data_dict)

            st.download_button(
                label="📥 Download NPY",
                data=npy_buffer.getvalue(),
                file_name="fobi_reconstruction.npy",
                mime="application/octet-stream",
                use_container_width=True
            )

    # ========================================================================
    # 5. Code Example
    # ========================================================================
    if 'result' in st.session_state:
        st.header("5️⃣ Code Example")

        result = st.session_state['result']

        code = f"""
import fobi

# Load and reconstruct with method chaining
result = (fobi.Workflow
    .load(signal="sample.csv", openbeam="openbeam.csv", L={result.metadata['L']})
    .interpolate(tmax={st.session_state['tmax']}, nrep={st.session_state['nrep']})
    .convolve(chopper="{result.metadata['chopper']}",
              noise_level={result.metadata['noise_level']},
              filter_type="{result.metadata['filter_type']}")
    .reconstruct(roll={result.metadata['roll']}))

# Plot results
result.plot(what="transmission", x_axis="wavelength")

# Save results
result.save("output.csv")
"""

        st.code(code, language="python")

    # ========================================================================
    # Footer
    # ========================================================================
    st.markdown("---")
    st.markdown("""
    **About FOBI**

    FOBI uses Wiener deconvolution to reconstruct high-resolution neutron transmission spectra
    from chopper-modulated time-of-flight measurements. The new Workflow API provides a clean,
    method-chaining interface for 1D data processing.

    **Features:**
    - Simple, readable API with method chaining
    - Support for multiple chopper configurations
    - Flexible frequency-domain filtering
    - Easy CSV import/export
    - Interactive parameter exploration

    **Reference:** Carminati, C., et al. "Bragg-edge attenuation spectra at voxel level from
    4D wavelength-resolved neutron tomography." *Nature Scientific Reports* 10, 13893 (2020).
    """)


if __name__ == '__main__':
    main()
