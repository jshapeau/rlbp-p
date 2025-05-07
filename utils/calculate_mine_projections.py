#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Land Cover Development Impact Analysis

This script calculates how much area of each land cover class would be
affected by development represented in a second TIFF file.
"""

import rasterio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from rasterio.plot import show
from rasterio.windows import Window
from rasterio.mask import mask
import os
import sys
import json
from pathlib import Path


def find_common_bounds(src1, src2):
    """Find the overlapping bounds between two raster datasets."""
    # Get bounds as (left, bottom, right, top)
    bounds1 = src1.bounds
    bounds2 = src2.bounds

    # Find the overlapping region
    left = max(bounds1.left, bounds2.left)
    bottom = max(bounds1.bottom, bounds2.bottom)
    right = min(bounds1.right, bounds2.right)
    top = min(bounds1.top, bounds2.top)

    # Check if there's a valid overlap
    if left >= right or bottom >= top:
        raise ValueError("The TIFF files don't have an overlapping region.")

    return (left, bottom, right, top)


def bounds_to_window(src, bounds):
    """Convert geographic bounds to pixel window for a raster dataset."""
    left, bottom, right, top = bounds

    # Convert bounds to row/col pixel coordinates
    row_start, col_start = src.index(left, top)
    row_stop, col_stop = src.index(right, bottom)

    # Ensure proper ordering (start < stop)
    row_start, row_stop = min(row_start, row_stop), max(row_start, row_stop)
    col_start, col_stop = min(col_start, col_stop), max(col_start, col_stop)

    # Create window
    window = Window(col_start, row_start, col_stop - col_start, row_stop - row_start)
    return window


def calculate_impacted_land_cover(
    land_cover_tif,
    development_tif,
    land_cover_names=None,
    development_value=None,
    area_unit="ha",
    no_data_value=0,
):
    """
    Calculate the area of each land cover class that would be removed by development.

    Parameters:
    land_cover_tif (str): Path to the land cover TIFF file
    development_tif (str): Path to the development TIFF file
    land_cover_names (dict, optional): Dictionary mapping land cover class IDs to names
    development_value (int/float, optional): Specific value in development TIFF that represents development
    area_unit (str, optional): Unit for area measurement ('m²', 'ha', 'km²', 'acre')
    no_data_value (int/float, optional): Value representing no data in the land cover TIFF

    Returns:
    DataFrame: Contains each land cover class and the area that would be removed
    """
    print("Opening raster files...")
    try:
        # Open the raster files
        with rasterio.open(land_cover_tif) as land_src, rasterio.open(
            development_tif
        ) as dev_src:
            print(f"Land cover dimensions: {land_src.shape}")
            print(f"Development dimensions: {dev_src.shape}")

            # Check that the files have the same CRS
            if land_src.crs != dev_src.crs:
                raise ValueError(
                    f"The TIFF files have different coordinate reference systems: {land_src.crs} vs {dev_src.crs}"
                )

            # Find the common bounds between the two datasets
            print("Finding common area between the two datasets...")
            common_bounds = find_common_bounds(land_src, dev_src)
            print(f"Common bounds: {common_bounds}")

            # Replace with this:
            land_window = bounds_to_window(land_src, common_bounds)
            dev_window = bounds_to_window(dev_src, common_bounds)

            # Read the data within the common area
            land_cover = land_src.read(1, window=land_window)
            development = dev_src.read(1, window=dev_window)

            # Fix shape mismatch - ensure both arrays have the same dimensions
            min_rows = min(land_cover.shape[0], development.shape[0])
            min_cols = min(land_cover.shape[1], development.shape[1])

            # Trim both arrays to the same shape
            land_cover = land_cover[:min_rows, :min_cols]
            development = development[:min_rows, :min_cols]

            print(f"Adjusted common area dimensions: {land_cover.shape}")

            # Get no data value from the dataset if available
            if land_src.nodata is not None:
                no_data_value = land_src.nodata
                print(f"Using no data value from land cover TIFF: {no_data_value}")

            # Create a binary mask for development areas
            if development_value is not None:
                print(f"Using specific development value: {development_value}")
                dev_mask = development == development_value
            else:
                print("Using all non-zero values as development")
                dev_mask = development > 0

            # Print percentage of area covered by development
            dev_percentage = (np.sum(dev_mask) / dev_mask.size) * 100
            print(f"Development covers {dev_percentage:.2f}% of the common area")

            # Get the land cover classes within the development area
            impacted_land_cover = np.where(dev_mask, land_cover, no_data_value)

            # Get unique land cover classes (excluding no data values)
            print("Identifying unique land cover classes...")
            unique_classes = np.unique(land_cover)
            valid_classes = unique_classes[unique_classes != no_data_value]
            print(f"Found {len(valid_classes)} unique land cover classes")

            # Calculate pixel area (in square meters)
            pixel_area = abs(
                land_src.res[0] * land_src.res[1]
            )  # Use absolute value to ensure positive area

            # Convert to requested area unit
            conversion_factors = {
                "m²": 1.0,
                "ha": 0.0001,
                "km²": 0.000001,
                "acre": 0.000247105,
            }

            if area_unit not in conversion_factors:
                raise ValueError(
                    f"Unsupported area unit: {area_unit}. Supported units: {list(conversion_factors.keys())}"
                )

            area_factor = conversion_factors[area_unit]
            print(
                f"Pixel area: {pixel_area:.6f} m² ({pixel_area * area_factor:.6f} {area_unit})"
            )

            # Calculate area for each class
            print("Calculating areas for each land cover class...")
            results = []
            for lc_class in valid_classes:
                # Get class name if available
                class_id = str(
                    int(lc_class)
                    if isinstance(lc_class, (int, float)) and lc_class.is_integer()
                    else lc_class
                )
                class_name = (
                    land_cover_names.get(class_id, f"Class {lc_class}")
                    if land_cover_names
                    else f"Class {lc_class}"
                )

                # Count pixels for this class in the impacted area
                impacted_pixels = np.sum((land_cover == lc_class) & dev_mask)
                impacted_area = impacted_pixels * pixel_area * area_factor

                # Count total pixels for this class in the common area
                total_pixels = np.sum(land_cover == lc_class)
                total_area = total_pixels * pixel_area * area_factor

                # Calculate percentage
                percentage = (
                    (impacted_pixels / total_pixels) * 100 if total_pixels > 0 else 0
                )

                results.append(
                    {
                        "land_cover_class": lc_class,
                        "class_name": class_name,
                        "impacted_pixels": impacted_pixels,
                        "total_pixels": total_pixels,
                        f"impacted_area_{area_unit}": impacted_area,
                        f"total_area_{area_unit}": total_area,
                        "percentage_impacted": percentage,
                    }
                )

            # Create a result DataFrame and sort it
            df_results = pd.DataFrame(results)
            df_results.sort_values("percentage_impacted", ascending=False, inplace=True)

            return df_results, land_cover, dev_mask, impacted_land_cover

    except Exception as e:
        print(f"Error during raster analysis: {e}")
        raise


def create_visualizations(
    results, land_cover, dev_mask, impacted_land_cover, area_unit, output_dir
):
    """
    Create visualizations of the analysis results.
    """
    try:
        print("Creating visualizations...")

        # Create main visualization
        plt.figure(figsize=(16, 12))

        # Plot 1: Original land cover
        plt.subplot(221)
        show(
            land_cover,
            ax=plt.gca(),
            title="Original Land Cover (Common Area)",
            cmap="viridis",
        )

        # Plot 2: Development mask
        plt.subplot(222)
        show(dev_mask, ax=plt.gca(), title="Development Mask", cmap="binary")

        # Plot 3: Impacted land cover
        plt.subplot(223)
        show(
            impacted_land_cover,
            ax=plt.gca(),
            title="Impacted Land Cover",
            cmap="viridis",
        )

        # Plot 4: Bar chart of impacted areas
        plt.subplot(224)

        # Use only top 10 classes for readability
        plot_data = results.head(10).copy()
        plt.bar(plot_data["class_name"], plot_data[f"impacted_area_{area_unit}"])
        plt.xticks(rotation=90)
        plt.title(f"Top 10 Impacted Land Cover Classes ({area_unit})")
        plt.tight_layout()

        plt.savefig(os.path.join(output_dir, "land_cover_impact_overview.png"), dpi=300)
        print(
            f"Overview visualization saved to {output_dir}/land_cover_impact_overview.png"
        )

        # Create additional visualizations

        # Bar chart of percentage impacted
        plt.figure(figsize=(12, 8))
        plot_data = results.head(15).copy()  # Top 15 for readability
        plt.bar(plot_data["class_name"], plot_data["percentage_impacted"])
        plt.axhline(
            y=50, color="r", linestyle="--", alpha=0.7
        )  # Add a reference line at 50%
        plt.xticks(rotation=90)
        plt.title("Percentage of Land Cover Class Impacted by Development")
        plt.ylabel("Percentage (%)")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "percentage_impacted.png"), dpi=300)

        # Pie chart of impacted areas
        plt.figure(figsize=(12, 8))
        # Group small classes for readability
        threshold = results[f"impacted_area_{area_unit}"].sum() * 0.02  # 2% threshold
        plot_data = results.copy()
        small_classes_area = plot_data[
            plot_data[f"impacted_area_{area_unit}"] < threshold
        ][f"impacted_area_{area_unit}"].sum()
        plot_data = plot_data[
            plot_data[f"impacted_area_{area_unit}"] >= threshold
        ].copy()

        # Add a row for "Other" if small classes exist
        if small_classes_area > 0:
            other_row = pd.DataFrame(
                [
                    {
                        "class_name": "Other small classes",
                        f"impacted_area_{area_unit}": small_classes_area,
                    }
                ]
            )
            plot_data = pd.concat([plot_data, other_row])

        plt.pie(
            plot_data[f"impacted_area_{area_unit}"],
            labels=plot_data["class_name"],
            autopct="%1.1f%%",
            shadow=True,
        )
        plt.title(f"Distribution of Impacted Land Cover ({area_unit})")
        plt.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "impacted_area_distribution.png"), dpi=300)

        print(f"Additional visualizations saved to {output_dir}")

    except Exception as e:
        print(f"Warning: Could not create visualizations: {e}")


def main():
    """Main function to run the analysis."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Analyze the impact of development on land cover classes.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("land_cover", help="Path to the land cover TIFF file")
    parser.add_argument("development", help="Path to the development TIFF file")
    parser.add_argument(
        "--dev-value",
        type=float,
        help="Specific value in development TIFF that represents development (default: all non-zero values)",
    )
    parser.add_argument(
        "--output-dir", default="output", help="Directory for output files"
    )
    parser.add_argument(
        "--class-map", help="JSON file mapping land cover class IDs to names"
    )
    parser.add_argument(
        "--area-unit",
        default="ha",
        choices=["m²", "ha", "km²", "acre"],
        help="Unit for area measurements",
    )
    parser.add_argument(
        "--no-data",
        type=float,
        default=0,
        help="Value representing no data in the land cover TIFF",
    )
    parser.add_argument(
        "--no-viz", action="store_true", help="Skip visualization generation"
    )

    args = parser.parse_args()

    # Validate input files
    for file_path in [args.land_cover, args.development]:
        if not os.path.isfile(file_path):
            print(f"Error: File not found: {file_path}")
            return 1

    # Create output directory
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output will be saved to: {output_dir}")

    # Load land cover class names if provided
    land_cover_names = None
    if args.class_map:
        try:
            with open(args.class_map, "r") as f:
                land_cover_names = json.load(f)
            print(f"Loaded class names for {len(land_cover_names)} land cover classes")
        except Exception as e:
            print(f"Warning: Could not load class map: {e}")

    try:
        # Calculate impacted areas
        results, land_cover, dev_mask, impacted_land_cover = (
            calculate_impacted_land_cover(
                args.land_cover,
                args.development,
                land_cover_names=land_cover_names,
                development_value=args.dev_value,
                area_unit=args.area_unit,
                no_data_value=args.no_data,
            )
        )

        # Display results
        print("\nLand Cover Impact Analysis:")
        pd.set_option("display.max_rows", 20)  # Limit to 20 rows for display
        pd.set_option("display.width", 120)  # Wider display
        print(results)

        # Save results to CSV
        csv_path = os.path.join(output_dir, "land_cover_impact.csv")
        results.to_csv(csv_path, index=False)
        print(f"Results saved to {csv_path}")

        # Create visualizations if not disabled
        if not args.no_viz:
            create_visualizations(
                results,
                land_cover,
                dev_mask,
                impacted_land_cover,
                args.area_unit,
                output_dir,
            )

        # Generate summary report
        summary_path = os.path.join(output_dir, "summary_report.txt")
        with open(summary_path, "w") as f:
            f.write("Land Cover Impact Analysis Summary\n")
            f.write("=================================\n\n")
            f.write(f"Land cover file: {args.land_cover}\n")
            f.write(f"Development file: {args.development}\n")
            f.write(
                f"Analysis date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            )

            f.write(
                f"Total area analyzed: {results[f'total_area_{args.area_unit}'].sum():.2f} {args.area_unit}\n"
            )
            f.write(
                f"Total area impacted: {results[f'impacted_area_{args.area_unit}'].sum():.2f} {args.area_unit}\n"
            )
            f.write(
                f"Percentage of total area impacted: {(results[f'impacted_area_{args.area_unit}'].sum() / results[f'total_area_{args.area_unit}'].sum() * 100):.2f}%\n\n"
            )

            f.write("Most impacted land cover classes (by percentage):\n")
            for _, row in results.head(5).iterrows():
                f.write(
                    f"- {row['class_name']}: {row['percentage_impacted']:.2f}% ({row[f'impacted_area_{args.area_unit}']:.2f} {args.area_unit})\n"
                )

            f.write("\nMost impacted land cover classes (by area):\n")
            for _, row in (
                results.sort_values(f"impacted_area_{args.area_unit}", ascending=False)
                .head(5)
                .iterrows()
            ):
                f.write(
                    f"- {row['class_name']}: {row[f'impacted_area_{args.area_unit}']:.2f} {args.area_unit} ({row['percentage_impacted']:.2f}%)\n"
                )

        print(f"Summary report saved to {summary_path}")
        print("\nAnalysis complete!")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
