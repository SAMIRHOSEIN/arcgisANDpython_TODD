"""DDOT CS-12 GIS test: read-only field inventory of ArcGIS Pro map layers.

Run inside an open ArcGIS Pro session (Python window), with the three
DDOT source services added to the active map.

Outputs are written to the reports/field_inventory directory alongside
3_ArcGIS_test's archispro directory, when that expected layout is found.
"""

import arcpy
import csv
import re
from pathlib import Path


TARGETS = {
    "roadway_subblocks": "roadwaysubblock",
    "construction_permits": "publicspaceconstructionpermits",
    "cityworks_requests": "cityworksrequest",
}


def normalized_name(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def main():
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    active_map = aprx.activeMap
    if active_map is None:
        maps = aprx.listMaps()
        if not maps:
            raise RuntimeError("No map found. Open the map with the three DDOT layers.")
        active_map = maps[0]

    project_dir = Path(aprx.filePath).resolve().parent
    # Expected: 3_ArcGIS_test/archispro/DDOT_CS12_GIS/DDOT_CS12_GIS.aprx
    if project_dir.parent.name.lower() == "archispro":
        workspace_dir = project_dir.parent.parent
    else:
        workspace_dir = project_dir
    out_dir = workspace_dir / "reports" / "field_inventory"
    out_dir.mkdir(parents=True, exist_ok=True)

    layers = [lyr for lyr in active_map.listLayers() if lyr.isFeatureLayer]
    print("Map:", active_map.name)
    print("Output directory:", out_dir)
    print("Feature layers found:", [lyr.name for lyr in layers])

    found = {}
    for layer in layers:
        norm = normalized_name(layer.name)
        for output_name, target in TARGETS.items():
            if target in norm and output_name not in found:
                found[output_name] = layer

    header = [
        "source_layer", "field_order", "field_name", "field_alias", "field_type",
        "field_length", "field_precision", "field_scale", "nullable",
        "required", "editable", "domain",
    ]
    all_rows = []
    for output_name, target in TARGETS.items():
        lyr = found.get(output_name)
        if lyr is None:
            print("NOT FOUND:", output_name, "(check the layer name in Contents)")
            continue
        try:
            fields = arcpy.ListFields(lyr)
        except Exception as exc:
            print("FAILED TO READ:", lyr.name, "-", exc)
            continue

        rows = []
        for order, field in enumerate(fields, start=1):
            rows.append([
                lyr.name, order, field.name, field.aliasName, field.type,
                field.length, field.precision, field.scale, field.isNullable,
                field.required, field.editable, field.domain,
            ])

        output = out_dir / (output_name + "_fields.csv")
        with output.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        all_rows.extend(rows)
        print("SUCCESS:", lyr.name, "-", len(rows), "fields ->", output)

    if all_rows:
        combined = out_dir / "all_ddot_fields.csv"
        with combined.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(all_rows)
        print("Combined field inventory:", combined)
    else:
        print("No field files created. Confirm the three layers are in the map.")


if __name__ == "__main__":
    main()
