#!/usr/bin/env python3
"""
FOBI Streamlit App
==================

Interactive web application for exploring FOBI parametric reconstruction
of neutron time-of-flight imaging data.

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
    plot_transmission_spectrum,
    plot_edge_maps,
    generate_test_data,
)
from fobi.utils.synthetic_data import generate_chopper_modulated_data


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
    Interactive exploration of parametric reconstruction for neutron time-of-flight imaging.

    **Reference:** Carminati, C., et al. (2020). [Nature Scientific Reports](https://www.nature.com/articles/s41598-020-71705-4)
    """)

    # Sidebar for configuration
    st.sidebar.header("⚙️ Configuration")

    # Mode selection
    mode = st.sidebar.radio(
        "Select Mode",
        ["Generate Synthetic Data", "Upload Your Data"],
    )

    # ========================================================================
    # Data Generation / Loading
    # ========================================================================
    st.header("1️⃣ Data Preparation")

    if mode == "Generate Synthetic Data":
        with st.expander("📊 Synthetic Data Parameters", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                rows = st.slider("Image rows", 10, 100, 30)
                cols = st.slider("Image columns", 10, 100, 30)
                nbins = st.slider("Time bins", 200, 2000, 800)

            with col2:
                edge_position = st.slider("Edge position (bin)", 100, nbins-100, nbins//2)
                edge_width = st.slider("Edge width (bins)", 5, 50, 20)
                edge_height = st.slider("Edge height (transmission drop)", 0.1, 0.9, 0.5)
                noise_level = st.slider("Noise level", 0.0, 0.1, 0.03)

            add_chopper = st.checkbox("Simulate chopper modulation", value=True)

            if st.button("🎲 Generate Data", type="primary"):
                with st.spinner("Generating synthetic data..."):
                    if add_chopper:
                        # Generate chopper-modulated data
                        nrep = 8
                        chopper_id = 'POLDI'

                        I, I0, t, tmax = generate_chopper_modulated_data(
                            shape=(rows, cols, nbins),
                            nrep=nrep,
                            chopper_id=chopper_id,
                            edge_position=edge_position / nrep,
                            edge_width=edge_width / nrep,
                            edge_height=edge_height,
                            noise_level=noise_level,
                        )

                        # Store in session state
                        st.session_state['I'] = I
                        st.session_state['I0'] = I0
                        st.session_state['t'] = t
                        st.session_state['tmax'] = tmax
                        st.session_state['nrep'] = nrep
                        st.session_state['chopper_modulated'] = True

                    else:
                        # Generate simple transmission data
                        I, I0, t = generate_test_data(
                            shape=(rows, cols, nbins),
                            edge_position=edge_position,
                            edge_width=edge_width,
                            edge_height=edge_height,
                            noise_level=noise_level,
                        )

                        st.session_state['I'] = I
                        st.session_state['I0'] = I0
                        st.session_state['t'] = t
                        st.session_state['tmax'] = t[-1]
                        st.session_state['nrep'] = 1
                        st.session_state['chopper_modulated'] = False

                    st.success("✅ Data generated successfully!")

    else:  # Upload mode
        st.info("📁 Upload functionality - Coming soon! For now, use synthetic data mode.")

    # Display data if available
    if 'I' in st.session_state:
        st.success(f"✅ Data loaded: {st.session_state['I'].shape}")

        # Show data preview
        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.imshow(np.mean(st.session_state['I'], axis=2), cmap='viridis')
            ax.set_title("Sample (time-averaged)")
            ax.set_xlabel("X (pixels)")
            ax.set_ylabel("Y (pixels)")
            plt.colorbar(ax.images[0], ax=ax)
            st.pyplot(fig)
            plt.close()

        with col2:
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.imshow(np.mean(st.session_state['I0'], axis=2), cmap='viridis')
            ax.set_title("Open Beam (time-averaged)")
            ax.set_xlabel("X (pixels)")
            ax.set_ylabel("Y (pixels)")
            plt.colorbar(ax.images[0], ax=ax)
            st.pyplot(fig)
            plt.close()

    # ========================================================================
    # FOBI Reconstruction
    # ========================================================================
    if 'I' in st.session_state:
        st.header("2️⃣ FOBI Wiener Deconvolution")

        with st.expander("⚙️ Reconstruction Parameters", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.session_state['chopper_modulated']:
                    nrep = st.number_input("Chopper repetitions", 1, 20, st.session_state['nrep'])
                    chopper_id = st.selectbox("Chopper configuration", ['POLDI', '4x10', '5x8', '3x14'])
                else:
                    nrep = 1
                    chopper_id = 'POLDI'
                    st.info("No chopper modulation - using simple reconstruction")

            with col2:
                c = st.slider("Wiener constant (regularization)", 0.001, 1.0, 0.1, format="%.3f")
                st.caption("Higher = more smoothing")

            with col3:
                flag_smooth = st.slider("Smoothing span", 0, 10, 0)
                roll = st.slider("Circular shift", -100, 100, 0)

        if st.button("🔄 Run FOBI Reconstruction", type="primary"):
            with st.spinner("Performing FOBI Wiener deconvolution..."):
                start_time = time.time()

                # Get data
                I = st.session_state['I']
                I0 = st.session_state['I0']
                t = st.session_state['t']
                tmax = st.session_state['tmax']

                # Run FOBI
                T, y_rec, y0_rec, t_merged = fobi_wiener_2d(
                    I, I0, t, tmax, nrep, chopper_id,
                    c=c, flag_smooth=flag_smooth, roll=roll
                )

                # Store results
                st.session_state['T'] = T
                st.session_state['y_rec'] = y_rec
                st.session_state['y0_rec'] = y0_rec
                st.session_state['t_merged'] = t_merged

                elapsed = time.time() - start_time
                st.success(f"✅ Reconstruction complete! ({elapsed:.2f}s)")

    # Display reconstruction results
    if 'T' in st.session_state:
        st.subheader("📈 Reconstructed Transmission")

        # Interactive pixel selection
        col1, col2 = st.columns([1, 2])

        with col1:
            row = st.slider("Row", 0, st.session_state['T'].shape[0]-1, st.session_state['T'].shape[0]//2)
            col = st.slider("Column", 0, st.session_state['T'].shape[1]-1, st.session_state['T'].shape[1]//2)

            st.markdown(f"**Selected pixel:** ({row}, {col})")

        with col2:
            # Plot spectrum for selected pixel
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

            t_merged = st.session_state['t_merged']
            T = st.session_state['T']

            # Transmission
            ax1.plot(t_merged, T[row, col, :], 'b-', linewidth=1.5)
            ax1.set_xlabel("Time-of-Flight (µs)")
            ax1.set_ylabel("Transmission")
            ax1.set_title(f"Pixel ({row}, {col}) - Transmission")
            ax1.grid(True, alpha=0.3)

            # Derivative
            d_trans = np.diff(T[row, col, :])
            d_t = t_merged[:-1]
            ax2.plot(d_t, d_trans, 'g-', linewidth=1.5)
            ax2.set_xlabel("Time-of-Flight (µs)")
            ax2.set_ylabel("d(Transmission)/dt")
            ax2.set_title("Derivative (shows edges as peaks)")
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    # ========================================================================
    # Edge Fitting
    # ========================================================================
    if 'T' in st.session_state:
        st.header("3️⃣ Bragg Edge Fitting")

        with st.expander("⚙️ Edge Fitting Parameters", expanded=True):
            col1, col2, col3 = st.columns(3)

            t_merged = st.session_state['t_merged']

            with col1:
                range_min = st.number_input("Spectrum range min", float(t_merged[0]), float(t_merged[-1]), float(t_merged[0]))
                range_max = st.number_input("Spectrum range max", float(t_merged[0]), float(t_merged[-1]), float(t_merged[-1]))

            with col2:
                est_p = st.number_input("Est. position", float(t_merged[0]), float(t_merged[-1]), float(t_merged[len(t_merged)//2]))
                est_w = st.number_input("Est. width", 0.001, 100.0, float(t_merged[1] - t_merged[0]) * 5)
                est_h = st.number_input("Est. height", -1.0, 0.0, -0.05)

            with col3:
                bc_p_min = st.number_input("BC position min", float(t_merged[0]), float(t_merged[-1]), float(t_merged[0]))
                bc_p_max = st.number_input("BC position max", float(t_merged[0]), float(t_merged[-1]), float(t_merged[-1]))
                bc_w_min = st.number_input("BC width min", 0.0, 100.0, 0.01)
                bc_w_max = st.number_input("BC width max", 0.0, 100.0, 50.0)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🎯 Fit Single Pixel (test)", type="secondary"):
                with st.spinner("Fitting edge..."):
                    T = st.session_state['T']
                    row = st.session_state.get('last_row', T.shape[0]//2)
                    col = st.session_state.get('last_col', T.shape[1]//2)

                    # Store last selected pixel
                    st.session_state['last_row'] = row
                    st.session_state['last_col'] = col

                    pos, wid, h = edge_fit_gaussian(
                        T[row, col, :],
                        t_merged,
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

                    st.info(f"**Fitted parameters:**\n- Position: {pos:.4f}\n- Width: {wid:.4f}\n- Height: {h:.4f}")

        with col2:
            if st.button("🗺️ Fit All Pixels (2D)", type="primary"):
                with st.spinner("Fitting all pixels... This may take a minute."):
                    progress_bar = st.progress(0)

                    T = st.session_state['T']

                    # Simplified progress tracking
                    edge_p, edge_w, edge_h = edge_fit_gaussian_2d(
                        T,
                        t_merged,
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
        st.subheader("🗺️ Edge Parameter Maps")

        edge_p = st.session_state['edge_p']
        edge_w = st.session_state['edge_w']
        edge_h = st.session_state['edge_h']

        # Create maps
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        im1 = axes[0].imshow(edge_p, cmap='viridis', aspect='auto')
        axes[0].set_title('Edge Position')
        axes[0].set_xlabel('X (pixels)')
        axes[0].set_ylabel('Y (pixels)')
        plt.colorbar(im1, ax=axes[0])

        im2 = axes[1].imshow(edge_w, cmap='plasma', aspect='auto')
        axes[1].set_title('Edge Width')
        axes[1].set_xlabel('X (pixels)')
        axes[1].set_ylabel('Y (pixels)')
        plt.colorbar(im2, ax=axes[1])

        im3 = axes[2].imshow(np.abs(edge_h), cmap='inferno', aspect='auto')
        axes[2].set_title('Edge Height (abs)')
        axes[2].set_xlabel('X (pixels)')
        axes[2].set_ylabel('Y (pixels)')
        plt.colorbar(im3, ax=axes[2])

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # Statistics
        st.subheader("📊 Statistics")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Mean Position", f"{np.nanmean(edge_p):.4f}")
            st.metric("Std Position", f"{np.nanstd(edge_p):.4f}")

        with col2:
            st.metric("Mean Width", f"{np.nanmean(edge_w):.4f}")
            st.metric("Std Width", f"{np.nanstd(edge_w):.4f}")

        with col3:
            st.metric("Mean Height", f"{np.nanmean(edge_h):.4f}")
            st.metric("Std Height", f"{np.nanstd(edge_h):.4f}")

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

    **Reference:** Carminati, C., et al. "Bragg-edge attenuation spectra at voxel level from
    4D wavelength-resolved neutron tomography." *Nature Scientific Reports* 10, 13893 (2020).
    """)


if __name__ == '__main__':
    main()
