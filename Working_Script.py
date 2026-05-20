import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

# ============================================================================
# PART 1: LOAD THE DATA
# ============================================================================
print("=" * 60)
print("GLOBAL SHIPPING LANES - COMPLETE ANALYSIS")
print("=" * 60)

# Load the shapefile
shipping_lanes = gpd.read_file("data/Shipping-Lanes-v1/Shipping-Lanes-v1.shp")

print(f"\n✓ Loaded {len(shipping_lanes)} shipping lane segments")

# ============================================================================
# PART 2: EXTRACT ATTRIBUTE DATA
# ============================================================================
print("\n" + "=" * 60)
print("PART 1: ATTRIBUTE DATA (What's in the dataset?)")
print("=" * 60)

# See all column names
print(f"\nColumn names: {shipping_lanes.columns.tolist()}")

# View the 'Type' column values (the main useful attribute)
print("\n📊 Shipping lane types breakdown:")
type_counts = shipping_lanes['Type'].value_counts()
for lane_type, count in type_counts.items():
    print(f"   {lane_type}: {count} segments")

# Export attribute table to CSV (no geometry)
shipping_lanes.drop('geometry', axis=1).to_csv("shipping_lanes_attributes.csv", index=False)
print("\n✓ Saved attribute data to 'shipping_lanes_attributes.csv'")

# ============================================================================
# PART 3: EXTRACT COORDINATES (Latitude/Longitude points)
# ============================================================================
print("\n" + "=" * 60)
print("PART 2: EXTRACT COORDINATES (Latitude/Longitude points)")
print("=" * 60)

# Extract all coordinates with their Type
coordinates_data = []

for _, row in shipping_lanes.iterrows():
    lane_type = row['Type']
    geom = row['geometry']

    if geom.geom_type == 'LineString':
        coordinates_data.extend(
            {'longitude': x, 'latitude': y, 'type': lane_type}
            for x, y in geom.coords
        )
    elif geom.geom_type == 'MultiLineString':
        coordinates_data.extend(
            {'longitude': x, 'latitude': y, 'type': lane_type}
            for line in geom.geoms
            for x, y in line.coords
        )

# Convert to DataFrame and save
coords_df = pd.DataFrame(coordinates_data)
coords_df.to_csv("shipping_lanes_coordinates.csv", index=False)

print(f"✓ Extracted {len(coords_df)} coordinate points")
print("✓ Saved coordinates to 'shipping_lanes_coordinates.csv'")

# Summary by type
print("\n📊 Coordinates by lane type:")
coord_counts = coords_df['type'].value_counts()
for lane_type, count in coord_counts.items():
    print(f"   {lane_type}: {count:,} points")

# Show sample coordinates
print("\n📍 Sample coordinates (first 10):")
print(coords_df.head(10).to_string(index=False))

# Find the bounding box (overall range)
print("\n🌍 Overall coordinate range:")
print(f"   Longitude: {coords_df['longitude'].min():.2f}° to {coords_df['longitude'].max():.2f}°")
print(f"   Latitude:  {coords_df['latitude'].min():.2f}° to {coords_df['latitude'].max():.2f}°")

# ============================================================================
# PART 4: VISUALIZE BY IMPORTANCE
# ============================================================================
print("\n" + "=" * 60)
print("PART 3: VISUALIZATION (Shipping lanes by importance)")
print("=" * 60)

# Create a color map
type_colors = {
    'Major': 'red',
    'Middle': 'orange', 
    'Minor': 'blue'
}

# Create line widths based on importance
type_linewidths = {
    'Major': 2.0,
    'Middle': 1.2, 
    'Minor': 0.5
}

# Create the plot
fig, ax = plt.subplots(1, 1, figsize=(16, 9))

# Plot each type separately
for lane_type, color in type_colors.items():
    subset = shipping_lanes[shipping_lanes['Type'] == lane_type]
    linewidth = type_linewidths[lane_type]
    
    if len(subset) > 0:
        subset.plot(ax=ax, color=color, linewidth=linewidth, 
                label=f"{lane_type} ({type_counts[lane_type]} segments)", alpha=0.8)

# Customize the plot
plt.title("Global Shipping Lanes by Importance", fontsize=16, fontweight='bold')
plt.xlabel("Longitude", fontsize=12)
plt.ylabel("Latitude", fontsize=12)
plt.legend(loc='lower left', fontsize=10)
plt.grid(True, alpha=0.3, linestyle='--')

# Add some context
plt.text(0.02, 0.98, f"Total segments: {len(shipping_lanes)}\nTotal points: {len(coords_df):,}", 
        transform=ax.transAxes, fontsize=9, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig("shipping_lanes_map.png", dpi=150, bbox_inches='tight')
plt.show()

print("\n✓ Saved map to 'shipping_lanes_map.png'")

# ============================================================================
# PART 5: STATISTICAL SUMMARY
# ============================================================================
print("\n" + "=" * 60)
print("PART 4: STATISTICAL SUMMARY")
print("=" * 60)

# Calculate total length by type (approximate, in degrees)
shipping_lanes['length_approx'] = shipping_lanes.geometry.length
length_by_type = shipping_lanes.groupby('Type')['length_approx'].sum().sort_values(ascending=False)

print("\n📏 Approximate total length by type (in degrees):")
for lane_type, length in length_by_type.items():
    print(f"   {lane_type}: {length:.2f}°")

print("\n" + "=" * 60)
print("✅ ANALYSIS COMPLETE!")
print("=" * 60)
print("\n📁 Files created:")
print("   1. shipping_lanes_attributes.csv - Attribute table (Type data)")
print("   2. shipping_lanes_coordinates.csv - All latitude/longitude points")
print("   3. shipping_lanes_map.png - Visual map of all routes")
print("\n💡 Next steps:")
print("   - Open 'shipping_lanes_coordinates.csv' in Excel to see all lat/lon points")
print("   - Use 'shipping_lanes_attributes.csv' to filter by Major/Minor routes")
print("   - The map shows red (Major) routes as thickest, blue (Minor) as thinnest")