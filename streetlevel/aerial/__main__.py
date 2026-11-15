# SURVAI: added module (not upstream).
"""
Command line entry point::

    python -m streetlevel.aerial PROVIDER NORTH WEST SOUTH EAST OUT [--zoom Z | --resolution M] [--max-zoom]

PROVIDER is one of bing, google, esri, usgs. ``--max-zoom`` only prints the highest available zoom level
at the center of the box.
"""
import argparse
import importlib
import json

from .util import ground_resolution, zoom_for_resolution

PROVIDERS = ("bing", "google", "esri", "usgs")


def main():
    parser = argparse.ArgumentParser(prog="python -m streetlevel.aerial",
                                     description="Download aerial imagery for a bounding box.")
    parser.add_argument("provider", choices=PROVIDERS)
    parser.add_argument("north", type=float)
    parser.add_argument("west", type=float)
    parser.add_argument("south", type=float)
    parser.add_argument("east", type=float)
    parser.add_argument("out", nargs="?", help="output .jpg, .png or .tif")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--zoom", type=int, help="zoom level")
    group.add_argument("--resolution", type=float, help="target ground resolution in m/px; picks the zoom level")
    group.add_argument("--max-zoom", action="store_true", help="print the highest available zoom level and exit")
    parser.add_argument("--max-tiles", type=int, default=20000)
    parser.add_argument("--max-concurrency", type=int, default=8)
    args = parser.parse_args()

    provider = importlib.import_module(f"streetlevel.aerial.{args.provider}")
    lat, lon = (args.north + args.south) / 2, (args.west + args.east) / 2

    if args.max_zoom:
        zoom = provider.find_max_zoom(lat, lon)
        res = None if zoom is None else round(ground_resolution(lat, zoom), 4)
        print(json.dumps({"provider": provider.PROVIDER, "max_zoom": zoom, "ground_resolution_m": res}))
        return
    if not args.out:
        parser.error("OUT is required unless --max-zoom is given")

    zoom = args.zoom
    if args.resolution is not None:
        zoom = zoom_for_resolution(lat, args.resolution)
    aerial = provider.download_image(args.north, args.west, args.south, args.east, args.out, zoom=zoom,
                                     max_tiles=args.max_tiles, max_concurrency=args.max_concurrency)
    print(json.dumps({"provider": aerial.provider, "zoom": aerial.zoom,
                      "ground_resolution_m": round(aerial.ground_resolution, 4),
                      "size_px": list(aerial.image.size), "tiles": aerial.tile_count,
                      "missing_tiles": len(aerial.missing_tiles), "metadata": aerial.metadata}))
    if aerial.missing_tiles:
        print(f"warning: {len(aerial.missing_tiles)} of {aerial.tile_count} tiles have no imagery "
              f"at zoom {aerial.zoom} (left black)")


if __name__ == "__main__":
    main()
