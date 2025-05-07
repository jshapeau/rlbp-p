from typing import List, Dict, Any, Tuple, Union
from data.constants import SLIDER_MAX_VALUES
from dataclasses import dataclass
from data.table import BisonDataFrame
import math

PERCENTAGE_MODE_MAX = 100
SCALING_MARGIN = 1.1
MAX_THRESHOLD = 0.8


class SliderValues:
    """
    Manages the values of major and minor sliders and their relationships.
    Maintains a hierarchical structure where major sliders represent category totals
    and minor sliders represent individual subcategories.
    """

    def __init__(self, minor_ids: List[Dict], major_ids: List[Dict]):
        self.minor = self._init_minor_values(minor_ids)
        self.major = self._init_major_values(major_ids)

    def get_minor_values(self) -> List[float]:
        """
        Returns a flat list of all minor slider values in their current state.
        Used for UI updates and calculations.
        """
        return [info["value"] for info in self.minor.values()]

    def get_major_values(self) -> List[float]:
        """
        Returns a flat list of all major slider values in their current state.
        Used for UI updates and calculations.
        """
        return [info["value"] for info in self.major.values()]

    def set_minor_values(self, values: Union[List[float], Dict[str, float]]):
        """
        Sets minor slider values and updates major slider totals accordingly.

        Args:
            values: Either a list of values (position-based) or a dict of {slider_id: value}
                   When a list is provided, values are assigned in order of minor.items()
                   When a dict is provided, values are assigned by matching keys
        """
        if isinstance(values, list):
            for (key, info), value in zip(self.minor.items(), values):
                info["value"] = value
        else:
            for key, value in values.items():
                if key in self.minor:
                    self.minor[key]["value"] = value

        self._update_major_totals()

    def _init_minor_values(self, minor_ids: List[Dict]) -> Dict:
        """
        Initialize the minor values structure from slider IDs.

        Args:
            minor_ids: List of dictionaries containing slider ID and value information

        Returns:
            Dictionary mapping slider IDs to their metadata and values
        """
        return {
            id_dict["id"]["index"]: {
                "value": id_dict["value"],
                "major_class": id_dict["id"]["index"].split("-")[0],
                "df_name": "-".join(id_dict["id"]["index"].split("-")[1:]).replace(
                    "-", " "
                ),
            }
            for id_dict in minor_ids
        }

    def _init_major_values(self, major_ids: List[Dict]) -> Dict:
        """
        Initialize the major values structure from slider IDs.
        Links major sliders to their corresponding minor sliders.

        Args:
            major_ids: List of dictionaries containing slider ID and value information

        Returns:
            Dictionary mapping slider IDs to their metadata and associated minor sliders
        """
        return {
            id_dict["id"]["index"]: {
                "value": id_dict["value"],
                "minor_classes": [
                    key
                    for key in self.minor.keys()
                    if key.startswith(f"{id_dict['id']['index']}-")
                ],
            }
            for id_dict in major_ids
        }

    def _update_major_totals(self):
        """
        Updates all major slider values based on the sum of their corresponding minor sliders.
        Called whenever minor slider values change.
        """
        for major_key, major_info in self.major.items():
            major_info["value"] = sum(
                self.minor[minor_key]["value"]
                for minor_key in major_info["minor_classes"]
            )


@dataclass
class SliderState:
    """
    Manages the state of all sliders in the application.
    Handles the relationship between minor and major sliders and the data model.
    """

    def __init__(
        self,
        bison_data: BisonDataFrame,
        minor_ids: List[Dict],
        major_ids: List[Dict],
        is_percentage_mode: bool,
    ):
        self.bison_data = bison_data
        self.is_percentage_mode = is_percentage_mode
        self.values = SliderValues(minor_ids, major_ids)
        self.major_max = SLIDER_MAX_VALUES["major_sliders"]
        self.minor_max = SLIDER_MAX_VALUES["minor_sliders"]

    def sync(self, preserve_values=None):
        """
        Synchronizes slider values with the current state of the BisonData dataframe.

        Args:
            preserve_values: Optional dictionary of {slider_id: value} containing values
                            that should remain unchanged during synchronization
        """
        preserve_values = preserve_values or {}
        col = "Area_percentage" if self.is_percentage_mode else "Area_km2"
        df_values = self.bison_data.df[col].tolist()

        for i, (key, info) in enumerate(self.values.minor.items()):
            if i < len(df_values) and key not in preserve_values:
                info["value"] = df_values[i]
            elif key in preserve_values:
                info["value"] = preserve_values[key]

        self.values._update_major_totals()

        for key, value in preserve_values.items():
            if key in self.values.major:
                self.values.major[key]["value"] = value

    def _distribute_values(
        self, total_value: float, minor_classes: List[str]
    ) -> Dict[str, float]:
        """
        Proportionally distributes a total value across multiple minor classes.

        Args:
            total_value: The total value to distribute (e.g., total area for a major class)
            minor_classes: List of minor class IDs to distribute the value among

        Returns:
            Dictionary mapping minor_class_id to its new value

        Notes:
            - If current values sum to > 0, distribution is proportional to current values
            - If current values sum to 0 but total_value > 0, distribution is equal
            - If total_value is 0, all values are set to 0
        """
        result = {}
        current_sum = sum(self.values.minor[cls]["value"] for cls in minor_classes)

        if current_sum > 0:
            ratio = total_value / current_sum
            for cls in minor_classes:
                result[cls] = self.values.minor[cls]["value"] * ratio
        elif total_value > 0:
            equal_share = total_value / len(minor_classes)
            for cls in minor_classes:
                result[cls] = equal_share
        else:
            for cls in minor_classes:
                result[cls] = 0

        return result

    def update_maximum_values(self) -> bool:
        """
        Updates the maximum values for sliders based on current data.

        In percentage mode, maximums are fixed at 100.
        In absolute mode, maximums are dynamically adjusted to accommodate large values.

        Returns:
            bool: True if maximum values were changed, False otherwise
        """
        if self.is_percentage_mode:
            self.major_max = PERCENTAGE_MODE_MAX
            self.minor_max = PERCENTAGE_MODE_MAX
            return False

        current_max_minor = max(info["value"] for info in self.values.minor.values())
        current_max_major = max(info["value"] for info in self.values.major.values())

        needed_minor_max = math.ceil(current_max_minor * SCALING_MARGIN / 100) * 100
        needed_major_max = math.ceil(current_max_major * SCALING_MARGIN / 100) * 100

        changed = False
        if needed_minor_max > self.minor_max:
            self.minor_max = needed_minor_max
            changed = True

        if needed_major_max > self.major_max:
            self.major_max = needed_major_max
            changed = True

        return changed

    def update_from_minor_change(self, minor_classes: List[str]) -> None:
        """
        Updates state when minor slider(s) change.

        Handles the propagation of changes from minor sliders to major sliders
        and updates the data model accordingly, accounting for percentage/absolute modes.

        Args:
            minor_classes: List of minor class identifiers that changed
        """
        original_values = {}
        modified_major_classes = set()

        for minor_class in minor_classes:
            original_values[minor_class] = self.values.minor[minor_class]["value"]

            if (
                not self.is_percentage_mode
                and original_values[minor_class] > self.minor_max * MAX_THRESHOLD
            ):
                self.update_maximum_values()

            major_class = self.values.minor[minor_class]["major_class"]
            modified_major_classes.add(major_class)

        preserve_map = {**original_values}

        if self.is_percentage_mode:
            self._update_percentage_mode(minor_classes, preserve_map)
        else:
            self._update_absolute_mode(
                minor_classes, modified_major_classes, preserve_map
            )

    def _update_percentage_mode(
        self, minor_classes: List[str], preserve_map: Dict[str, float]
    ):
        """
        Handles updates in percentage mode when minor sliders change.

        Args:
            minor_classes: List of minor class identifiers that changed
            preserve_map: Dictionary of values to preserve during synchronization
        """
        indices, _ = self._get_values_from_keys(minor_classes, "Area_percentage")
        all_values = self.values.get_minor_values()
        self.bison_data.update_percentages(indices, all_values)
        self.sync(preserve_values=preserve_map)

    def _update_absolute_mode(
        self,
        minor_classes: List[str],
        modified_major_classes: set,
        preserve_map: Dict[str, float],
    ):
        """
        Handles updates in absolute mode when minor sliders change.

        Args:
            minor_classes: List of minor class identifiers that changed
            modified_major_classes: Set of major classes affected by the changes
            preserve_map: Dictionary of values to preserve during synchronization
        """
        self._update_absolute_values(minor_classes, preserve_map)

        for major_class in modified_major_classes:
            self.values.major[major_class]["value"] = sum(
                self.values.minor[cls]["value"]
                for cls in self.values.major[major_class]["minor_classes"]
            )
            preserve_map[major_class] = self.values.major[major_class]["value"]

        self._sync_specific(minor_classes, list(modified_major_classes), preserve_map)

    def _update_absolute_values(
        self, minor_classes: List[str], values_dict: Dict[str, float]
    ):
        """
        Updates the absolute area values in the dataframe for specific minor classes.
        Also updates the derived bison supported values.

        Args:
            minor_classes: List of minor class identifiers to update
            values_dict: Dictionary mapping minor class IDs to their new values
        """
        for minor_class in minor_classes:
            info = self.values.minor[minor_class]

            mask = (
                self.bison_data.df["Land_Cover_Major_Class"] == info["major_class"]
            ) & (self.bison_data.df["Land_Cover_Minor_Class"] == info["df_name"])

            if any(mask):
                index = self.bison_data.df[mask].index[0]
                value = values_dict[minor_class]

                self.bison_data.df.at[index, "Area_km2"] = value
                self.bison_data._update_bison_supported()

    def update_from_major_change(self, major_class: str) -> None:
        """
        Updates state when a major slider changes.

        Distributes the change proportionally to child minor sliders and updates
        the data model accordingly, accounting for percentage/absolute modes.

        Args:
            major_class: The major class identifier that changed
        """
        new_major_value = self.values.major[major_class]["value"]
        minor_classes = self.values.major[major_class]["minor_classes"]

        # Check if maximum slider values need to be updated
        if (
            not self.is_percentage_mode
            and new_major_value > self.major_max * MAX_THRESHOLD
        ):
            self.update_maximum_values()

        new_minor_values = self._distribute_values(new_major_value, minor_classes)

        for minor_class, new_value in new_minor_values.items():
            self.values.minor[minor_class]["value"] = new_value

        # Prepare preservation map for sync operations
        preserve_map = {major_class: new_major_value}
        preserve_map.update(new_minor_values)

        if self.is_percentage_mode:
            self._update_percentage_mode(minor_classes, preserve_map)
        else:
            self._update_absolute_values(minor_classes, new_minor_values)
            self._sync_specific(minor_classes, [major_class], preserve_map)

    def _sync_specific(
        self,
        minor_classes: List[str],
        major_classes: List[str],
        preserve_values: Dict[str, float],
    ):
        """
        Updates only the specified sliders from the dataframe.
        More efficient than a full sync when only a subset of sliders need updating.

        Args:
            minor_classes: List of minor class identifiers to update
            major_classes: List of major class identifiers to update
            preserve_values: Dictionary of values to preserve during synchronization
        """
        col = "Area_percentage" if self.is_percentage_mode else "Area_km2"

        for minor_class in minor_classes:
            if minor_class not in preserve_values:
                info = self.values.minor[minor_class]
                mask = (
                    self.bison_data.df["Land_Cover_Major_Class"] == info["major_class"]
                ) & (self.bison_data.df["Land_Cover_Minor_Class"] == info["df_name"])

                if any(mask):
                    idx = self.bison_data.df[mask].index[0]
                    self.values.minor[minor_class]["value"] = self.bison_data.df.at[
                        idx, col
                    ]

        for major_class in major_classes:
            if major_class not in preserve_values:
                minor_classes = self.values.major[major_class]["minor_classes"]
                total = sum(self.values.minor[cls]["value"] for cls in minor_classes)
                self.values.major[major_class]["value"] = total
            else:
                self.values.major[major_class]["value"] = preserve_values[major_class]

    def _get_values_from_keys(
        self, slider_keys: List[str], col: str
    ) -> Tuple[List[int], List[float]]:
        """
        Retrieves dataframe indices and values for a set of minor slider keys.

        Args:
            slider_keys: List of minor slider identifiers
            col: Column name to retrieve values from

        Returns:
            Tuple containing:
                - List of dataframe indices corresponding to the slider keys
                - List of values from the specified column at those indices
        """
        indices = []
        values = []

        for key in slider_keys:
            info = self.values.minor[key]

            mask = (
                self.bison_data.df["Land_Cover_Major_Class"] == info["major_class"]
            ) & (self.bison_data.df["Land_Cover_Minor_Class"] == info["df_name"])

            matching_rows = self.bison_data.df[mask]
            if not matching_rows.empty:
                indices.append(matching_rows.index[0])
                values.append(matching_rows[col].iloc[0])

        return indices, values

    def format_output(self) -> Tuple[List[float], List[float], Dict[str, Any]]:
        """
        Formats the slider values for callback output.
        Checks if maximums need to be updated and includes that information.

        Returns:
            Tuple containing:
                - List of minor slider values
                - List of major slider values
                - Dictionary with error data and slider mark update information
        """
        maximums_updated = self.update_maximum_values()

        error_data = {
            "minor": [],
            "major": [],
            "update_marks": maximums_updated and not self.is_percentage_mode,
        }

        # Include new maximum values if they were updated
        if error_data["update_marks"]:
            error_data["major_max"] = self.major_max
            error_data["minor_max"] = self.minor_max

        return (
            self.values.get_minor_values(),
            self.values.get_major_values(),
            error_data,
        )
