from typing import List, Dict, Optional
import pandas as pd
import numpy as np


class BisonDataFrame:
    """
    Represents the state of the dataframe modeling bison density and population.

    This class encapsulates all dataframe operations for the bison model,
    handling area calculations, percentage distributions, density updates,
    and tracking changes between scenarios.
    """

    def __init__(self, data: List[Dict]):
        self.df = pd.DataFrame(data)
        self.MINIMUM_CHANGE_THRESHOLD = 0.001

    def _update_percentages(self) -> None:
        """
        Updates the Area_percentage column based on current Area_km2 values.
        Calculates each area as a percentage of the total area.
        """
        total = self.df["Area_km2"].sum()
        self.df["Area_percentage"] = (
            0 if total <= 0 else self.df["Area_km2"] / total * 100
        )

    def _update_areas_from_percentages(self) -> None:
        """
        Updates the Area_km2 column based on current Area_percentage values.
        Distributes the total area according to the percentages.
        """
        total = self.df["Area_km2"].sum()
        self.df["Area_km2"] = self.df["Area_percentage"] / 100 * total

    def _update_bison_supported(self) -> None:
        """
        Updates the model-specific Maximum_Bison_Supported columns based on area and density.
        Calculates the maximum number of bison each land cover type can support for both models.
        """

        self.df["Maximum_Bison_Supported"] = (
            self.df["Area_km2"] * self.df["Mean_Bison_Density"]
        )
        self.df["Maximum_Bison_Supported_NM"] = (
            self.df["Area_km2"] * self.df["Mean_Bison_Density_NM"]
        )
        self.df["Maximum_Bison_Supported_BR"] = (
            self.df["Area_km2"] * self.df["Mean_Bison_Density_BR"]
        )

    def update_areas(self, areas: List[float]):
        """
        Updates area values and recalculates dependent values.

        Args:
            areas: List of area values in km²
        """
        self.df["Area_km2"] = areas
        self._update_percentages()
        self._update_bison_supported()

    def update_percentages(self, fixed_indices: List[int], values: List[float] = None):
        """
        Updates percentages while maintaining fixed values at specified indices.

        Args:
            fixed_indices: Indices of rows that should keep their exact percentage values
            values: Optional list of all percentage values to set

        Notes:
            - If values is provided, it updates all percentages first
            - If fixed_indices is empty, it simply converts percentages to areas
            - Otherwise, it adjusts non-fixed percentages to ensure sum equals 100%
        """
        if values is not None:
            self.df["Area_percentage"] = values

        if not fixed_indices:
            self._update_areas_from_percentages()
            self._update_bison_supported()
            return

        self._adjust_percentages_with_fixed_indices(fixed_indices)
        self._update_areas_from_percentages()
        self._update_bison_supported()

    def _adjust_percentages_with_fixed_indices(self, fixed_indices: List[int]):
        """
        Adjusts the percentage values to maintain 100% total while keeping fixed indices unchanged.

        Args:
            fixed_indices: Indices of rows that should keep their exact percentage values
        """
        percentages = self.df["Area_percentage"].copy()
        fixed_values = {idx: percentages[idx] for idx in fixed_indices}
        fixed_sum = sum(fixed_values.values())
        remaining = max(0, 100 - fixed_sum)  # Cannot be negative
        adjustable_indices = [i for i in range(len(self.df)) if i not in fixed_indices]

        if adjustable_indices:
            current_adjustable_sum = percentages[adjustable_indices].sum()

            if current_adjustable_sum > 0:
                # Scale non-fixed indices proportionally
                ratio = remaining / current_adjustable_sum
                for idx in adjustable_indices:
                    percentages[idx] *= ratio
            elif remaining > 0:
                # Distribute evenly if all adjustable values are zero
                even_share = remaining / len(adjustable_indices)
                for idx in adjustable_indices:
                    percentages[idx] = even_share

        for idx, value in fixed_values.items():
            percentages[idx] = value

        self.df["Area_percentage"] = percentages

    def update_densities(self, densities: List[float]):
        """
        Updates bison density values and recalculates supported bison population.

        Args:
            densities: List of density values (bison per km²)
        """

        self.df["Mean_Bison_Density"] = densities
        self._update_bison_supported()

    @property
    def total_area(self) -> float:
        """Total area in km² across all land cover types."""
        return self.df["Area_km2"].sum()

    @property
    def total_bison(self) -> float:
        """Total maximum bison population supported across all land cover types."""
        return self.df["Maximum_Bison_Supported"].sum()

    def get_indices_for_major_class(self, major_class: str) -> List[int]:
        """
        Returns dataframe indices for all rows belonging to a specific major class.

        Args:
            major_class: Major land cover class identifier

        Returns:
            List of dataframe row indices
        """
        return [
            i
            for i, row in self.df.iterrows()
            if row["Land_Cover_Major_Class"] == major_class
        ]

    def update_from_scenario(self, data: List[Dict], model_type) -> None:
        """
        Updates the dataframe to the state defined by a provided scenario.

        Args:
            data: List of row dictionaries from a saved scenario
        """
        self.df = pd.DataFrame(data)
        if model_type == "Nutritional Maximum":
            self.df["Mean_Bison_Density"] = self.df["Mean_Bison_Density_NM"]
        else:
            self.df["Mean_Bison_Density"] = self.df["Mean_Bison_Density_BR"]
        self._update_bison_supported()

    def update_from_table(
        self, current_data: List[Dict], previous_data: List[Dict]
    ) -> None:
        """
        Updates the dataframe based on changes made directly in the data table.

        Detects which values changed between previous and current state,
        and applies appropriate updates to maintain consistency between
        area, percentage, and bison supported values.

        Args:
            current_data: Current table data as list of dictionaries
            previous_data: Previous table data as list of dictionaries
        """
        if not previous_data or not current_data:
            return

        current_df = pd.DataFrame(current_data)

        null_area_indices = current_df["Area_km2"].isnull() | (
            current_df["Area_km2"] == ""
        )
        null_pct_indices = current_df["Area_percentage"].isnull() | (
            current_df["Area_percentage"] == ""
        )

        current_df["Area_km2"] = current_df["Area_km2"].fillna(0).replace("", 0)
        current_df["Area_percentage"] = (
            current_df["Area_percentage"].fillna(0).replace("", 0)
        )

        previous_df = pd.DataFrame(previous_data)

        changed_indices = self._identify_changed_indices(
            current_df, previous_df, null_area_indices, null_pct_indices
        )

        if not changed_indices["indices"]:
            return

        if changed_indices["area_changed"]:
            self.update_areas(current_df["Area_km2"].tolist())
        elif changed_indices["percentage_changed"]:
            self.update_percentages(
                changed_indices["indices"], current_df["Area_percentage"].tolist()
            )

    def _identify_changed_indices(
        self,
        current_df: pd.DataFrame,
        previous_df: pd.DataFrame,
        null_area_indices: pd.Series,
        null_pct_indices: pd.Series,
    ) -> Dict:
        """
        Identify which indices changed and what type of change occurred.

        Args:
            current_df: DataFrame representing current table state
            previous_df: DataFrame representing previous table state
            null_area_indices: Boolean mask of rows with null area values
            null_pct_indices: Boolean mask of rows with null percentage values

        Returns:
            Dictionary with:
                - area_changed: Boolean indicating if area values changed
                - percentage_changed: Boolean indicating if percentage values changed
                - indices: List of row indices that changed

        Notes:
            Change detection prioritizes:
            1. Null values (from cell deletion)
            2. Changed area values
            3. Changed percentage values
        """
        area_changed = False
        percentage_changed = False
        changed_indices = []

        # Check for null values first (deleted cells)
        if null_area_indices.any():
            area_changed = True
            changed_indices = null_area_indices[null_area_indices].index.tolist()
        elif null_pct_indices.any():
            percentage_changed = True
            changed_indices = null_pct_indices[null_pct_indices].index.tolist()
        else:
            # Check for value changes
            area_diff = current_df["Area_km2"] != previous_df["Area_km2"]
            if area_diff.any():
                area_changed = True
                changed_indices = area_diff[area_diff].index.tolist()
            else:
                pct_diff = (
                    current_df["Area_percentage"] != previous_df["Area_percentage"]
                )
                if pct_diff.any():
                    percentage_changed = True
                    changed_indices = pct_diff[pct_diff].index.tolist()

        return {
            "area_changed": area_changed,
            "percentage_changed": percentage_changed,
            "indices": changed_indices,
        }

    def calculate_changes_from_scenario(
        self,
        stored_scenarios: Optional[List[Dict]] = None,
        model_type="Nutritional Maximum",
    ) -> None:
        """
        Calculates percentage changes from first and previous scenarios.
        Compares the Maximum_Bison_Supported values to calculate changes.

        Args:
            stored_scenarios: List of saved scenarios to compare against
        """
        if model_type == "Nutritional Maximum":
            column_suffix = "NM"
        else:
            column_suffix = "BR"

        if not stored_scenarios or len(stored_scenarios) < 1:
            return

        current_values = self.df[f"Maximum_Bison_Supported_{column_suffix}"]

        prev_scenario_df = pd.DataFrame(stored_scenarios[-1]["data"])
        first_scenario_df = pd.DataFrame(stored_scenarios[0]["data"])

        old_prev_values = prev_scenario_df[f"Maximum_Bison_Supported_{column_suffix}"]
        old_first_values = first_scenario_df[f"Maximum_Bison_Supported_{column_suffix}"]

        with np.errstate(divide="ignore", invalid="ignore"):
            changes = np.where(
                old_prev_values != 0,
                (current_values - old_prev_values) / old_prev_values,
                0,
            )
            changes = np.where(
                np.abs(changes) < self.MINIMUM_CHANGE_THRESHOLD, 0.0, changes
            )
        self.df["Change_From_Previous"] = changes

        with np.errstate(divide="ignore", invalid="ignore"):
            changes = np.where(
                old_first_values != 0,
                (current_values - old_first_values) / old_first_values,
                0,
            )
            changes = np.where(
                np.abs(changes) < self.MINIMUM_CHANGE_THRESHOLD, 0.0, changes
            )
        self.df["Change_From_First"] = changes
