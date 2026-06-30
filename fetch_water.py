#!/usr/bin/env python3
"""
fetch_water.py  —  build water.json for Range Finder (run ONCE on a computer)
=============================================================================

Downloads streams/creeks and ponds/lakes for southern Butler County from the
USGS National Hydrography Dataset and writes a slim `water.json` that the web app
loads for its on-parcel "pond / creek" flags. Commit the resulting file next to
index.html in your repo.

    pip install requests
    python fetch_water.py
    # -> writes water.json  (then: git add water.json && commit & push)

Re-run occasionally to refresh. Glade Run proximity in the app does NOT need this.
"""

import json, sys, time
try:
    import requests
except ImportError:
    sys.exit("Run: pip install requests")

NHD = "https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer"
# Bounding box covering the target townships (minLng, minLat, maxLng, maxLat).
BBOX = (-80.22, 40.55, -79.55, 40.92)

# NHD FCodes that are perennial (year-round) — everything else flagged seasonal.
PERENNIAL_FCODES = {46006, 55800, 33600, 33601, 33603, 46000}

def layers():
    """Find the most-detailed Flowline and Waterbody layer ids in the service."""
    j = requests.get(NHD, params={"f": "json"}, timeout=60).json()
    flow = wb = None
    for lyr in j.get("layers", []):
        nm = (lyr.get("name") or "").lower()
        if "flowline" in nm and ("large" in nm or flow is None):
            flow = lyr["id"]
        if "waterbody" in nm and ("large" in nm or wb is None):
            wb = lyr["id"]
    if flow is None or wb is None:
        sys.exit(f"Couldn't find NHD layers (flow={flow}, waterbody={wb}).")
    return flow, wb

def query(layer_id):
    out, offset = [], 0
    while True:
        params = {
            "where": "1=1",
            "geometry": ",".join(map(str, BBOX)),
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326", "outSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "GNIS_NAME,FCODE",
            "returnGeometry": "true",
            "f": "geojson",
            "resultOffset": offset, "resultRecordCount": 1000,
        }
        r = requests.get(f"{NHD}/{layer_id}/query", params=params, timeout=120)
        r.raise_for_status()
        gj = r.json()
        feats = gj.get("features", [])
        out.extend(feats)
        if len(feats) < 1000:
            break
        offset += 1000
        time.sleep(0.3)
    return out

def flatten(geom):
    """Collect all [lng,lat] vertices from any GeoJSON geometry, rounded."""
    pts = []
    def walk(coords):
        if not coords:
            return
        if isinstance(coords[0], (int, float)):
            pts.append([round(coords[0], 5), round(coords[1], 5)])
        else:
            for c in coords:
                walk(c)
    if geom:
        walk(geom.get("coordinates"))
    return pts

def main():
    flow_id, wb_id = layers()
    print(f"NHD layers: flowline={flow_id}, waterbody={wb_id}")
    out = []
    for kind, lid in (("stream", flow_id), ("pond", wb_id)):
        print(f"  fetching {kind}s …", flush=True)
        for f in query(lid):
            props = f.get("properties", {}) or {}
            pts = flatten(f.get("geometry"))
            if not pts:
                continue
            try:
                fcode = int(props.get("FCODE") or props.get("fcode") or 0)
            except (TypeError, ValueError):
                fcode = 0
            out.append({
                "t": kind,
                "name": props.get("GNIS_NAME") or props.get("gnis_name") or "",
                "perennial": fcode in PERENNIAL_FCODES,
                "pts": pts,
            })
    with open("water.json", "w") as fh:
        json.dump({"features": out}, fh)
    print(f"Wrote water.json with {len(out)} water features.")

if __name__ == "__main__":
    main()
