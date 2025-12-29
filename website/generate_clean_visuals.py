"""
Generate Clean Professional Visualizations for Website
No text reports - only clean, independent charts
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set professional style
plt.style.use('dark_background')
sns.set_palette("husl")

# Output directory
output_dir = Path('images')
output_dir.mkdir(exist_ok=True)

# Base directory (parent of website folder)
base_dir = Path(__file__).parent.parent

print("="*70)
print("Generating Clean Professional Visualizations")
print("="*70)


# ==================== 1. Satellite-Contrail Fusion ====================
def generate_fusion_image():
    """Generate clean satellite-contrail-flight fusion visualization"""
    print("\n[1/5] Generating satellite-contrail fusion image...")

    try:
        # Load actual data
        record_id = '1350397700256573018'
        record_path = base_dir / 'validation' / record_id

        if not record_path.exists():
            print("  [SKIP] Validation data not found")
            return

        # Load bands
        band_11 = np.load(record_path / 'band_11.npy')
        band_14 = np.load(record_path / 'band_14.npy')
        band_15 = np.load(record_path / 'band_15.npy')
        contrail_mask = np.load(record_path / 'human_pixel_masks.npy')

        # Create false color image
        timestep = 4
        b11 = band_11[:, :, timestep]
        b14 = band_14[:, :, timestep]
        b15 = band_15[:, :, timestep]

        def normalize(band):
            band_min = np.nanpercentile(band, 1)
            band_max = np.nanpercentile(band, 99)
            normalized = (band - band_min) / (band_max - band_min)
            return np.clip(normalized, 0, 1)

        r = normalize(b15 - b14)
        g = normalize(b14 - b11)
        b = normalize(b14)
        rgb = np.stack([r, g, b], axis=2)

        # Create single clean fusion image
        fig, ax = plt.subplots(figsize=(12, 12), facecolor='#0a1628')
        ax.set_facecolor('#0a1628')

        # Show satellite image
        ax.imshow(rgb, alpha=0.9)

        # Overlay contrail mask
        mask_display = np.ma.masked_where(contrail_mask[:,:,0] == 0, contrail_mask[:,:,0])
        ax.imshow(mask_display, cmap='Reds', alpha=0.6, vmin=0, vmax=1)

        # Load and plot flight tracks
        flight_data = pd.read_csv(base_dir / 'data/flights/validation_flights_matched.csv')
        flights = flight_data[flight_data['record_id'] == int(record_id)]

        if len(flights) > 0:
            bbox_min_lat = flights['bbox_min_lat'].iloc[0]
            bbox_max_lat = flights['bbox_max_lat'].iloc[0]
            bbox_min_lon = flights['bbox_min_lon'].iloc[0]
            bbox_max_lon = flights['bbox_max_lon'].iloc[0]

            def latlon_to_pixel(lat, lon):
                lat_norm = (lat - bbox_min_lat) / (bbox_max_lat - bbox_min_lat)
                lon_norm = (lon - bbox_min_lon) / (bbox_max_lon - bbox_min_lon)
                x = lon_norm * 256
                y = (1 - lat_norm) * 256
                return x, y

            # Plot flight tracks
            colors = plt.cm.cool(np.linspace(0, 1, len(flights)))
            for idx, (_, flight) in enumerate(flights.iterrows()):
                lat1, lon1 = flight['latitude_1'], flight['longitude_1']
                lat2, lon2 = flight['latitude_2'], flight['longitude_2']
                x1, y1 = latlon_to_pixel(lat1, lon1)
                x2, y2 = latlon_to_pixel(lat2, lon2)

                if 0 <= x1 <= 256 and 0 <= y1 <= 256:
                    ax.plot([x1, x2], [y1, y2], color=colors[idx],
                           linewidth=2.5, alpha=0.8)
                    ax.plot(x1, y1, 'o', color=colors[idx], markersize=8,
                           markeredgecolor='white', markeredgewidth=1.5)

        ax.axis('off')
        plt.tight_layout(pad=0)

        output_file = output_dir / 'contrail_fusion.png'
        plt.savefig(output_file, dpi=200, bbox_inches='tight',
                   facecolor='#0a1628', edgecolor='none')
        plt.close()

        print(f"  [OK] Saved: {output_file}")

    except Exception as e:
        print(f"  [ERROR] {e}")


# ==================== 2. Emission Distribution ====================
def generate_emission_charts():
    """Generate clean emission analysis charts"""
    print("\n[2/5] Generating emission distribution chart...")

    try:
        df = pd.read_csv(base_dir / 'data/flights/validation_emissions_results.csv')

        # Single clean chart: CO2 distribution with key stats
        fig, ax = plt.subplots(figsize=(14, 8), facecolor='#0a1628')
        ax.set_facecolor('#0a1628')

        # Histogram
        n, bins, patches = ax.hist(df['co2_total_kg']/1000, bins=20,
                                    color='#00cc66', alpha=0.7, edgecolor='white')

        # Color gradient
        for i, patch in enumerate(patches):
            patch.set_facecolor(plt.cm.viridis(i / len(patches)))

        # Add mean and median lines
        mean_val = df['co2_total_kg'].mean() / 1000
        median_val = df['co2_total_kg'].median() / 1000

        ax.axvline(mean_val, color='#ff9933', linewidth=3,
                  linestyle='--', label=f'Mean: {mean_val:.1f} tonnes', alpha=0.8)
        ax.axvline(median_val, color='#3399ff', linewidth=3,
                  linestyle='--', label=f'Median: {median_val:.1f} tonnes', alpha=0.8)

        ax.set_xlabel('CO₂ Emissions (tonnes)', fontsize=14, fontweight='bold', color='white')
        ax.set_ylabel('Number of Flights', fontsize=14, fontweight='bold', color='white')
        ax.tick_params(colors='white', labelsize=12)
        ax.grid(True, alpha=0.2, color='white')
        ax.legend(fontsize=12, loc='upper right', framealpha=0.9)

        # Clean spine
        for spine in ax.spines.values():
            spine.set_color('white')
            spine.set_linewidth(1)

        plt.tight_layout()
        output_file = output_dir / 'emission_distribution.png'
        plt.savefig(output_file, dpi=200, bbox_inches='tight',
                   facecolor='#0a1628', edgecolor='none')
        plt.close()

        print(f"  [OK] Saved: {output_file}")

    except Exception as e:
        print(f"  [ERROR] {e}")


# ==================== 3. Distance vs Emission ====================
def generate_distance_emission():
    """Generate clean distance-emission correlation chart"""
    print("\n[3/5] Generating distance-emission correlation...")

    try:
        df = pd.read_csv(base_dir / 'data/flights/validation_emissions_results.csv')

        fig, ax = plt.subplots(figsize=(14, 8), facecolor='#0a1628')
        ax.set_facecolor('#0a1628')

        # Scatter plot with color gradient
        scatter = ax.scatter(df['flight_distance_km'], df['co2_total_kg']/1000,
                           c=df['flight_distance_km'], cmap='plasma',
                           s=100, alpha=0.7, edgecolors='white', linewidth=1)

        # Fit line
        z = np.polyfit(df['flight_distance_km'], df['co2_total_kg']/1000, 1)
        p = np.poly1d(z)
        x_line = np.linspace(df['flight_distance_km'].min(),
                            df['flight_distance_km'].max(), 100)
        ax.plot(x_line, p(x_line), color='#00cc66', linewidth=3,
               linestyle='--', label=f'Linear Fit: y = {z[0]:.3f}x + {z[1]:.1f}', alpha=0.9)

        # Calculate R²
        from scipy import stats
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df['flight_distance_km'], df['co2_total_kg']/1000)

        ax.text(0.05, 0.95, f'R² = {r_value**2:.3f}',
               transform=ax.transAxes, fontsize=16, fontweight='bold',
               verticalalignment='top', color='#00cc66',
               bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))

        ax.set_xlabel('Flight Distance (km)', fontsize=14, fontweight='bold', color='white')
        ax.set_ylabel('CO₂ Emissions (tonnes)', fontsize=14, fontweight='bold', color='white')
        ax.tick_params(colors='white', labelsize=12)
        ax.grid(True, alpha=0.2, color='white')
        ax.legend(fontsize=12, loc='lower right', framealpha=0.9)

        # Colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Distance (km)', fontsize=12, color='white')
        cbar.ax.tick_params(colors='white')

        for spine in ax.spines.values():
            spine.set_color('white')
            spine.set_linewidth(1)

        plt.tight_layout()
        output_file = output_dir / 'distance_emission.png'
        plt.savefig(output_file, dpi=200, bbox_inches='tight',
                   facecolor='#0a1628', edgecolor='none')
        plt.close()

        print(f"  [OK] Saved: {output_file}")

    except Exception as e:
        print(f"  [ERROR] {e}")


# ==================== 4. Carbon Market Comparison ====================
def generate_carbon_markets():
    """Generate clean carbon market comparison chart"""
    print("\n[4/5] Generating carbon market comparison...")

    try:
        df = pd.read_csv(base_dir / 'data/flights/carbon_market_comparison.csv')

        fig, ax = plt.subplots(figsize=(14, 8), facecolor='#0a1628')
        ax.set_facecolor('#0a1628')

        # Sort by cost
        df_sorted = df.sort_values('total_cost_usd', ascending=False)

        # Color mapping
        colors = ['#ff3333', '#ff9933', '#ffcc33', '#00cc66', '#0066cc']

        # Bar chart
        bars = ax.barh(df_sorted['market_name'], df_sorted['total_cost_usd'],
                      color=colors, alpha=0.8, edgecolor='white', linewidth=2)

        # Add value labels
        for i, (idx, row) in enumerate(df_sorted.iterrows()):
            ax.text(row['total_cost_usd'] + 5000, i,
                   f"${row['total_cost_usd']:,.0f}",
                   va='center', fontsize=12, fontweight='bold', color='white')

        ax.set_xlabel('Total Carbon Cost (USD)', fontsize=14, fontweight='bold', color='white')
        ax.tick_params(colors='white', labelsize=12)
        ax.grid(True, alpha=0.2, axis='x', color='white')

        # Add price per tonne annotations
        for i, (idx, row) in enumerate(df_sorted.iterrows()):
            ax.text(5000, i, f"${row['price_per_tonne_usd']}/tCO₂",
                   va='center', ha='left', fontsize=10,
                   color='white', style='italic',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.6))

        for spine in ax.spines.values():
            spine.set_color('white')
            spine.set_linewidth(1)

        plt.tight_layout()
        output_file = output_dir / 'carbon_markets.png'
        plt.savefig(output_file, dpi=200, bbox_inches='tight',
                   facecolor='#0a1628', edgecolor='none')
        plt.close()

        print(f"  [OK] Saved: {output_file}")

    except Exception as e:
        print(f"  [ERROR] {e}")


# ==================== 5. Top Emitters ====================
def generate_top_emitters():
    """Generate clean top emitters chart"""
    print("\n[5/5] Generating top emitters chart...")

    try:
        df = pd.read_csv(base_dir / 'data/flights/validation_emissions_results.csv')

        # Get top 10
        top10 = df.nlargest(10, 'co2_total_kg')

        fig, ax = plt.subplots(figsize=(14, 8), facecolor='#0a1628')
        ax.set_facecolor('#0a1628')

        # Create labels
        labels = []
        for _, row in top10.iterrows():
            callsign = row['callsign'] if pd.notna(row['callsign']) else 'N/A'
            typecode = row['typecode'] if pd.notna(row['typecode']) else 'N/A'
            labels.append(f"{callsign} ({typecode})")

        # Color gradient
        colors_grad = plt.cm.Reds(np.linspace(0.5, 1, len(top10)))

        # Bar chart
        bars = ax.barh(range(len(top10)), top10['co2_total_kg']/1000,
                      color=colors_grad, alpha=0.8, edgecolor='white', linewidth=2)

        # Add value labels
        for i, val in enumerate(top10['co2_total_kg']/1000):
            ax.text(val + 2, i, f'{val:.1f}t',
                   va='center', fontsize=11, fontweight='bold', color='white')

        ax.set_yticks(range(len(top10)))
        ax.set_yticklabels(labels)
        ax.set_xlabel('CO₂ Emissions (tonnes)', fontsize=14, fontweight='bold', color='white')
        ax.tick_params(colors='white', labelsize=11)
        ax.grid(True, alpha=0.2, axis='x', color='white')

        # Invert y-axis so highest is on top
        ax.invert_yaxis()

        for spine in ax.spines.values():
            spine.set_color('white')
            spine.set_linewidth(1)

        plt.tight_layout()
        output_file = output_dir / 'top_emitters.png'
        plt.savefig(output_file, dpi=200, bbox_inches='tight',
                   facecolor='#0a1628', edgecolor='none')
        plt.close()

        print(f"  [OK] Saved: {output_file}")

    except Exception as e:
        print(f"  [ERROR] {e}")


# ==================== Main ====================
if __name__ == "__main__":
    generate_fusion_image()
    generate_emission_charts()
    generate_distance_emission()
    generate_carbon_markets()
    generate_top_emitters()

    print("\n" + "="*70)
    print("All visualizations generated successfully!")
    print(f"Output directory: {output_dir.absolute()}")
    print("="*70)
    print("\nGenerated files:")
    for img in output_dir.glob('*.png'):
        size_mb = img.stat().st_size / (1024**2)
        print(f"  - {img.name} ({size_mb:.2f} MB)")
    print("="*70)
