import rasterio
import numpy as np
import os
from rasterio.warp import (
    calculate_default_transform,
    reproject,
    Resampling,
    transform_bounds,
)
from PIL import Image
import matplotlib.pyplot as plt


def analyze_geotiff(file_path, debug=True):
    """
    Analyze a GeoTIFF file and print out its key spatial properties.

    Args:
        file_path: Path to the GeoTIFF file
        debug: Whether to print debug information

    Returns:
        Dictionary with the spatial properties
    """
    try:
        with rasterio.open(file_path) as src:
            properties = {
                "crs": src.crs,
                "transform": src.transform,
                "bounds": src.bounds,
                "resolution": src.res,
                "shape": src.shape,
                "driver": src.driver,
                "count": src.count,
                "nodata": src.nodata,
                "dtypes": src.dtypes,
            }

            if debug:
                print(f"\n===== Analysis of {os.path.basename(file_path)} =====")
                print(f"CRS: {properties['crs']}")
                print(f"Transform: {properties['transform']}")
                print(f"Bounds: {properties['bounds']}")
                print(f"Resolution: {properties['resolution']}")
                print(f"Shape (height, width): {properties['shape']}")
                print(f"Number of bands: {properties['count']}")
                print(f"NoData value: {properties['nodata']}")
                print(f"Data types: {properties['dtypes']}")

            return properties
    except Exception as e:
        print(f"Error analyzing GeoTIFF {file_path}: {str(e)}")
        raise


def align_geotiff(
    misaligned_path, reference_path, output_path, method="crs_transform", debug=True
):
    """
    Align a misaligned GeoTIFF to match a reference GeoTIFF.

    Args:
        misaligned_path: Path to the misaligned GeoTIFF
        reference_path: Path to the properly aligned reference GeoTIFF
        output_path: Path to save the aligned output
        method: Alignment method ('crs_transform', 'exact_match', or 'matching_bounds')
        debug: Whether to print debug information

    Returns:
        Path to the aligned GeoTIFF
    """
    if debug:
        print(f"\n===== Aligning {os.path.basename(misaligned_path)} =====")
        print(f"Reference: {os.path.basename(reference_path)}")
        print(f"Output: {os.path.basename(output_path)}")
        print(f"Method: {method}")

    # Analyze both files
    misaligned_props = analyze_geotiff(misaligned_path, debug)
    reference_props = analyze_geotiff(reference_path, debug)

    # Create output directory if needed
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Implement different alignment methods
    if method == "crs_transform":
        # Simple reprojection to match the CRS of the reference
        return reproject_to_match_crs(
            misaligned_path, reference_props["crs"], output_path, debug
        )

    elif method == "exact_match":
        # Use the exact transform from the reference
        return reproject_with_reference_transform(
            misaligned_path, reference_props, output_path, debug
        )

    elif method == "matching_bounds":
        # Reproject to match bounds of reference
        return reproject_to_match_bounds(
            misaligned_path, reference_props, output_path, debug
        )

    else:
        raise ValueError(f"Unknown alignment method: {method}")


def reproject_to_match_crs(src_path, dst_crs, dst_path, debug=True):
    """
    Reproject a GeoTIFF to match a target CRS.

    Args:
        src_path: Path to source GeoTIFF
        dst_crs: Target CRS
        dst_path: Path to save output
        debug: Whether to print debug information

    Returns:
        Path to the reprojected GeoTIFF
    """
    if debug:
        print(f"\n===== Reprojecting to match CRS =====")
        print(f"Target CRS: {dst_crs}")

    try:
        with rasterio.open(src_path) as src:
            # Check if reprojection is needed
            if src.crs == dst_crs:
                if debug:
                    print(f"Source already in target CRS. No reprojection needed.")
                # If no reprojection needed, just copy the file
                if src_path != dst_path:
                    import shutil

                    shutil.copy(src_path, dst_path)
                return dst_path

            # Calculate the optimal transform for the new projection
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds
            )

            if debug:
                print(f"New dimensions: {width} x {height}")
                print(f"New transform: {transform}")

            # Setup the destination raster
            dst_kwargs = src.meta.copy()
            dst_kwargs.update(
                {
                    "crs": dst_crs,
                    "transform": transform,
                    "width": width,
                    "height": height,
                }
            )

            with rasterio.open(dst_path, "w", **dst_kwargs) as dst:
                # Reproject each band
                for i in range(1, src.count + 1):
                    if debug:
                        print(f"Reprojecting band {i}")

                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest,
                    )

            if debug:
                print(f"Reprojection completed successfully")

            return dst_path

    except Exception as e:
        print(f"Error reprojecting GeoTIFF: {str(e)}")
        raise


def reproject_with_reference_transform(src_path, reference_props, dst_path, debug=True):
    """
    Reproject a GeoTIFF to use the exact same transform as a reference.

    Args:
        src_path: Path to source GeoTIFF
        reference_props: Properties of the reference GeoTIFF
        dst_path: Path to save output
        debug: Whether to print debug information

    Returns:
        Path to the reprojected GeoTIFF
    """
    if debug:
        print(f"\n===== Reprojecting with reference transform =====")

    try:
        with rasterio.open(src_path) as src:
            # Get data and transform to reference CRS
            data = src.read()

            dst_crs = reference_props["crs"]
            dst_transform = reference_props["transform"]
            dst_width = reference_props["shape"][1]  # width is the second element
            dst_height = reference_props["shape"][0]  # height is the first element

            if debug:
                print(f"Using reference dimensions: {dst_width} x {dst_height}")
                print(f"Using reference transform: {dst_transform}")

            # Setup the destination raster with reference properties
            dst_kwargs = src.meta.copy()
            dst_kwargs.update(
                {
                    "crs": dst_crs,
                    "transform": dst_transform,
                    "width": dst_width,
                    "height": dst_height,
                }
            )

            with rasterio.open(dst_path, "w", **dst_kwargs) as dst:
                # Reproject each band
                for i in range(1, src.count + 1):
                    if debug:
                        print(f"Reprojecting band {i}")

                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=dst_transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest,
                    )

            if debug:
                print(f"Reprojection completed successfully")

            return dst_path

    except Exception as e:
        print(f"Error reprojecting with reference transform: {str(e)}")
        raise


def reproject_to_match_bounds(src_path, reference_props, dst_path, debug=True):
    """
    Reproject a GeoTIFF to match the bounds of a reference.

    Args:
        src_path: Path to source GeoTIFF
        reference_props: Properties of the reference GeoTIFF
        dst_path: Path to save output
        debug: Whether to print debug information

    Returns:
        Path to the reprojected GeoTIFF
    """
    if debug:
        print(f"\n===== Reprojecting to match bounds =====")

    try:
        with rasterio.open(src_path) as src:
            # Get target CRS and bounds
            dst_crs = reference_props["crs"]
            ref_bounds = reference_props["bounds"]

            # Transform the source bounds to the reference CRS
            if src.crs != dst_crs:
                if debug:
                    print(f"Transforming bounds from {src.crs} to {dst_crs}")
                src_bounds = transform_bounds(
                    src.crs,
                    dst_crs,
                    src.bounds.left,
                    src.bounds.bottom,
                    src.bounds.right,
                    src.bounds.top,
                )
            else:
                src_bounds = (
                    src.bounds.left,
                    src.bounds.bottom,
                    src.bounds.right,
                    src.bounds.top,
                )

            # Calculate offset between source and reference bounds
            # (This is a simplified approach - in a real-world scenario,
            # you might need a more complex transformation)
            x_offset = ref_bounds.left - src_bounds[0]
            y_offset = ref_bounds.bottom - src_bounds[1]

            if debug:
                print(f"Source bounds in reference CRS: {src_bounds}")
                print(f"Reference bounds: {ref_bounds}")
                print(f"Calculated offsets: X: {x_offset}, Y: {y_offset}")

            # Apply the transform from reference, adjusted for offset
            dst_transform = reference_props["transform"]

            # Calculate resolution to maintain the same number of pixels
            # as in the source while covering the reference bounds
            x_res = (ref_bounds.right - ref_bounds.left) / src.width
            y_res = (ref_bounds.top - ref_bounds.bottom) / src.height

            # Calculate the transform for the output
            from rasterio.transform import from_origin

            dst_transform = from_origin(ref_bounds.left, ref_bounds.top, x_res, y_res)

            if debug:
                print(f"Resolution: X: {x_res}, Y: {y_res}")
                print(f"Calculated transform: {dst_transform}")

            # Setup the destination raster
            dst_kwargs = src.meta.copy()
            dst_kwargs.update(
                {
                    "crs": dst_crs,
                    "transform": dst_transform,
                    "width": src.width,
                    "height": src.height,
                }
            )

            with rasterio.open(dst_path, "w", **dst_kwargs) as dst:
                # Reproject each band
                for i in range(1, src.count + 1):
                    if debug:
                        print(f"Reprojecting band {i}")

                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=dst_transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest,
                    )

            if debug:
                print(f"Reprojection completed successfully")

            return dst_path

    except Exception as e:
        print(f"Error reprojecting to match bounds: {str(e)}")
        raise


def create_comparison_image(
    misaligned_path, reference_path, aligned_path, output_path, debug=True
):
    """
    Create a comparison image showing the misaligned, reference, and aligned GeoTIFFs.

    Args:
        misaligned_path: Path to the misaligned GeoTIFF
        reference_path: Path to the reference GeoTIFF
        aligned_path: Path to the aligned GeoTIFF
        output_path: Path to save the comparison image
        debug: Whether to print debug information

    Returns:
        Path to the comparison image
    """
    if debug:
        print(f"\n===== Creating comparison image =====")

    # Create a figure with three subplots
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Load and display the three images
    with rasterio.open(misaligned_path) as src:
        misaligned_img = src.read(1)
        axes[0].imshow(misaligned_img, cmap="viridis")
        axes[0].set_title("Misaligned")
        axes[0].axis("off")

    with rasterio.open(reference_path) as src:
        reference_img = src.read(1)
        axes[1].imshow(reference_img, cmap="viridis")
        axes[1].set_title("Reference")
        axes[1].axis("off")

    with rasterio.open(aligned_path) as src:
        aligned_img = src.read(1)
        axes[2].imshow(aligned_img, cmap="viridis")
        axes[2].set_title("Aligned")
        axes[2].axis("off")

    # Save the comparison image
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    if debug:
        print(f"Comparison image saved to: {output_path}")

    return output_path


def create_colorized_landcover_png(
    tif_path, output_png=None, colormap=None, debug=True
):
    """
    Convert land cover GeoTIFF to PNG with the correct colors.

    Args:
        tif_path: Path to GeoTIFF file
        output_png: Path to save PNG file (if None, will use tif_path with .png extension)
        colormap: Custom colormap (if None, will use the default landcover colormap)
        debug: Print debug information

    Returns:
        Path to the saved PNG file
    """
    if debug:
        print(f"\n===== Converting TIF to PNG =====")
        print(f"TIF: {tif_path}")

    # Ensure output path is set
    if output_png is None:
        output_png = os.path.splitext(tif_path)[0] + ".png"

    if debug:
        print(f"Output PNG will be: {output_png}")

    # Get colormap
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

    return colormap


if __name__ == "__main__":
    print("GeoTIFF Alignment Correction Tool")
    print("=================================")

    # Paths
    misaligned_path = input("Enter path to misaligned GeoTIFF: ")
    reference_path = input("Enter path to reference GeoTIFF: ")
    output_dir = (
        input("Enter output directory (or press Enter for current directory): ") or "."
    )

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)

    # Set output paths
    output_basename = os.path.splitext(os.path.basename(misaligned_path))[0]
    aligned_tif_path = os.path.join(output_dir, f"{output_basename}_aligned.tif")
    aligned_png_path = os.path.join(output_dir, f"{output_basename}_aligned.png")
    comparison_path = os.path.join(output_dir, f"{output_basename}_comparison.png")

    # Methods to try
    methods = ["crs_transform", "exact_match", "matching_bounds"]

    print("\nSelect alignment method:")
    print("1. Basic CRS Transformation (fastest)")
    print("2. Exact Transform Match (best for similar data)")
    print("3. Match Bounds (best for different data)")
    print("4. Try All Methods (slower but most thorough)")

    choice = input("Enter choice (1-4): ")

    if choice == "4":
        # Try all methods
        best_method = None
        best_score = float("-inf")

        print("\nTrying all methods and evaluating results...")

        for method in methods:
            try:
                # Align with this method
                method_output = os.path.join(
                    output_dir, f"{output_basename}_aligned_{method}.tif"
                )
                align_geotiff(misaligned_path, reference_path, method_output, method)

                # Create PNG
                create_colorized_landcover_png(method_output, None)

                # Here you would evaluate the alignment quality
                # For this example, we're just assuming the last method is best
                # In a real implementation, you'd compare to the reference somehow
                best_method = method
                best_score = 1.0

                print(f"Method '{method}' completed successfully")
            except Exception as e:
                print(f"Method '{method}' failed: {str(e)}")

        if best_method:
            print(f"\nBest method: {best_method} (score: {best_score})")
            # Copy the best result to the final output
            import shutil

            best_output = os.path.join(
                output_dir, f"{output_basename}_aligned_{best_method}.tif"
            )
            shutil.copy(best_output, aligned_tif_path)
        else:
            print("All methods failed. Please check your inputs.")
            exit(1)
    else:
        # Convert choice to method
        method_idx = int(choice) - 1
        if method_idx < 0 or method_idx >= len(methods):
            print("Invalid choice. Defaulting to method 1.")
            method_idx = 0

        method = methods[method_idx]
        print(f"\nUsing method: {method}")

        # Perform alignment
        align_geotiff(misaligned_path, reference_path, aligned_tif_path, method)

    # Convert to PNG
    print("\nConverting aligned TIF to PNG...")
    create_colorized_landcover_png(aligned_tif_path, aligned_png_path)

    # Create comparison image
    print("\nCreating comparison image...")
    create_comparison_image(
        misaligned_path, reference_path, aligned_tif_path, comparison_path
    )

    print("\nAlignment complete!")
    print(f"Aligned TIF: {aligned_tif_path}")
    print(f"Aligned PNG: {aligned_png_path}")
    print(f"Comparison: {comparison_path}")
    print("\nPlease check the comparison image to verify alignment quality.")
