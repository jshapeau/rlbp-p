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
    colormap = {
        1: (76, 0, 115),  # Open Bog
        2: (114, 137, 68),  # Upland Mixedwood
        3: (122, 182, 245),  # Open Water
        4: (245, 202, 122),  # Emergent Marsh
        5: (214, 157, 188),  # Shrubby Rich Fen
        6: (214, 157, 188),  # Graminoid Rich Fen
        7: (214, 157, 188),  # Treed Rich Fen
        8: (76, 0, 115),  # Treed Bog
        9: (137, 68, 68),  # Tamarack Swamp
        10: (114, 137, 68),  # Upland Pine
        11: (214, 157, 188),  # Treed Poor Fen
        12: (114, 137, 68),  # Upland Conifer
        13: (214, 157, 188),  # Shrubby Poor Fen
        14: (76, 0, 115),  # Shrubby Bog
        15: (214, 157, 188),  # Graminoid Poor Fen
        16: (114, 137, 68),  # Upland Meadow
        17: (122, 182, 245),  # Aquatic Bed
        18: (137, 68, 68),  # Mixedwood Swamp
        19: (137, 68, 68),  # Shrub Swamp
        20: (114, 137, 68),  # Upland Deciduous
        21: (137, 68, 68),  # Conifer Swamp
        22: (245, 202, 122),  # Meadow Marsh
        23: (122, 182, 245),  # Mudflats
    }

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


# Generate the remapped colormaps
colormap_scenario1 = create_remapped_colormap(scenario1_remap)
colormap_scenario2 = create_remapped_colormap(scenario2_remap)
colormap_scenario3 = create_remapped_colormap(scenario3_remap)
colormap_base = create_landcover_colormap()


def convert_landcover_tif_to_png(tif_path, output_png=None, debug=True):
    """
    Convert land cover GeoTIFF to PNG with the correct colors

    Args:
        tif_path: Path to GeoTIFF file
        output_png: Path to save PNG file (if None, will use tif_path with .png extension)
        debug: Print debug information

    Returns:
        Path to the saved PNG file
    """
    if debug:
        print(f"Opening TIF: {tif_path}")

    # Ensure output path is set
    if output_png is None:
        output_png = os.path.splitext(tif_path)[0] + ".png"

    if debug:
        print(f"Output PNG will be: {output_png}")

    # Get the custom colormap
    colormap = colormap_base

    try:
        with rasterio.open(tif_path) as src:
            if debug:
                print(f"TIF opened successfully")
                print(f"CRS: {src.crs}")
                print(f"Dimensions: {src.width} x {src.height}")
                print(f"Bands: {src.count}")
                print(f"Nodata value: {src.nodata}")

            # Read the raster data
            data = src.read(1)  # Land cover data is in the first band

            if debug:
                print(f"Data shape: {data.shape}")
                print(f"Data type: {data.dtype}")
                unique_values = np.unique(data)
                print(f"Unique values: {unique_values}")

            # Create a mask for nodata values
            if src.nodata is not None:
                mask = data != src.nodata
            else:
                mask = np.ones_like(data, dtype=bool)

            # Create a colored image
            rgb_img = np.zeros((data.shape[0], data.shape[1], 3), dtype=np.uint8)

            # Apply colormap to each land cover class
            for val, color in colormap.items():
                idx = (data == val) & mask
                rgb_img[idx, 0] = color[0]  # R
                rgb_img[idx, 1] = color[1]  # G
                rgb_img[idx, 2] = color[2]  # B

            # Create PIL image
            img = Image.fromarray(rgb_img)

            # Create alpha channel from mask
            alpha = Image.fromarray((mask * 255).astype(np.uint8))

            # Apply alpha channel
            img = img.convert("RGBA")
            img.putalpha(alpha)

            # Save the image
            if debug:
                print(f"Saving PNG to: {output_png}")

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_png)), exist_ok=True)

            img.save(output_png)

            if debug:
                print(f"PNG saved successfully")

            return output_png

    except Exception as e:
        print(f"Error converting TIF to PNG: {str(e)}")
        raise


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

            # Get bounds from TIF
            bounds = src.bounds

            # Transform to WGS84 if necessary
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

            # Return in Leaflet format [[south, west], [north, east]]
            leaflet_bounds = [[south, west], [north, east]]

            if debug:
                print(f"Leaflet bounds from TIF: {leaflet_bounds}")

            return leaflet_bounds

    except Exception as e:
        print(f"Error getting bounds from TIF: {str(e)}")
        raise


def create_landcover_legend(output_path="landcover_legend.png"):
    """
    Create a legend image for the land cover classes

    Args:
        output_path: Path to save the legend image

    Returns:
        Path to the saved legend image
    """
    colormap = create_landcover_colormap()
    class_names = get_landcover_class_names()

    # Group classes with the same color
    color_groups = {}
    for val, color in colormap.items():
        color_key = str(color)
        if color_key not in color_groups:
            color_groups[color_key] = []
        color_groups[color_key].append(val)

    # Create a figure for the legend
    fig, ax = plt.figure(figsize=(8, 6)), plt.gca()

    # Plot each color group
    y_pos = 0
    for color_key, values in color_groups.items():
        color = eval(color_key)
        rgb_color = (color[0] / 255, color[1] / 255, color[2] / 255)

        # Get class names for this color group
        class_text = ", ".join([f"{val}: {class_names[val]}" for val in values])

        # Plot the color patch and text
        ax.add_patch(plt.Rectangle((0, y_pos), 0.3, 0.8, color=rgb_color))
        ax.text(0.4, y_pos + 0.4, class_text, va="center", fontsize=10)

        y_pos += 1

    # Set the figure properties
    ax.set_xlim(0, 4)
    ax.set_ylim(0, y_pos)
    ax.set_title("Land Cover Classes")
    ax.axis("off")

    # Save the figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close()

    return output_path


# Example usage
if __name__ == "__main__":
    # Path to your TIF file
    tif_path = "assets/LandCover_30m_reprojected.tif"

    # Convert TIF to PNG with custom colormap
    png_path = convert_landcover_tif_to_png(
        tif_path,
        output_png="testoo.png",  # Will use the same name with .png extension
        debug=True,
    )

    # Get bounds for Leaflet
    bounds = get_bounds_from_tif(tif_path, debug=True)

    # Create a legend
    legend_path = create_landcover_legend()

    print(f"\nFinal Results:")
    print(f"PNG created: {png_path}")
    print(f"Legend created: {legend_path}")
    print(f"Bounds for Leaflet: {bounds}")
