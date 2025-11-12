#!/usr/bin/env python3
"""
FOBI Streamlit App
==================

Interactive web application for exploring FOBI parametric reconstruction
of neutron time-of-flight imaging data with realistic POLDI characteristics.

Run with:
    streamlit run streamlit_app.py
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import time

# Import FOBI modules
from fobi.reduction import fobi_wiener_2d
from fobi.edge_fitting import edge_fit_gaussian, edge_fit_gaussian_2d
from fobi.utils import (
    plot_edge_maps,
    generate_realistic_poldi_data,
    generate_realistic_chopper_modulated_data,
    poldi_neutron_flux,
    tof_to_wavelength,
    wavelength_to_tof,
)

# Configure page
st.set_page_config(
    page_title="FOBI - Parametric Reconstruction",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main Streamlit application."""

    # Title and description
    st.title("🔬 FOBI: Full-spectrum Bragg Edge Transmission Imaging")

    st.markdown("""
    Interactive exploration of parametric reconstruction for **realistic POLDI neutron imaging data**.

    This demonstrates Wiener deconvolution to reconstruct transmission spectra from chopper-modulated measurements.

    **Reference:** Carminati, C., et al. (2020). [Nature Scientific Reports](https://www.nature.com/articles/s41598-020-71705-4)
    """)

    # Sidebar for configuration
    st.sidebar.header("⚙️ Configuration")

    # Mode selection
    mode = st.sidebar.radio(
        "Select Mode",
        ["Realistic POLDI Data", "Upload Your Data (Coming Soon)"],
    )

    # ========================================================================
    # Data Generation / Loading
    # ========================================================================
    st.header("1️⃣ Data Preparation - Realistic POLDI Instrument")

    if mode == "Realistic POLDI Data":
        with st.expander("📊 POLDI Data Parameters", expanded=True):
            st.markdown("""
            **POLDI Instrument Characteristics:**
            - Wavelength range: 1-8 Å
            - Neutron flux peaks at ~1.5 Å
            - Multiple Bragg edges for Fe (BCC): 4.05 Å (110), 2.87 Å (200), 2.34 Å (211)
            - Flight path: 10 m
            """)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Detector Settings**")
                rows = st.slider("Image rows", 10, 100, 30)
                cols = st.slider("Image columns", 10, 100, 30)
                nbins = st.slider("Wavelength bins", 200, 1000, 400)

            with col2:
                st.markdown("**Sample Material**")
                material = st.selectbox("Material", ['Fe', 'Al', 'Generic'])
                noise_level = st.slider("Noise level", 0.0, 0.1, 0.03)
                add_spatial_var = st.checkbox("Add spatial variation (strain)", value=True)

            with col3:
                st.markdown("**Chopper Settings**")
                nrep = st.slider("Chopper repetitions", 4, 12, 8)
                chopper_id = st.selectbox("Chopper config", ['POLDI', '4x10', '5x8', '3x14'])
                nbins_mod = nbins * nrep

            if st.button("🎲 Generate Realistic POLDI Data", type="primary"):
                with st.spinner("Generating realistic chopper-modulated POLDI data..."):
                    # Generate chopper-modulated data
                    I_mod, I0_mod, wavelength, tof, tmax = generate_realistic_chopper_modulated_data(
                        shape=(rows, cols, nbins_mod),
                        nrep=nrep,
                        chopper_id=chopper_id,
                        wavelength_range=(1.0, 8.0),
                        material=material,
                        flight_path=10.0,
                        noise_level=noise_level,
                        add_spatial_variation=add_spatial_var,
                    )

                    # Also generate unconvoluted ground truth for comparison
                    I_true, I0_true, wavelength_true, tof_true = generate_realistic_poldi_data(
                        shape=(rows, cols, nbins),
                        wavelength_range=(1.0, 8.0),
                        material=material,
                        flight_path=10.0,
                        noise_level=noise_level,
                        add_spatial_variation=add_spatial_var,
                    )

                    # Store in session state
                    st.session_state['I_mod'] = I_mod
                    st.session_state['I0_mod'] = I0_mod
                    st.session_state['I_true'] = I_true
                    st.session_state['I0_true'] = I0_true
                    st.session_state['wavelength'] = wavelength
                    st.session_state['wavelength_true'] = wavelength_true
                    st.session_state['tof'] = tof
                    st.session_state['tof_true'] = tof_true
                    st.session_state['tmax'] = tmax
                    st.session_state['nrep'] = nrep
                    st.session_state['chopper_id'] = chopper_id
                    st.session_state['material'] = material

                    st.success("✅ Realistic POLDI data generated successfully!")

    else:  # Upload mode
        st.info("📁 Upload functionality - Coming soon! For now, use realistic POLDI data mode.")

    # Display data if available
    if 'I_mod' in st.session_state:
        st.success(f"✅ Data loaded: {st.session_state['I_mod'].shape}")

        # Show POLDI neutron flux
        st.subheader("🌟 POLDI Neutron Flux Distribution")
        wavelength = st.session_state['wavelength']
        flux = poldi_neutron_flux(wavelength)

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(wavelength, flux, 'b-', linewidth=2)
        ax.set_xlabel("Wavelength (Å)")
        ax.set_ylabel("Normalized Flux")
        ax.set_title("POLDI Neutron Spectrum (1-8 Å, peak at 1.5 Å)")
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0.5, 9)
        st.pyplot(fig)
        plt.close()

        # Show data preview - time-averaged images
        st.subheader("📷 Time-Averaged Detector Images")
        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(6, 5))
            im = ax.imshow(np.mean(st.session_state['I_mod'], axis=2), cmap='viridis')
            ax.set_title("Sample (chopper-modulated, time-avg)")
            ax.set_xlabel("X (pixels)")
            ax.set_ylabel("Y (pixels)")
            plt.colorbar(im, ax=ax, label="Intensity")
            st.pyplot(fig)
            plt.close()

        with col2:
            fig, ax = plt.subplots(figsize=(6, 5))
            im = ax.imshow(np.mean(st.session_state['I0_mod'], axis=2), cmap='viridis')
            ax.set_title("Open Beam (chopper-modulated, time-avg)")
            ax.set_xlabel("X (pixels)")
            ax.set_ylabel("Y (pixels)")
            plt.colorbar(im, ax=ax, label="Intensity")
            st.pyplot(fig)
            plt.close()

        # Show raw convoluted spectrum
        st.subheader("📊 Raw Chopper-Modulated Spectrum (Before Reconstruction)")
        st.markdown("""
        This shows the **actual measured signal** from the detector, which is convoluted with the chopper response.
        The FOBI reconstruction will deconvolve this to recover the true transmission spectrum.
        """)

        row_preview = st.session_state['I_mod'].shape[0] // 2
        col_preview = st.session_state['I_mod'].shape[1] // 2

        fig, axes = plt.subplots(2, 2, figsize=(14, 8))

        # Raw modulated sample
        axes[0, 0].plot(wavelength, st.session_state['I_mod'][row_preview, col_preview, :], 'b-', linewidth=1)
        axes[0, 0].set_xlabel("Wavelength (Å)")
        axes[0, 0].set_ylabel("Intensity (counts)")
        axes[0, 0].set_title(f"Raw Sample Signal (convoluted) - Pixel ({row_preview}, {col_preview})")
        axes[0, 0].grid(True, alpha=0.3)

        # Raw modulated open beam
        axes[0, 1].plot(wavelength, st.session_state['I0_mod'][row_preview, col_preview, :], 'g-', linewidth=1)
        axes[0, 1].set_xlabel("Wavelength (Å)")
        axes[0, 1].set_ylabel("Intensity (counts)")
        axes[0, 1].set_title("Raw Open Beam Signal (convoluted)")
        axes[0, 1].grid(True, alpha=0.3)

        # Raw transmission (convoluted)
        with np.errstate(divide='ignore', invalid='ignore'):
            T_raw = st.session_state['I_mod'][row_preview, col_preview, :] / st.session_state['I0_mod'][row_preview, col_preview, :]
            T_raw[~np.isfinite(T_raw)] = 1.0

        axes[1, 0].plot(wavelength, T_raw, 'r-', linewidth=1)
        axes[1, 0].set_xlabel("Wavelength (Å)")
        axes[1, 0].set_ylabel("Transmission")
        axes[1, 0].set_title("Raw Transmission (convoluted - hard to see edges!)")
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_ylim(0, 1.5)

        # Ground truth (for comparison)
        wavelength_true = st.session_state['wavelength_true']
        with np.errstate(divide='ignore', invalid='ignore'):
            T_true = st.session_state['I_true'][row_preview, col_preview, :] / st.session_state['I0_true'][row_preview, col_preview, :]
            T_true[~np.isfinite(T_true)] = 1.0

        axes[1, 1].plot(wavelength_true, T_true, 'g-', linewidth=2, label='Ground truth')
        axes[1, 1].set_xlabel("Wavelength (Å)")
        axes[1, 1].set_ylabel("Transmission")
        axes[1, 1].set_title("Ground Truth Transmission (unconvoluted)")
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].set_ylim(0, 1.5)
        axes[1, 1].legend()

        # Add annotations for Fe edges
        if st.session_state.get('material') == 'Fe':
            for ax in [axes[1, 0], axes[1, 1]]:
                ax.axvline(4.05, color='orange', linestyle='--', alpha=0.5, linewidth=1)
                ax.axvline(2.87, color='orange', linestyle='--', alpha=0.5, linewidth=1)
                ax.axvline(2.34, color='orange', linestyle='--', alpha=0.5, linewidth=1)
                ax.text(4.05, ax.get_ylim()[1]*0.95, '110', ha='center', fontsize=8, color='orange')
                ax.text(2.87, ax.get_ylim()[1]*0.95, '200', ha='center', fontsize=8, color='orange')
                ax.text(2.34, ax.get_ylim()[1]*0.95, '211', ha='center', fontsize=8, color='orange')

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        st.info("👆 Notice how the raw transmission (bottom-left) is heavily distorted by the chopper modulation, making Bragg edges hard to see. FOBI reconstruction will recover the true spectrum (bottom-right)!")

    # ========================================================================
    # FOBI Reconstruction
    # ========================================================================
    if 'I_mod' in st.session_state:
        st.header("2️⃣ FOBI Wiener Deconvolution - Reconstruct True Spectrum")

        with st.expander("⚙️ Reconstruction Parameters", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                nrep = st.number_input("Chopper repetitions", 1, 20, st.session_state['nrep'])
                chopper_id = st.selectbox("Chopper configuration", ['POLDI', '4x10', '5x8', '3x14'],
                                         index=['POLDI', '4x10', '5x8', '3x14'].index(st.session_state['chopper_id']))
                c = st.slider("Wiener constant (regularization)", 0.001, 1.0, 0.1, format="%.3f")
                st.caption("Higher = more smoothing, lower = more noise")

            with col2:
                flag_smooth = st.slider("Smoothing span", 0, 10, 0)
                roll = st.slider("Circular shift (re-center)", -50, 50, 0)
                st.caption("Adjust if spectrum appears shifted")

        if st.button("🔄 Run FOBI Reconstruction", type="primary"):
            with st.spinner("Performing FOBI Wiener deconvolution..."):
                start_time = time.time()

                # Get data
                I = st.session_state['I_mod']
                I0 = st.session_state['I0_mod']
                t = st.session_state['tof']
                tmax = st.session_state['tmax']

                # Run FOBI
                T, y_rec, y0_rec, t_merged = fobi_wiener_2d(
                    I, I0, t, tmax, nrep, chopper_id,
                    c=c, flag_smooth=flag_smooth, roll=roll
                )

                # Convert to wavelength
                wavelength_rec = tof_to_wavelength(t_merged, L=10.0)

                # Store results
                st.session_state['T'] = T
                st.session_state['y_rec'] = y_rec
                st.session_state['y0_rec'] = y0_rec
                st.session_state['t_merged'] = t_merged
                st.session_state['wavelength_rec'] = wavelength_rec

                elapsed = time.time() - start_time
                st.success(f"✅ Reconstruction complete! ({elapsed:.2f}s)")

    # Display reconstruction results
    if 'T' in st.session_state:
        st.subheader("📈 Reconstructed Transmission Spectrum")

        # Interactive pixel selection
        col1, col2 = st.columns([1, 3])

        with col1:
            row = st.slider("Row", 0, st.session_state['T'].shape[0]-1, st.session_state['T'].shape[0]//2)
            col_sel = st.slider("Column", 0, st.session_state['T'].shape[1]-1, st.session_state['T'].shape[1]//2)

            st.markdown(f"**Selected pixel:** ({row}, {col_sel})")

        with col2:
            # Plot comparison: Raw vs Reconstructed vs Ground Truth
            fig, axes = plt.subplots(2, 2, figsize=(14, 8))

            wavelength_rec = st.session_state['wavelength_rec']
            wavelength_raw = st.session_state['wavelength']
            wavelength_true = st.session_state['wavelength_true']
            T_rec = st.session_state['T']

            # Raw transmission (convoluted)
            with np.errstate(divide='ignore', invalid='ignore'):
                T_raw = st.session_state['I_mod'][row, col_sel, :] / st.session_state['I0_mod'][row, col_sel, :]
                T_raw[~np.isfinite(T_raw)] = 1.0

            axes[0, 0].plot(wavelength_raw, T_raw, 'r-', linewidth=1, alpha=0.7)
            axes[0, 0].set_xlabel("Wavelength (Å)")
            axes[0, 0].set_ylabel("Transmission")
            axes[0, 0].set_title(f"Raw Transmission (convoluted)")
            axes[0, 0].grid(True, alpha=0.3)
            axes[0, 0].set_ylim(0, 1.2)

            # Reconstructed transmission
            axes[0, 1].plot(wavelength_rec, T_rec[row, col_sel, :], 'b-', linewidth=2)
            axes[0, 1].set_xlabel("Wavelength (Å)")
            axes[0, 1].set_ylabel("Transmission")
            axes[0, 1].set_title(f"Reconstructed Transmission (FOBI)")
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].set_ylim(0, 1.2)

            # Ground truth comparison
            with np.errstate(divide='ignore', invalid='ignore'):
                T_true = st.session_state['I_true'][row, col_sel, :] / st.session_state['I0_true'][row, col_sel, :]
                T_true[~np.isfinite(T_true)] = 1.0

            axes[1, 0].plot(wavelength_true, T_true, 'g-', linewidth=2, label='Ground Truth', alpha=0.8)
            axes[1, 0].plot(wavelength_rec, T_rec[row, col_sel, :], 'b--', linewidth=2, label='Reconstructed', alpha=0.8)
            axes[1, 0].set_xlabel("Wavelength (Å)")
            axes[1, 0].set_ylabel("Transmission")
            axes[1, 0].set_title("Comparison: Ground Truth vs FOBI Reconstruction")
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
            axes[1, 0].set_ylim(0, 1.2)

            # Derivative (shows edges as peaks)
            d_trans = np.diff(T_rec[row, col_sel, :])
            d_wavelength = wavelength_rec[:-1]
            axes[1, 1].plot(d_wavelength, d_trans, 'purple', linewidth=1.5)
            axes[1, 1].set_xlabel("Wavelength (Å)")
            axes[1, 1].set_ylabel("d(Transmission)/dλ")
            axes[1, 1].set_title("Derivative (Bragg edges as peaks)")
            axes[1, 1].grid(True, alpha=0.3)
            axes[1, 1].axhline(0, color='k', linestyle='-', linewidth=0.5)

            # Add Fe edge markers
            if st.session_state.get('material') == 'Fe':
                for ax in axes.flat:
                    ax.axvline(4.05, color='orange', linestyle='--', alpha=0.4, linewidth=1)
                    ax.axvline(2.87, color='orange', linestyle='--', alpha=0.4, linewidth=1)
                    ax.axvline(2.34, color='orange', linestyle='--', alpha=0.4, linewidth=1)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        st.success("✅ Notice how the FOBI reconstruction successfully recovers the Bragg edges from the convoluted raw data!")

    # ========================================================================
    # Edge Fitting
    # ========================================================================
    if 'T' in st.session_state:
        st.header("3️⃣ Bragg Edge Fitting - Extract Material Properties")

        with st.expander("⚙️ Edge Fitting Parameters", expanded=True):
            wavelength_rec = st.session_state['wavelength_rec']

            st.markdown("""
            **Fitting a single Bragg edge to extract:**
            - Edge position → lattice spacing
            - Edge width → strain/texture
            - Edge height → phase fraction
            """)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Fitting Range**")
                range_min = st.number_input("λ min (Å)", 1.0, 8.0, 2.0)
                range_max = st.number_input("λ max (Å)", 1.0, 8.0, 5.0)

            with col2:
                st.markdown("**Initial Guesses**")
                est_p = st.number_input("Est. position (Å)", 1.0, 8.0, 4.0)
                est_w = st.number_input("Est. width (Å)", 0.001, 1.0, 0.02)
                est_h = st.number_input("Est. height", -1.0, 0.0, -0.1)

            with col3:
                st.markdown("**Boundary Conditions**")
                bc_p_min = st.number_input("BC position min (Å)", 1.0, 8.0, 2.0)
                bc_p_max = st.number_input("BC position max (Å)", 1.0, 8.0, 6.0)
                bc_w_min = st.number_input("BC width min (Å)", 0.0, 1.0, 0.005)
                bc_w_max = st.number_input("BC width max (Å)", 0.0, 1.0, 0.5)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🎯 Fit Single Pixel (test)", type="secondary"):
                with st.spinner("Fitting edge..."):
                    T = st.session_state['T']
                    row_fit = st.session_state.get('last_row', T.shape[0]//2)
                    col_fit = st.session_state.get('last_col', T.shape[1]//2)

                    # Store last selected pixel
                    st.session_state['last_row'] = row_fit
                    st.session_state['last_col'] = col_fit

                    pos, wid, h = edge_fit_gaussian(
                        T[row_fit, col_fit, :],
                        wavelength_rec,
                        spectrum_range=(range_min, range_max),
                        est_p=est_p,
                        est_w=est_w,
                        est_h=est_h,
                        BC_p=(bc_p_min, bc_p_max),
                        BC_w=(bc_w_min, bc_w_max),
                        BC_h=(-1, 0),
                        smooth_span=1,
                        plot_result=True,
                    )

                    st.pyplot(plt.gcf())
                    plt.close()

                    st.info(f"**Fitted parameters:**\n- Position: {pos:.4f} Å\n- Width: {wid:.4f} Å\n- Height: {h:.4f}")

        with col2:
            if st.button("🗺️ Fit All Pixels (2D)", type="primary"):
                with st.spinner("Fitting all pixels... This may take a minute."):
                    progress_bar = st.progress(0)

                    T = st.session_state['T']

                    # Simplified progress tracking
                    edge_p, edge_w, edge_h = edge_fit_gaussian_2d(
                        T,
                        wavelength_rec,
                        spectrum_range=(range_min, range_max),
                        est_p=est_p,
                        est_w=est_w,
                        est_h=est_h,
                        BC_p=(bc_p_min, bc_p_max),
                        BC_w=(bc_w_min, bc_w_max),
                        BC_h=(-1, 0),
                    )

                    progress_bar.progress(100)

                    # Store results
                    st.session_state['edge_p'] = edge_p
                    st.session_state['edge_w'] = edge_w
                    st.session_state['edge_h'] = edge_h

                    st.success("✅ 2D fitting complete!")

    # Display edge fitting results
    if 'edge_p' in st.session_state:
        st.subheader("🗺️ Edge Parameter Maps - Material Property Distribution")

        edge_p = st.session_state['edge_p']
        edge_w = st.session_state['edge_w']
        edge_h = st.session_state['edge_h']

        # Create maps
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        im1 = axes[0].imshow(edge_p, cmap='viridis', aspect='auto')
        axes[0].set_title('Edge Position (Å)\n→ Lattice Spacing / Strain')
        axes[0].set_xlabel('X (pixels)')
        axes[0].set_ylabel('Y (pixels)')
        plt.colorbar(im1, ax=axes[0], label='Position (Å)')

        im2 = axes[1].imshow(edge_w, cmap='plasma', aspect='auto')
        axes[1].set_title('Edge Width (Å)\n→ Strain Broadening / Texture')
        axes[1].set_xlabel('X (pixels)')
        axes[1].set_ylabel('Y (pixels)')
        plt.colorbar(im2, ax=axes[1], label='Width (Å)')

        im3 = axes[2].imshow(np.abs(edge_h), cmap='inferno', aspect='auto')
        axes[2].set_title('Edge Height\n→ Phase Fraction')
        axes[2].set_xlabel('X (pixels)')
        axes[2].set_ylabel('Y (pixels)')
        plt.colorbar(im3, ax=axes[2], label='Height (abs)')

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # Statistics
        st.subheader("📊 Statistics - Material Property Variations")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Mean Position (Å)", f"{np.nanmean(edge_p):.4f}")
            st.metric("Std Position (Å)", f"{np.nanstd(edge_p):.4f}")
            st.caption("Variation indicates strain distribution")

        with col2:
            st.metric("Mean Width (Å)", f"{np.nanmean(edge_w):.4f}")
            st.metric("Std Width (Å)", f"{np.nanstd(edge_w):.4f}")
            st.caption("Variation indicates texture/microstructure")

        with col3:
            st.metric("Mean Height", f"{np.nanmean(edge_h):.4f}")
            st.metric("Std Height", f"{np.nanstd(edge_h):.4f}")
            st.caption("Variation indicates phase distribution")

    # ========================================================================
    # Footer
    # ========================================================================
    st.markdown("---")
    st.markdown("""
    **About FOBI**

    FOBI (Full-spectrum Bragg edge transmission) is a parametric reconstruction technique for
    neutron time-of-flight imaging. It uses Wiener deconvolution to reconstruct transmission
    spectra from chopper-modulated measurements, enabling extraction of material properties
    through Bragg edge analysis.

    **This app demonstrates:**
    - Realistic POLDI neutron flux distribution (1-8 Å, peak at 1.5 Å)
    - Chopper modulation effects on raw measurements
    - FOBI Wiener deconvolution for spectral reconstruction
    - Bragg edge fitting for material property extraction

    **Reference:** Carminati, C., et al. "Bragg-edge attenuation spectra at voxel level from
    4D wavelength-resolved neutron tomography." *Nature Scientific Reports* 10, 13893 (2020).
    """)


if __name__ == '__main__':
    main()
