import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from shapely.geometry import LineString, MultiLineString

# ============================================================================
# LOAD AND FILTER MAJOR SHIPPING ROUTES ONLY
# ============================================================================
print("=" * 60)
print("MAJOR SHIPPING ROUTES - WORLD MAP OVERLAY")
print("=" * 60)

# Load the shapefile
shipping_lanes = gpd.read_file("data/Shipping-Lanes-v1/Shipping-Lanes-v1.shp")

# Filter for Major routes only
major_routes = shipping_lanes[shipping_lanes['Type'] == 'Major'].copy()
print(f"\nOK Loaded {len(major_routes)} Major shipping route segments")

# ============================================================================
# SHOW THE SINGLE MAJOR VOYAGE ONLY
# ============================================================================
print("\n" + "=" * 60)
print("SHOWING THE SINGLE MAJOR VOYAGE")
print("=" * 60)

# If there is only one major route, use it directly as the single voyage.
# Otherwise, keep all major routes but do not attempt to split further.
if len(major_routes) == 1:
    voyages_gdf = major_routes.reset_index(drop=True).copy()
    voyages_gdf['voyage_id'] = 1
else:
    voyages_gdf = major_routes.reset_index(drop=True).copy()
    voyages_gdf['voyage_id'] = range(1, len(voyages_gdf) + 1)

# Add length information
voyages_gdf['length_degrees'] = voyages_gdf.geometry.length
voyages_gdf['length_km'] = voyages_gdf.geometry.length * 111  # Approximate conversion

print(f"\nVoyage statistics:")
print(f"   Number of major voyage segments: {len(voyages_gdf)}")
print(f"   Shortest voyage: {voyages_gdf['length_km'].min():.1f} km")
print(f"   Longest voyage: {voyages_gdf['length_km'].max():.1f} km")
print(f"   Average length: {voyages_gdf['length_km'].mean():.1f} km")

# ============================================================================
# CREATE WORLD MAP OVERLAY
# ============================================================================
print("\n" + "=" * 60)
print("CREATING WORLD MAP OVERLAY")
print("=" * 60)

# Load world map from naturalearth data
world = None
try:
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    print("OK Loaded Natural Earth world map")
except Exception as exc:
    print(f"WARNING: Could not load built-in world dataset: {exc}")
    print("OK Downloading world map from a public GeoJSON source...")
    world_url = 'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'
    try:
        world = gpd.read_file(world_url)
        print("OK Downloaded world map from GitHub")
    except Exception as exc2:
        print(f"WARNING: Failed to download world basemap: {exc2}")

if world is None:
    print("WARNING: Using fallback world map...")
    from shapely.geometry import Polygon
    world_coords = {
        'continent': ['Africa', 'Antarctica', 'Asia', 'Europe', 'North America', 'Oceania', 'South America'],
        'geometry': [
            Polygon([(-20, -35), (50, -35), (50, 35), (-20, 35), (-20, -35)]),  # Rough Africa
            Polygon([(-180, -90), (180, -90), (180, -60), (-180, -60), (-180, -90)]),  # Antarctica
            Polygon([(30, 0), (150, 0), (150, 70), (30, 70), (30, 0)]),  # Rough Asia
            Polygon([(-10, 35), (60, 35), (60, 70), (-10, 70), (-10, 35)]),  # Rough Europe
            Polygon([(-170, 15), (-60, 15), (-60, 70), (-170, 70), (-170, 15)]),  # Rough N America
            Polygon([(110, -40), (180, -40), (180, 0), (110, 0), (110, -40)]),  # Rough Oceania
            Polygon([(-80, -55), (-35, -55), (-35, 15), (-80, 15), (-80, -55)])  # Rough S America
        ]
    }
    world = gpd.GeoDataFrame(world_coords, crs='EPSG:4326')

# Ensure the basemap uses the same CRS as the shipping routes
if world.crs is None:
    world.set_crs('EPSG:4326', inplace=True)
elif world.crs.to_string() != 'EPSG:4326':
    world = world.to_crs('EPSG:4326')

# Helper to draw the world overlay with an ocean background
def plot_world_overlay(ax, world_gdf):
    ax.set_facecolor('#d6eaf8')  # soft ocean blue
    world_gdf.plot(ax=ax, color='#f2f2f2', edgecolor='gray', linewidth=0.4, zorder=0)
    world_gdf.boundary.plot(ax=ax, linewidth=0.6, edgecolor='gray', zorder=1)

# ============================================================================
# PLOT 1: ALL MAJOR ROUTES ON WORLD MAP
# ============================================================================
print("\n" + "=" * 60)
print("GENERATING VISUALIZATIONS")
print("=" * 60)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

# Plot 1: All major routes on world map
print("\nPlot 1: All Major routes on world map...")

# Plot world map overlay
plot_world_overlay(ax1, world)

# Plot major shipping routes with color gradient by length
sc = voyages_gdf.plot(ax=ax1, column='length_km', cmap='plasma', 
                      linewidth=3, alpha=0.9, zorder=2, legend=True,
                    legend_kwds={'label': 'Route Length (km)', 
                                'shrink': 0.6, 'pad': 0.02})

ax1.set_title("Major Global Shipping Routes\n(Colored by Voyage Length)", fontsize=14, fontweight='bold')
ax1.set_xlabel("Longitude")
ax1.set_ylabel("Latitude")
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.set_xlim([-180, 180])
ax1.set_ylim([-60, 80])

# ============================================================================
# PLOT 2: INDIVIDUAL VOYAGES (SPLIT AND NUMBERED)
# ============================================================================
print("Plot 2: Single major voyage route...")

# Create a color map for different voyages
colors = plt.cm.tab20(np.linspace(0, 1, len(voyages_gdf)))

# Plot world map overlay
plot_world_overlay(ax2, world)

# Plot each voyage with a different color and number
for idx, (i, row) in enumerate(voyages_gdf.iterrows()):
    # Plot the route
    if row.geometry.geom_type == 'LineString':
        x, y = row.geometry.xy
        ax2.plot(x, y, color=colors[idx], linewidth=2, alpha=0.85, zorder=2)
    elif row.geometry.geom_type == 'MultiLineString':
        for part in row.geometry.geoms:
            x, y = part.xy
            ax2.plot(x, y, color=colors[idx], linewidth=2, alpha=0.85, zorder=2)
        
    # Add label at midpoint for the whole voyage
    mid_point = row.geometry.interpolate(0.5, normalized=True)
    ax2.annotate(str(row['voyage_id']), 
                xy=(mid_point.x, mid_point.y),
                fontsize=8, ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7),
                zorder=3)

ax2.set_title("Single Major Shipping Voyage\n(Colored route segment)", fontsize=14, fontweight='bold')
ax2.set_xlabel("Longitude")
ax2.set_ylabel("Latitude")
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.set_xlim([-180, 180])
ax2.set_ylim([-60, 80])

plt.tight_layout()
plt.savefig("major_shipping_routes_world_map.png", dpi=150, bbox_inches='tight')
plt.close(fig)

print("OK Saved map to 'major_shipping_routes_world_map.png'")

# ============================================================================
# PLOT 3: DETAILED VOYAGE MAP WITH LEGEND
# ============================================================================
fig, ax3 = plt.subplots(1, 1, figsize=(18, 10))

# Plot world map overlay
plot_world_overlay(ax3, world)

# Create a more detailed visualization with size based on route length
if len(voyages_gdf) > 1:
    voyages_gdf.plot(ax=ax3, column='length_km', cmap='RdYlBu_r',
                     linewidth=3, alpha=0.9, zorder=2, legend=True,
                     legend_kwds={'label': 'Route Length (km)',
                                  'shrink': 0.6, 'pad': 0.02})
else:
    voyages_gdf.plot(ax=ax3, color='#d62728', linewidth=4,
                     alpha=0.9, zorder=2)

ax3.set_title("Single Major Shipping Voyage - Detailed View", 
             fontsize=14, fontweight='bold')
ax3.set_xlabel("Longitude")
ax3.set_ylabel("Latitude")
ax3.grid(True, alpha=0.3, linestyle='--')
ax3.set_xlim([-180, 180])
ax3.set_ylim([-60, 80])

plt.tight_layout()
plt.savefig("major_shipping_routes_detailed.png", dpi=150, bbox_inches='tight')
plt.close(ax3.figure)

print("OK Saved detailed map to 'major_shipping_routes_detailed.png'")

# ============================================================================
# EXPORT VOYAGE DATA
# ============================================================================
print("\n" + "=" * 60)
print("EXPORTING VOYAGE DATA")
print("=" * 60)

# Create a summary table of voyages
voyage_summary = []
for idx, row in voyages_gdf.iterrows():
    # Get bounds of the voyage
    bounds = row.geometry.bounds
    voyage_summary.append({
        'voyage_id': row['voyage_id'],
        'length_km': row['length_km'],
        'min_lon': bounds[0],
        'min_lat': bounds[1],
        'max_lon': bounds[2],
        'max_lat': bounds[3],
        'approx_region': f"{bounds[1]:.1f}° to {bounds[3]:.1f}° lat, {bounds[0]:.1f}° to {bounds[2]:.1f}° lon"
    })

summary_df = pd.DataFrame(voyage_summary)
summary_df = summary_df.sort_values('length_km', ascending=False)

# Save to CSV
summary_df.to_csv("major_voyages_summary.csv", index=False)
print("\nOK Saved voyage summary to 'major_voyages_summary.csv'")

# Export individual voyages as separate GeoJSON files
print("\nOK Exporting individual voyages as GeoJSON files...")
for idx, row in voyages_gdf.iterrows():
    if idx < 10:  # Export first 10 as examples
        voyage_gdf = gpd.GeoDataFrame([row], crs=shipping_lanes.crs)
        voyage_gdf.to_file(f"voyage_{row['voyage_id']}.geojson", driver="GeoJSON")
        print(f"   - Exported voyage {row['voyage_id']} to 'voyage_{row['voyage_id']}.geojson'")

# ============================================================================
# PRINT SUMMARY STATISTICS
# ============================================================================
print("\n" + "=" * 60)
print("FINAL SUMMARY")
print("=" * 60)

print("\nTop 10 Longest Major Shipping Voyages:")
print(summary_df.head(10).to_string(index=False))

print("\nOverall Statistics:")
print(f"   Total Major voyages: {len(voyages_gdf)}")
print(f"   Total route length: {voyages_gdf['length_km'].sum():.0f} km")
print(f"   Average voyage length: {voyages_gdf['length_km'].mean():.0f} km")
print(f"   Longest single voyage: {voyages_gdf['length_km'].max():.0f} km")
print(f"   Shortest single voyage: {voyages_gdf['length_km'].min():.0f} km")

print("\nAnalysis complete!")
print("\nFiles created:")
print("   1. major_shipping_routes_world_map.png - World map with colored routes")
print("   2. major_shipping_routes_detailed.png - Detailed voyage view")
print("   3. major_voyages_summary.csv - Summary table of all voyages")
print("   4. voyage_1.geojson, voyage_2.geojson, etc. - Individual voyage files")