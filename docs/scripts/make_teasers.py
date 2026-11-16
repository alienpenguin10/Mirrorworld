"""
Regenerates the teaser images used in the documentation, with mirrorworld itself.

Only openly licensed sources are used (PDOK, AHN, NAIP, USGS 3DEP, Sentinel-2, Environment Agency, Mapillary,
OpenStreetMap); credits are written to docs/_static/teasers/credits.json and shown in the captions.

Run from the repository root (needs mirrorworld[all], matplotlib and MAPILLARY_ACCESS_TOKEN):

    python docs/scripts/make_teasers.py [name ...]
"""
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from PIL import Image, ImageDraw
from pyproj import Transformer

OUT = Path(__file__).resolve().parents[1] / "_static" / "teasers"
OUT.mkdir(parents=True, exist_ok=True)
CREDITS_FILE = OUT / "credits.json"
credits = json.loads(CREDITS_FILE.read_text()) if CREDITS_FILE.exists() else {}

DAM = (52.37365, 4.8912, 52.37275, 4.8935)            # Amsterdam, Dam square
SEATTLE_BLOCK = (47.6075, -122.3360, 47.6045, -122.3310)
SEATTLE_WIDE = (47.640, -122.360, 47.595, -122.290)
TRAFALGAR = (51.5090, -0.1300, 51.5072, -0.1262)
POLES = (47.6810, -122.3030, 47.6790, -122.2970)
VONDELPARK = (52.36060, 4.8740, 52.35880, 4.8790)      # Amsterdam, east end of Vondelpark
VOLUNTEER_PARK = (47.6330, -122.3200, 47.6290, -122.3120)


def save(image: Image.Image, name: str, credit: str, width: int = 1200):
    if image.width > width:
        image = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
    image.convert("RGB").save(OUT / f"{name}.jpg", quality=80, optimize=True, progressive=True)
    credits[name] = credit
    CREDITS_FILE.write_text(json.dumps(credits, indent=2, sort_keys=True))
    print("wrote", name, image.size)


def colorize(values, valid, cmap, vmin, vmax):
    norm = np.clip((values - vmin) / (vmax - vmin), 0, 1)
    rgba = (plt.get_cmap(cmap)(norm) * 255).astype(np.uint8)
    rgba[~valid] = (20, 22, 30, 255)
    return Image.fromarray(rgba[..., :3])


def to_pixel(raster, crs):
    """Returns a function mapping (lon, lat) to pixel coordinates of a north-up raster."""
    tf = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    a, _, xoff, _, e, yoff = raster.transform

    def f(lon, lat):
        x, y = tf.transform(lon, lat)
        return (x - xoff) / a, (y - yoff) / e
    return f


def amsterdam():
    from mirrorworld.aerial import pdok
    rgb = pdok.get_raster(*DAM, resolution=0.08)
    save(rgb.to_image(), "amsterdam_rgb", "PDOK / Beeldmateriaal Nederland, CC BY 4.0")
    cir = pdok.get_raster(*VONDELPARK, resolution=0.08, infrared=True)
    save(cir.to_image(), "amsterdam_cir", "PDOK / Beeldmateriaal Nederland, CC BY 4.0")
    return rgb


def amsterdam_heights():
    from mirrorworld.elevation import ahn
    ndsm = ahn.get_ndsm(*DAM)
    v = ndsm.data[0]
    image = colorize(v, v != ndsm.nodata, "magma", 0, 35)
    save(image.resize((image.width * 4, image.height * 4), Image.BICUBIC), "amsterdam_ndsm", "AHN via PDOK, CC0")


def amsterdam_osm(rgb=None):
    from mirrorworld.aerial import pdok
    from mirrorworld.vector import osm
    rgb = rgb or pdok.get_raster(*DAM, resolution=0.08)
    image = rgb.to_image().convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    px = to_pixel(rgb, rgb.crs)
    fc = osm.find_features(*DAM, {"building": True, "highway": ["footway", "pedestrian", "crossing"],
                                  "railway": "tram"})
    for f in fc["features"]:
        g, p = f["geometry"], f["properties"]
        if g["type"] == "Polygon":
            draw.polygon([px(*c) for c in g["coordinates"][0]], fill=(255, 190, 60, 70), outline=(255, 190, 60, 255))
        elif g["type"] == "LineString":
            color = (80, 200, 255, 255) if "railway" in p else (120, 255, 160, 255)
            draw.line([px(*c) for c in g["coordinates"]], fill=color, width=6)
    save(Image.alpha_composite(image, overlay), "amsterdam_osm",
         "PDOK, CC BY 4.0; (c) OpenStreetMap contributors, ODbL")


def mapillary_detections():
    from mirrorworld import mapillary
    features = mapillary.find_map_features(47.68, -122.30, radius=150, values=["object--support--utility-pole"])
    feature = mapillary.find_map_feature_by_id(features[0].id)
    pano = mapillary.find_panorama_by_id(feature.image_ids[0])
    image = mapillary.get_panorama(pano, size="2048").convert("RGBA")
    W, H = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    palette = {"construction--flat--road": (255, 70, 90, 110), "construction--flat--sidewalk": (80, 255, 140, 120),
               "nature--sky": (70, 150, 255, 70), "nature--vegetation": (60, 200, 80, 90),
               "object--support--utility-pole": (255, 230, 0, 200), "object--street-light": (255, 140, 0, 200),
               "construction--barrier--curb": (255, 255, 255, 160), "object--vehicle--car": (180, 90, 255, 120)}
    for det in mapillary.get_detections(pano):
        color = palette.get(det.value)
        if color:
            for polygon in det.polygons:
                draw.polygon([(x * W, y * H) for x, y in polygon[0]], fill=color)
    save(Image.alpha_composite(image, overlay), "mapillary_detections",
         f"Mapillary, image by {pano.creator_username or 'a Mapillary contributor'}, CC BY-SA 4.0")


def naip_poles():
    from mirrorworld import mapillary
    from mirrorworld.satellite import naip
    r = naip.get_raster(*POLES)
    image = Image.fromarray(np.moveaxis(r.data[[0, 1, 2]], 0, -1)).convert("RGBA")
    draw = ImageDraw.Draw(image)
    px = to_pixel(r, r.crs)
    lat, lon = (POLES[0] + POLES[2]) / 2, (POLES[1] + POLES[3]) / 2
    style = {"object--support--utility-pole": (255, 220, 0), "object--manhole": (90, 200, 255),
             "object--street-light": (255, 120, 60), "object--junction-box": (255, 80, 200)}
    for f in mapillary.find_map_features(lat, lon, radius=300, values=list(style)):
        x, y = px(f.lon, f.lat)
        if 0 <= x < image.width and 0 <= y < image.height:
            c = style[f.value]
            draw.ellipse([x - 7, y - 7, x + 7, y + 7], fill=c + (255,), outline=(0, 0, 0, 255), width=2)
    save(image, "naip_poles", "USDA NAIP, public domain; Mapillary map features, CC BY-SA 4.0")


def naip_false_color():
    from mirrorworld.satellite import naip
    r = naip.get_raster(*VOLUNTEER_PARK)
    nir, red, green = r.data[3], r.data[0], r.data[1]
    save(Image.fromarray(np.dstack([nir, red, green])), "naip_false_color", "USDA NAIP, public domain")


def sentinel2_ndvi():
    from mirrorworld.satellite import sentinel2
    r = sentinel2.get_raster(*SEATTLE_WIDE, bands=("red", "nir"), start="2025-06-01", end="2025-09-30")
    info = r.metadata["band_info"]
    red = r.band("red") * info["red"].get("scale", 1e-4) + info["red"].get("offset", 0)
    nir = r.band("nir") * info["nir"].get("scale", 1e-4) + info["nir"].get("offset", 0)
    ndvi = (nir - red) / np.maximum(nir + red, 1e-6)
    image = np.array(colorize(ndvi, np.isfinite(ndvi), "RdYlGn", 0.0, 0.8))
    image[ndvi < 0.0] = (24, 46, 92)          # water in dark blue rather than "bare" red
    image = Image.fromarray(image)
    save(image.resize((image.width * 3, image.height * 3), Image.NEAREST), "sentinel2_ndvi",
         "Contains modified Copernicus Sentinel data 2025")


def lidar_city():
    from mirrorworld.lidar import usgs3dep
    las = usgs3dep.get_points(*SEATTLE_BLOCK, resolution=1.5)
    x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
    keep = np.random.default_rng(0).choice(len(x), size=min(len(x), 260_000), replace=False)
    x, y, z = x[keep] - x.mean(), y[keep] - y.mean(), z[keep]
    fig = plt.figure(figsize=(12, 7.5), dpi=170, facecolor="#0b0d14")
    ax = fig.add_subplot(projection="3d", facecolor="#0b0d14")
    ax.scatter(x, y, z, c=z, cmap="turbo", s=0.18, linewidths=0, norm=colors.PowerNorm(0.6, vmin=np.percentile(z, 1),
                                                                                       vmax=np.percentile(z, 99.5)))
    ax.view_init(elev=28, azim=-58)
    ax.set_box_aspect((np.ptp(x), np.ptp(y), np.ptp(z) * 1.2))
    ax.set_axis_off()
    plt.subplots_adjust(0, 0, 1, 1)
    fig.canvas.draw()
    image = Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert("RGB")
    plt.close(fig)
    bbox = Image.eval(image, lambda v: 255 if v > 30 else 0).convert("L").getbbox()
    save(image.crop(bbox) if bbox else image, "lidar_city", "USGS 3DEP (King County 2021), public domain")


def london_heights():
    from mirrorworld.elevation import ea
    ndsm = ea.get_ndsm(*TRAFALGAR)
    v = ndsm.data[0]
    image = colorize(v, v != ndsm.nodata, "viridis", 0, 40)
    save(image.resize((image.width * 4, image.height * 4), Image.BICUBIC), "london_ndsm",
         "Environment Agency LiDAR, Open Government Licence v3.0")


def wayback_timeline():
    from mirrorworld.aerial import wayback
    sites = {"London, Charing Cross": (51.5074, -0.1278), "Ipswich": (52.0567, 1.1545),
             "Seattle, downtown": (47.6062, -122.3321)}
    fig, ax = plt.subplots(figsize=(12, 3.6), dpi=110)
    fig.patch.set_alpha(0)
    for i, (name, (lat, lon)) in enumerate(sites.items()):
        dates = [v.capture_date for v in wayback.find_versions(lat, lon) if v.capture_date]
        ax.plot(dates, [i] * len(dates), "-", color="#7c8cff", alpha=0.35, linewidth=2)
        ax.scatter(dates, [i] * len(dates), s=120, color="#6c5cff", edgecolor="white", linewidth=1.5, zorder=3)
    ax.set_yticks(range(len(sites)), list(sites))
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors="#8a8fa3")
    ax.set_title("Distinct aerial captures found by wayback.find_versions()", color="#8a8fa3", loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "wayback_timeline.png", transparent=True)
    plt.close(fig)
    credits["wayback_timeline"] = "Capture dates from Esri World Imagery Wayback metadata"
    CREDITS_FILE.write_text(json.dumps(credits, indent=2, sort_keys=True))
    print("wrote wayback_timeline")


STEPS = {"amsterdam": amsterdam, "amsterdam_heights": amsterdam_heights, "amsterdam_osm": amsterdam_osm,
         "mapillary_detections": mapillary_detections, "naip_poles": naip_poles,
         "naip_false_color": naip_false_color, "sentinel2_ndvi": sentinel2_ndvi, "lidar_city": lidar_city,
         "london_heights": london_heights, "wayback_timeline": wayback_timeline}

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    for name in sys.argv[1:] or STEPS:
        try:
            STEPS[name]()
        except Exception as e:  # keep going so one flaky service does not block the rest
            print("FAILED", name, type(e).__name__, e)
