import rasterio
import numpy as np
from PIL import Image
import os
import matplotlib.pyplot as plt
from rasterio.warp import transform_bounds
import pyproj


def get_landcover_class_names():
    """
    Get the class names for the land cover categories

    Returns:
        Dictionary mapping category values to class names
    """
    class_names = {
        1: "Open Bog",
        2: "Upland Mixedwood",
        3: "Open Water",
        4: "Emergent Marsh",
        5: "Shrubby Rich Fen",
        6: "Graminoid Rich Fen",
        7: "Treed Rich Fen",
        8: "Treed Bog",
        9: "Tamarack Swamp",
        10: "Upland Pine",
        11: "Treed Poor Fen",
        12: "Upland Conifer",
        13: "Shrubby Poor Fen",
        14: "Shrubby Bog",
        15: "Graminoid Poor Fen",
        16: "Upland Meadow",
        17: "Aquatic Bed",
        18: "Mixedwood Swamp",
        19: "Shrub Swamp",
        20: "Upland Deciduous",
        21: "Conifer Swamp",
        22: "Meadow Marsh",
        23: "Mudflats",
    }

    return class_names


def create_landcover_colormap():
    """
    Create a colormap for the land cover categories

    Returns:
        Dictionary mapping category values to RGB tuples
    """
    # Define the custom colormap based on provided RGB values
    colormap2 = {
        # BOG - Purple family (base: Treed Bog (8): (76, 0, 115))
        8: (76, 0, 115),  # Treed Bog - BASE COLOR - deep purple
        1: (96, 50, 175),  # Open Bog - bluer/brighter purple
        14: (106, 10, 125),  # Shrubby Bog - redder purple
        # FEN - Pink family (base: Treed Rich Fen (7): (214, 157, 188))
        # Rich Fens - darker
        7: (184, 127, 168),  # Treed Rich Fen - BASE COLOR - deeper magenta-pink
        5: (244, 127, 198),  # Shrubby Rich Fen - vibrant pure pink
        6: (224, 147, 128),  # Graminoid Rich Fen - salmon pink (yellow-orange tint)
        # Poor Fens - lighter versions with the same hue variations
        11: (204, 147, 188),  # Treed Poor Fen - lighter version of base
        13: (255, 157, 218),  # Shrubby Poor Fen - lighter version of Shrubby Rich
        15: (244, 167, 148),  # Graminoid Poor Fen - lighter version of Graminoid Rich
        # UPLAND - Green family (base: Upland Deciduous (20): (114, 137, 68))
        20: (114, 137, 68),  # Upland Deciduous - BASE COLOR
        16: (154, 177, 38),  # Upland Meadow - much more yellow-green
        2: (94, 147, 98),  # Upland Mixedwood - clear teal-green tint
        10: (144, 157, 28),  # Upland Pine - stronger yellow-olive green
        12: (74, 117, 88),  # Upland Conifer - definite blue-green
        # SWAMP - Reddish-Brown family (base: Mixedwood Swamp (18): (137, 68, 68))
        18: (137, 68, 68),  # Mixedwood Swamp - BASE COLOR - reddish-brown
        19: (167, 98, 38),  # Shrub Swamp - orange-brown
        9: (147, 78, 48),  # Tamarack Swamp - golden-brown (NO purple tones)
        21: (97, 38, 38),  # Conifer Swamp - darker brown
        # MARSH - Yellow/Orange family (base: Emergent Marsh (4): (245, 202, 122))
        4: (245, 202, 122),  # Emergent Marsh - BASE COLOR
        22: (215, 222, 82),  # Meadow Marsh - brighter, more distinct yellow
        # WATER - Blue family
        3: (52, 112, 185),  # Open Water - deeper blue
        17: (102, 162, 225),  # Aquatic Bed - medium blue
        23: (162, 212, 255),  # Mudflats - very light blue
    }
    return colormap2


# Scenario 1:
# - All upland land cover reclassified to upland deciduous
# - All wetlands (marsh, swamp, fen) land cover reclassified to meadow marsh
def scenario1_remap(class_id):
    # Upland classes (2, 10, 12, 16) -> Upland Deciduous (20)
    if class_id in [2, 10, 12, 16]:
        return 20

    # Wetland classes (4, 5, 6, 7, 9, 11, 13, 15, 18, 19, 21, 22) -> Meadow Marsh (22)
    if class_id in [1, 4, 5, 6, 7, 8, 9, 11, 13, 14, 15, 18, 19, 21, 22]:
        return 22

    # Keep others the same
    return class_id


# Scenario 2:
# - Shrubby rich fen reclassifies to shrubby poor fen
# - Treed rich fen reclassifies to treed poor fen
# - Graminoid rich fen reclassified to graminoid poor fen
# - Meadow marsh reclassified to upland meadow
def scenario2_remap(class_id):
    remap = {
        5: 13,  # Shrubby Rich Fen -> Shrubby Poor Fen
        7: 11,  # Treed Rich Fen -> Treed Poor Fen
        6: 15,  # Graminoid Rich Fen -> Graminoid Poor Fen
        22: 16,  # Meadow Marsh -> Upland Meadow
    }

    return remap.get(class_id, class_id)


# Scenario 3:
# - Shrubby rich and poor fens reclassified to shrubby bog
# - Treed rich and poor fens reclassified to treed bog
# - Graminoid rich and poor fens reclassified to open bog
# - Meadow marsh reclassified to upland deciduous
def scenario3_remap(class_id):
    remap = {
        5: 14,  # Shrubby Rich Fen -> Shrubby Bog
        13: 14,  # Shrubby Poor Fen -> Shrubby Bog
        7: 8,  # Treed Rich Fen -> Treed Bog
        11: 8,  # Treed Poor Fen -> Treed Bog
        6: 1,  # Graminoid Rich Fen -> Open Bog
        15: 1,  # Graminoid Poor Fen -> Open Bog
        22: 20,  # Meadow Marsh -> Upland Deciduous
    }

    return remap.get(class_id, class_id)


# Create new colormaps for each scenario
def create_remapped_colormap(remap_function):
    remapped_colormap = {}

    for class_id in get_landcover_class_names().keys():
        # Get the target class after remapping
        target_class = remap_function(class_id)
        # Use the color of the target class
        remapped_colormap[class_id] = create_landcover_colormap()[target_class]

    return remapped_colormap


colormap_scenario1 = create_remapped_colormap(scenario1_remap)
colormap_scenario2 = create_remapped_colormap(scenario2_remap)
colormap_scenario3 = create_remapped_colormap(scenario3_remap)
colormap_base = create_landcover_colormap()


def convert_landcover_tif_to_png(tif_path, output_png=None, colormap=None, debug=True):
    """
    Convert land cover GeoTIFF to PNG with the specified colors

    Args:
        tif_path: Path to GeoTIFF file
        output_png: Path to save PNG file (if None, will use tif_path with .png extension)
        colormap: Colormap to use (if None, will use base colormap)
        debug: Print debug information

    Returns:
        Path to the saved PNG file
    """
    if debug:
        print(f"Opening TIF: {tif_path}")

    if output_png is None:
        output_png = os.path.splitext(tif_path)[0] + ".png"

    if debug:
        print(f"Output PNG will be: {output_png}")

    if colormap is None:
        colormap = create_landcover_colormap()

    try:
        with rasterio.open(tif_path) as src:
            if debug:
                print(f"TIF opened successfully")
                print(f"CRS: {src.crs}")
                print(f"Dimensions: {src.width} x {src.height}")
                print(f"Bands: {src.count}")
                print(f"Nodata value: {src.nodata}")

            data = src.read(1)  # Land cover data is in the first band

            if debug:
                print(f"Data shape: {data.shape}")
                print(f"Data type: {data.dtype}")
                unique_values = np.unique(data)
                print(f"Unique values: {unique_values}")

            if src.nodata is not None:
                mask = data != src.nodata
            else:
                mask = np.ones_like(data, dtype=bool)

            rgb_img = np.zeros((data.shape[0], data.shape[1], 3), dtype=np.uint8)

            for val, color in colormap.items():
                idx = (data == val) & mask
                rgb_img[idx, 0] = color[0]  # R
                rgb_img[idx, 1] = color[1]  # G
                rgb_img[idx, 2] = color[2]  # B

            img = Image.fromarray(rgb_img)

            alpha = Image.fromarray((mask * 255).astype(np.uint8))

            img = img.convert("RGBA")
            img.putalpha(alpha)

            if debug:
                print(f"Saving PNG to: {output_png}")

            os.makedirs(os.path.dirname(os.path.abspath(output_png)), exist_ok=True)

            img.save(output_png)

            if debug:
                print(f"PNG saved successfully")

            return output_png

    except Exception as e:
        print(f"Error converting TIF to PNG: {str(e)}")
        raise


def overlay_images_with_color_change(
    base_image_path, overlay_image_path, output_path, color=(80, 80, 80)
):
    """
    Overlay the second image on top of the first one and change all colors
    in the overlay image to the specified color (default: dark gray).

    Args:
        base_image_path (str): Path to the base image
        overlay_image_path (str): Path to the overlay image
        output_path (str): Path to save the resulting image
        color (tuple): RGB color to change the overlay image to (default: dark gray)
    """
    print(f"Overlaying {overlay_image_path} on {base_image_path} with color {color}")

    base_img = Image.open(base_image_path).convert("RGBA")
    overlay_img = Image.open(overlay_image_path).convert("RGBA")

    if base_img.size != overlay_img.size:
        print(f"Resizing overlay from {overlay_img.size} to {base_img.size}")
        overlay_img = overlay_img.resize(base_img.size)

    overlay_array = np.array(overlay_img)

    mask = overlay_array[:, :, 3] > 0

    for i in range(3):  # RGB channels
        overlay_array[:, :, i][mask] = color[i]

    modified_overlay = Image.fromarray(overlay_array)

    result = Image.new("RGBA", base_img.size)
    result.paste(base_img, (0, 0))
    result.paste(modified_overlay, (0, 0), modified_overlay)

    result.save(output_path)

    print(f"Overlay image saved to {output_path}")

    return output_path


def get_bounds_from_tif(tif_path, debug=True):
    """
    Get bounds from the TIF file

    Args:
        tif_path: Path to GeoTIFF file
        debug: Print debug information

    Returns:
        bounds in format [[south, west], [north, east]] (Leaflet format)
    """
    try:
        with rasterio.open(tif_path) as src:
            if debug:
                print(f"Getting bounds from TIF: {tif_path}")
                print(f"CRS: {src.crs}")
                print(f"Transform: {src.transform}")
                print(f"Bounds: {src.bounds}")

            bounds = src.bounds

            if src.crs != "EPSG:4326":
                if debug:
                    print(f"Transforming bounds from {src.crs} to EPSG:4326")

                wgs84_bounds = transform_bounds(
                    src.crs,
                    "EPSG:4326",
                    bounds.left,
                    bounds.bottom,
                    bounds.right,
                    bounds.top,
                )

                west, south, east, north = wgs84_bounds
            else:
                west, south, east, north = (
                    bounds.left,
                    bounds.bottom,
                    bounds.right,
                    bounds.top,
                )

            leaflet_bounds = [[south, west], [north, east]]

            if debug:
                print(f"Leaflet bounds from TIF: {leaflet_bounds}")

            return leaflet_bounds

    except Exception as e:
        print(f"Error getting bounds from TIF: {str(e)}")
        raise


def generate_category_structures(colormap=None):
    """
    Generate SUBCATEGORIES and LEGEND_COLORS data structures from the base colormap

    Args:
        colormap: Colormap to use (if None, will use base colormap)

    Returns:
        Tuple of (SUBCATEGORIES, LEGEND_COLORS)
    """
    if colormap is None:
        colormap = create_landcover_colormap()

    class_names = get_landcover_class_names()

    category_mapping = {
        "Bog": [1, 8, 14],  # Open Bog, Treed Bog, Shrubby Bog
        "Fen": [5, 6, 7, 11, 13, 15],  # All Rich and Poor Fens
        "Upland": [2, 10, 12, 16, 20],  # All Upland types
        "Swamp": [9, 18, 19, 21],  # All Swamp types
        "Marsh": [4, 22],  # Emergent Marsh, Meadow Marsh
        "Water": [3, 17, 23],  # Open Water, Aquatic Bed, Mudflats
    }

    category_base_ids = {
        "Bog": 8,  # Treed Bog
        "Fen": 7,  # Treed Rich Fen
        "Upland": 20,  # Upland Deciduous
        "Swamp": 18,  # Mixedwood Swamp
        "Marsh": 4,  # Emergent Marsh
        "Water": 3,  # Open Water
    }

    # Generate SUBCATEGORIES structure
    subcategories = {}
    for category, class_ids in category_mapping.items():
        subcategories[category] = []
        for class_id in class_ids:
            subcategories[category].append(
                {
                    "id": class_id,
                    "name": class_names[class_id],
                    "color": colormap[class_id],
                }
            )

    legend_colors = {}
    for category, base_id in category_base_ids.items():
        legend_colors[category] = colormap[base_id]

    legend_colors["Unusable"] = (80, 80, 80)

    return subcategories, legend_colors


def generate_all_versions(
    tif_path, overlay_image_path, output_dir="output", debug=True
):
    """
    Generate all required versions of the landcover map

    Args:
        tif_path: Path to the input GeoTIFF file
        overlay_image_path: Path to the overlay image
        output_dir: Directory to save output files
        debug: Print debug information

    Returns:
        Dictionary of paths to all generated images
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    output_paths = {}

    output_paths["0_base"] = convert_landcover_tif_to_png(
        tif_path,
        output_png=os.path.join(output_dir, "0.png"),
        colormap=create_landcover_colormap(),
        debug=debug,
    )

    # 1: Base map with overlay
    output_paths["1_base_overlay"] = overlay_images_with_color_change(
        output_paths["0_base"],
        overlay_image_path,
        os.path.join(output_dir, "1.png"),
    )

    # 2: Scenario 1 remap
    output_paths["2_scenario1"] = convert_landcover_tif_to_png(
        tif_path,
        output_png=os.path.join(output_dir, "2.png"),
        colormap=colormap_scenario1,
        debug=debug,
    )

    # 3a: Scenario 2 remap
    output_paths["3a_scenario2"] = convert_landcover_tif_to_png(
        tif_path,
        output_png=os.path.join(output_dir, "3a.png"),
        colormap=colormap_scenario2,
        debug=debug,
    )

    # 3b: Scenario 3 remap
    output_paths["3b_scenario3"] = convert_landcover_tif_to_png(
        tif_path,
        output_png=os.path.join(output_dir, "3b.png"),
        colormap=colormap_scenario3,
        debug=debug,
    )

    # 4a: Scenario 2 with overlay
    output_paths["4a_scenario2_overlay"] = overlay_images_with_color_change(
        output_paths["3a_scenario2"],
        overlay_image_path,
        os.path.join(output_dir, "4a.png"),
    )

    # 4b: Scenario 3 with overlay
    output_paths["4b_scenario3_overlay"] = overlay_images_with_color_change(
        output_paths["3b_scenario3"],
        overlay_image_path,
        os.path.join(output_dir, "4b.png"),
    )

    return output_paths


if __name__ == "__main__":
    tif_path = ""
    overlay_image_path = ""

    output_paths = generate_all_versions(tif_path, overlay_image_path)

    print("\nGenerated files:")
    for name, path in output_paths.items():
        print(f"{name}: {path}")

    # Generate and print the SUBCATEGORIES and LEGEND_COLORS structures
    subcategories, legend_colors = generate_category_structures()

    print("\n# Copy and paste these structures into your app:")
    print("\nSUBCATEGORIES = {")
    for category, items in subcategories.items():
        print(f'    "{category}": [')
        for item in items:
            print(
                f'        {{"id": {item["id"]}, "name": "{item["name"]}", "color": {item["color"]}}},'
            )
        print("    ],")
    print("}")

    print("\nLEGEND_COLORS = {")
    for category, color in legend_colors.items():
        print(f'    "{category}": {color},')
    print("}")

    print("\nProcess completed successfully.")
