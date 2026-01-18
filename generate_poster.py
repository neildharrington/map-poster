#!/usr/bin/env python3
"""Generate minimalist map posters of any city with tech-inspired aesthetics."""

import argparse
import osmnx as ox
import matplotlib.pyplot as plt
import numpy as np

# Tech Minimalist Theme
THEME = {
    'background': '#0d1b2a',      # Deep navy
    'water': '#1b4965',           # Teal
    'parks': '#1e3a2f',           # Dark forest green
    'roads': {
        'motorway': '#00d4ff',    # Bright cyan
        'trunk': '#00c4ec',
        'primary': '#00b4d8',
        'secondary': '#0096c7',
        'tertiary': '#0077b6',
        'residential': '#023e8a',  # Darker blue for minor roads
        'default': '#014f86'
    },
    'road_widths': {
        'motorway': 2.5,
        'trunk': 2.0,
        'primary': 1.5,
        'secondary': 1.2,
        'tertiary': 0.8,
        'residential': 0.3,
        'default': 0.2
    },
    'text': '#e0fbfc',            # Light cyan
    'text_shadow': '#1b4965'
}


def get_road_style(highway_type):
    """Get color and width for a road type."""
    if isinstance(highway_type, list):
        highway_type = highway_type[0]

    color = THEME['roads'].get(highway_type, THEME['roads']['default'])
    width = THEME['road_widths'].get(highway_type, THEME['road_widths']['default'])

    return color, width


def geocode_city(city_name):
    """Geocode a city name to coordinates."""
    print(f"Geocoding '{city_name}'...")
    try:
        location = ox.geocode(city_name)
        print(f"  Found: {location[0]:.4f}, {location[1]:.4f}")
        return location
    except Exception as e:
        raise ValueError(f"Could not find location: {city_name}") from e


def fetch_map_data(center, radius_km):
    """Fetch street network and features from OpenStreetMap."""
    print(f"Fetching map data for {radius_km}km radius...")

    # Get street network
    print("  - Street network...")
    G = ox.graph_from_point(center, dist=radius_km * 1000, network_type='all')

    # Get water features
    print("  - Water features...")
    try:
        water = ox.features_from_point(
            center,
            tags={'natural': 'water'},
            dist=radius_km * 1000
        )
    except Exception:
        water = None

    # Get parks
    print("  - Parks and green spaces...")
    try:
        parks = ox.features_from_point(
            center,
            tags={'leisure': 'park'},
            dist=radius_km * 1000
        )
    except Exception:
        parks = None

    return G, water, parks


def render_poster(G, water, parks, output_path, dpi, city_name, state_or_country, coords, show_labels=True):
    """Render the map poster."""
    print("Rendering poster...")

    # Create figure with poster proportions (18x24 inches)
    fig, ax = plt.subplots(figsize=(18, 24), facecolor=THEME['background'])
    ax.set_facecolor(THEME['background'])

    # Remove axes
    ax.set_axis_off()

    # Get edges for plotting
    edges = ox.graph_to_gdfs(G, nodes=False)

    # Plot water features first (background layer)
    if water is not None and len(water) > 0:
        print("  - Drawing water...")
        try:
            water.plot(ax=ax, color=THEME['water'], alpha=0.8)
        except Exception:
            pass

    # Plot parks
    if parks is not None and len(parks) > 0:
        print("  - Drawing parks...")
        try:
            parks.plot(ax=ax, color=THEME['parks'], alpha=0.6)
        except Exception:
            pass

    # Plot roads by type (from smallest to largest for proper layering)
    print("  - Drawing roads...")
    road_order = ['residential', 'tertiary', 'secondary', 'primary', 'trunk', 'motorway']

    for road_type in road_order:
        mask = edges['highway'].apply(
            lambda x: (x == road_type) if isinstance(x, str)
            else (road_type in x if isinstance(x, list) else False)
        )
        subset = edges[mask]

        if len(subset) > 0:
            color, width = get_road_style(road_type)
            subset.plot(ax=ax, color=color, linewidth=width, alpha=0.9)

    # Plot remaining roads
    plotted_types = set(road_order)
    mask = edges['highway'].apply(
        lambda x: (x not in plotted_types) if isinstance(x, str)
        else (not any(t in plotted_types for t in x) if isinstance(x, list) else True)
    )
    remaining = edges[mask]
    if len(remaining) > 0:
        remaining.plot(ax=ax, color=THEME['roads']['default'],
                      linewidth=THEME['road_widths']['default'], alpha=0.7)

    # Add text labels
    if show_labels:
        print("  - Adding labels...")

        # Get plot bounds for text positioning
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        # City name - large, at bottom
        ax.text(
            (xlim[0] + xlim[1]) / 2,
            ylim[0] + (ylim[1] - ylim[0]) * 0.06,
            city_name.upper(),
            fontsize=72,
            fontweight='bold',
            color=THEME['text'],
            ha='center',
            va='bottom',
            fontfamily='sans-serif'
        )

        # Coordinates - smaller, below city name
        lat_dir = 'N' if coords[0] >= 0 else 'S'
        lon_dir = 'W' if coords[1] < 0 else 'E'
        coord_text = f"{abs(coords[0]):.4f}°{lat_dir}  {abs(coords[1]):.4f}°{lon_dir}"
        ax.text(
            (xlim[0] + xlim[1]) / 2,
            ylim[0] + (ylim[1] - ylim[0]) * 0.03,
            coord_text,
            fontsize=24,
            color=THEME['text'],
            ha='center',
            va='bottom',
            fontfamily='sans-serif',
            alpha=0.7
        )

        # State/Country - top
        ax.text(
            (xlim[0] + xlim[1]) / 2,
            ylim[1] - (ylim[1] - ylim[0]) * 0.03,
            state_or_country.upper(),
            fontsize=28,
            color=THEME['text'],
            ha='center',
            va='top',
            fontfamily='sans-serif',
            alpha=0.6
        )

    # Tight layout
    plt.tight_layout(pad=1)

    # Save
    print(f"  - Saving to {output_path}...")
    plt.savefig(
        output_path,
        dpi=dpi,
        facecolor=THEME['background'],
        edgecolor='none',
        bbox_inches='tight',
        pad_inches=0.5
    )
    plt.close()

    print(f"Done! Saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate minimalist map posters of any city'
    )
    parser.add_argument(
        'city',
        help='City name (e.g., "San Jose, California, USA" or "Paris, France")'
    )
    parser.add_argument(
        '--label', type=str, default=None,
        help='City label for poster (default: extracted from city name)'
    )
    parser.add_argument(
        '--region', type=str, default=None,
        help='Region/state/country label for top of poster (default: extracted from city name)'
    )
    parser.add_argument(
        '--radius', type=int, default=20,
        help='Radius in kilometers from city center (default: 20)'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Output filename (default: <city>_poster.png)'
    )
    parser.add_argument(
        '--dpi', type=int, default=150,
        help='Resolution in DPI (default: 150, use 300 for print)'
    )
    parser.add_argument(
        '--no-labels', action='store_true',
        help='Omit city name and coordinates'
    )

    args = parser.parse_args()

    # Parse city name for labels
    parts = [p.strip() for p in args.city.split(',')]
    city_label = args.label or parts[0]
    region_label = args.region or (parts[1] if len(parts) > 1 else '')

    # Default output filename
    if args.output is None:
        safe_name = city_label.lower().replace(' ', '_').replace("'", '')
        args.output = f"{safe_name}_poster.png"

    print(f"\n{'='*50}")
    print("  MAP POSTER GENERATOR")
    print("  Tech Minimalist Theme")
    print(f"{'='*50}\n")

    # Geocode
    coords = geocode_city(args.city)

    # Fetch data
    G, water, parks = fetch_map_data(coords, args.radius)

    # Render
    render_poster(
        G, water, parks,
        output_path=args.output,
        dpi=args.dpi,
        city_name=city_label,
        state_or_country=region_label,
        coords=coords,
        show_labels=not args.no_labels
    )

    print(f"\nPoster specifications:")
    print(f"  - City: {city_label}")
    print(f"  - Center: {coords[0]:.4f}, {coords[1]:.4f}")
    print(f"  - Radius: {args.radius} km")
    print(f"  - Resolution: {args.dpi} DPI")
    print(f"  - Theme: Tech Minimalist (dark + cyan)")


if __name__ == '__main__':
    main()
