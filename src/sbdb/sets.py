"""
Core set-based data structures for generalised structural design.

This module contains the fundamental dataclasses for managing design parameter sets,
object sets, and verification data sets in set-based structural design workflows.
"""

from __future__ import annotations

import importlib
import inspect
import itertools
import json
import os
from dataclasses import dataclass, field
from typing import Callable, Tuple

import numpy as np
import pandas as pd


def _get_init_params(cls: type) -> set[str] | None:
    """
    Get valid ``__init__`` parameter names for a class.

    Returns:
        Set of parameter names accepted by the class constructor,
        or None if the constructor accepts **kwargs (meaning all
        keyword arguments are valid).
    """
    sig = inspect.signature(cls.__init__)
    has_var_keyword = any(
        p.kind == inspect.Parameter.VAR_KEYWORD
        for p in sig.parameters.values()
    )
    if has_var_keyword:
        return None  # accepts anything
    return {
        name
        for name, param in sig.parameters.items()
        if name != "self"
        and param.kind
        in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    }


def _import_class(dotted_path: str) -> type:
    """
    Import a class from a dotted module path.

    Args:
        dotted_path: Fully qualified class path (e.g., 'steelas.component.bolt.Bolt')

    Returns:
        The imported class object

    Raises:
        ImportError: If the module cannot be imported
        AttributeError: If the class is not found in the module
    """
    module_path, class_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


@dataclass(kw_only=True)
class DesignParameterSet:
    """
    Manages design parameter sets for combinatorial design space generation.

    Creates all possible combinations of design parameters using Cartesian product,
    enabling systematic exploration of design spaces.
    """

    design_param_sets: dict[str, object]
    param_list: list[dict] = field(init=False)

    def __post_init__(self):
        self.solve_me()

    def solve_me(self):
        """Generate parameter list from design parameter sets."""
        self.param_list = self.read_design_variable_set()

    def read_design_variable_set(self) -> list[dict]:
        """
        Returns a design parameter set (list of dict, with dict containing class
        instancing attributes).

        Uses Cartesian product to generate all possible combinations of design
        parameters.
        """
        design_var_dicts = []
        data = self.design_param_sets
        keys = list(data.keys())
        design_var_cross_product = itertools.product(*data.values())
        for d in design_var_cross_product:
            design_var_dicts.append(dict(zip(keys, list(d))))
        return design_var_dicts

    def replace_variable(self, var_name: str, op: Callable):
        """
        Apply an operation to a named design parameter and rebuild the parameter list.

        Args:
            var_name: Name of the design parameter to modify
            op: Function to apply to each value in the parameter set
        """
        self.design_param_sets[var_name] = [
            op(v) for v in self.design_param_sets[var_name]
        ]
        self.solve_me()

    def create_value_function(self) -> dict[str, float]:
        """
        Create value function for design parameters (descending order preference).

        Returns:
            Dictionary mapping variable names to value functions
        """
        val_fn = {}
        for key, val in self.design_param_sets.items():
            N = len(val)
            # Descending order - first items have higher value
            v_i = [(N - v) / N for v in list(range(N))]
            val_fn_dict = dict(zip(val, v_i))
            val_fn[key] = val_fn_dict
        return val_fn

    def as_df(self) -> pd.DataFrame:
        """
        Convert the design parameter set to a pandas DataFrame.
        """
        return pd.DataFrame(self.param_list)

    @classmethod
    def from_json(cls, filename):
        """
        Create DesignParameterSet from JSON file.

        Supports both the simple format (flat dict of variable lists) and the
        extended format (dict with a "design_parameter_set" key).

        Args:
            filename: Path to JSON file containing design parameter sets
        """
        with open(filename) as json_file:
            data = json.load(json_file)
            # Support extended JSON schema: extract design_parameter_set if present
            if "design_parameter_set" in data:
                return cls(design_param_sets=data["design_parameter_set"])
            return cls(design_param_sets=data)

    @classmethod
    def merge_parameter_lists(cls, merge_list: list[DesignParameterSet]) -> list[dict]:
        """
        Returns a merged parameter list, combined from multiple DesignParameterSets.

        Args:
            merge_list: List of DesignParameterSet instances to merge
        """
        param_list = []
        for m in merge_list:
            for p in m.param_list:
                param_list.append(p)
        return param_list


@dataclass(kw_only=True)
class ObjectSet:
    """
    Generates object sets from design parameters using a reference class.

    Creates instances of a reference class for each parameter combination,
    handling errors gracefully and providing progress feedback.
    """

    reference_class: Callable
    param_list: list[dict]
    report_attrs: list[str] | None = None

    object_set: list = field(init=False)
    object_library: pd.DataFrame = field(init=False)
    value_fn: list | None = None

    def __post_init__(self):
        if self.report_attrs is None:
            self.report_attrs = list(self.reference_class.__annotations__.keys())
        self.object_set, self.object_library = self.generate_object_set()

    def generate_object_set(self) -> Tuple[list, pd.DataFrame]:
        """
        Calculate the object sets and object libraries from the provided reference class
        and design parameter list.

        Returns:
            Tuple of (object_set, object_library_dataframe)
        """
        df_columns = self.report_attrs
        df = pd.DataFrame(data=None, columns=df_columns)
        obj_set = []

        # Determine valid __init__ params for the reference class
        # so we can filter out extra keys that would cause errors.
        valid_params = _get_init_params(self.reference_class)

        # Keep track of which indices are skipped
        self.skipped_indices = []
        count = 0

        for i, p in enumerate(self.param_list):
            try:
                # Filter params to only those accepted by the class
                if valid_params is not None:
                    p_filtered = {
                        k: v for k, v in p.items() if k in valid_params
                    }
                else:
                    p_filtered = p
                p_instance = self.reference_class(**p_filtered)
                obj_set.append(p_instance)
                # Add all class attributes to the dataframe
                attr_value_list = []
                for attr_name in df_columns:
                    if hasattr(p_instance, attr_name):
                        attr_value_list.append(getattr(p_instance, attr_name))
                    else:
                        raise ValueError(
                            f'Error: reportable attribute "{attr_name}" not available'
                        )
                df.loc[len(df)] = attr_value_list

            except Exception as e:
                print(f"Skipping param_list index {i} due to error: {e}")
                self.skipped_indices.append(i)

            count += 1
            interval = 1000
            if count % interval == 0:
                print(f"Object #{count} completed")

        print(f"Total count = {count}")

        if self.value_fn is not None:
            df["value_fn"] = self.value_fn
        return obj_set, df

    def reduce_design_space(self, query_string: str):
        """
        Apply the query string to the object library.
        Rebuild the ObjectSet without items that match the query (return True).

        Args:
            query_string: Pandas query string for filtering
        """
        remove_me = self.object_library.query(query_string).index
        for index in sorted(list(remove_me), reverse=True):
            del self.param_list[index]
            if self.value_fn is not None:
                del self.value_fn[index]
        self.object_set, self.object_library = self.generate_object_set()

    def make_name_dict(self, index_name: str) -> dict:
        """
        Returns the object set as a named dictionary, using the object_library dataframe
        column index_name.

        Args:
            index_name: Column name to use as dictionary keys
        """
        vals = self.object_set
        keys = list(self.object_library[index_name])
        return dict(zip(keys, vals))

    @classmethod
    def _resolve_descriptor(cls, descriptor: dict) -> ObjectSet:
        """Recursively resolve an ObjectSet descriptor dict.

        Handles both ``design_parameter_set`` (Cartesian product) and
        ``design_parameter_dict`` (zip / CSV import) modes, including
        arbitrarily nested descriptors.

        Args:
            descriptor: A dict with ``reference_class`` and either
                ``design_parameter_set`` or ``design_parameter_dict``.

        Returns:
            The resolved ObjectSet.
        """
        reference_class = _import_class(descriptor["reference_class"])
        report_attrs = descriptor.get("report_attrs", None)

        if "design_parameter_dict" in descriptor:
            param_list = cls._resolve_param_dict(
                descriptor["design_parameter_dict"]
            )
        elif "design_parameter_set" in descriptor:
            param_list = cls._resolve_param_set(
                descriptor["design_parameter_set"]
            )
        else:
            raise ValueError(
                "Descriptor needs 'design_parameter_set' or "
                "'design_parameter_dict'"
            )

        return cls(
            reference_class=reference_class,
            param_list=param_list,
            report_attrs=report_attrs,
        )

    @classmethod
    def _resolve_param_dict(cls, dpd) -> list[dict]:
        """Resolve a ``design_parameter_dict`` value.

        Args:
            dpd: Either a CSV file path (str) or an inline dict
                whose values are lists, or nested ObjectSet descriptors.

        Returns:
            A list of param dicts (one per row / zipped entry).
        """
        if isinstance(dpd, str):
            return pd.read_csv(dpd).to_dict(orient="records")

        if isinstance(dpd, dict):
            resolved = {}
            for name, value in dpd.items():
                if (
                    isinstance(value, dict)
                    and "reference_class" in value
                ):
                    nested = cls._resolve_descriptor(value)
                    resolved[name] = nested.object_set
                elif isinstance(value, list):
                    resolved[name] = value
                else:
                    raise ValueError(
                        f"Unsupported value type for "
                        f"'{name}' in design_parameter_dict"
                    )
            keys = list(resolved.keys())
            values = list(resolved.values())
            return [
                dict(zip(keys, row)) for row in zip(*values)
            ]

        raise ValueError(
            "'design_parameter_dict' must be a CSV file "
            "path (string) or an inline dict"
        )

    @classmethod
    def _resolve_param_set(cls, dps: dict) -> list[dict]:
        """Resolve a ``design_parameter_set`` value.

        Handles nested ObjectSet descriptors within the set
        (which become lists of objects for Cartesian product).

        Args:
            dps: Dict of variable names to value lists or nested
                ObjectSet descriptors.

        Returns:
            A list of param dicts (Cartesian product).
        """
        for var_name, var_value in dps.items():
            if (
                isinstance(var_value, dict)
                and "reference_class" in var_value
            ):
                nested = cls._resolve_descriptor(var_value)
                dps[var_name] = nested.object_set
        dvs = DesignParameterSet(design_param_sets=dps)
        return dvs.param_list

    @classmethod
    def from_json(
        cls, filename: str, autoexport: bool = True
    ) -> Tuple[ObjectSet, list[str]]:
        """
        Create an ObjectSet from a JSON descriptor file.

        The JSON file supports two modes:

        **Generation mode** (design_parameter_set):
            - "reference_class" (required): Dotted import path to the class
              (e.g., "steelas.component.bolt.Bolt")
            - "design_parameter_set" (required): Dict of variable names to
              value lists. Generates Cartesian product of all combinations.

        **Import mode** (design_parameter_dict):
            - "design_parameter_dict": Either a CSV file path (string) or
              an inline dict whose values are lists or nested ObjectSet
              descriptors. Entries are zipped 1-to-1.

        Nested descriptors are resolved recursively to arbitrary depth.

        **Common optional fields** (both modes):
            - "report_attrs" (optional): List of attribute/column names to
              include. If omitted, all are used.
            - "output" (optional): Export configuration dict with keys:
                - "folder" (str): Output directory path
                - "filename" (str): Base filename (without extension)
                - "filetypes" (list[str]): List of file types to export
                  (e.g., ["csv", "json"])

        Args:
            filename: Path to JSON descriptor file
            autoexport: If True (default), automatically export files when
                an "output" config is specified in the JSON file. If False,
                skip the export even if "output" is present.

        Returns:
            Tuple of (ObjectSet instance, list of exported file paths).
            The list is empty if autoexport is False or no output is configured.

        Example JSON file::

            {
                "reference_class": "steelas.component.bolt.Bolt",
                "design_parameter_set": {
                    "d_f": [12, 16, 20, 24, 30, 36],
                    "bolt_cat": ["4.6/S", "8.8/S", "8.8/TF", "8.8/TB"],
                    "threads_included": [true, false]
                },
                "report_attrs": ["name", "d_f", "phiV_f", "phiN_tf"],
                "output": {
                    "folder": "examples",
                    "filename": "bolt_library",
                    "filetypes": ["csv", "json"]
                }
            }
        """
        with open(filename) as json_file:
            data = json.load(json_file)

        # Validate required fields
        if (
            "reference_class" not in data
            and "design_parameter_dict" not in data
        ):
            raise ValueError(
                f"JSON file '{filename}' missing 'reference_class' "
                "or 'design_parameter_dict'"
            )

        # Extract optional fields
        report_attrs = data.get("report_attrs", None)
        output_config = data.get("output", None)

        # Handle design_parameter_dict mode
        if "design_parameter_dict" in data:
            param_list = cls._resolve_param_dict(
                data["design_parameter_dict"]
            )

            # If reference_class is provided, instantiate objects
            if "reference_class" in data:
                reference_class = _import_class(
                    data["reference_class"]
                )
                obj_set = cls(
                    reference_class=reference_class,
                    param_list=param_list,
                    report_attrs=report_attrs,
                )
            else:
                # No class — use as library directly
                import_df = pd.DataFrame(param_list)
                if report_attrs is not None:
                    import_df = import_df[report_attrs]
                obj_set = object.__new__(cls)
                obj_set.reference_class = None
                obj_set.param_list = param_list
                obj_set.report_attrs = (
                    report_attrs
                    if report_attrs
                    else list(import_df.columns)
                )
                obj_set.object_set = []
                obj_set.object_library = import_df
                obj_set.value_fn = None
                obj_set.skipped_indices = []

        else:
            # Standard generation mode
            if "design_parameter_set" not in data:
                raise ValueError(
                    f"JSON file '{filename}' missing required "
                    "field 'design_parameter_set'"
                )

            reference_class = _import_class(
                data["reference_class"]
            )
            param_list = cls._resolve_param_set(
                data["design_parameter_set"]
            )
            obj_set = cls(
                reference_class=reference_class,
                param_list=param_list,
                report_attrs=report_attrs,
            )

        # Export files if output config specified and autoexport is enabled
        exported_files = []
        if autoexport and output_config is not None:
            folder = output_config.get("folder", ".")
            base_filename = output_config.get("filename", "output")
            filetypes = output_config.get("filetypes", ["csv"])

            # Create output folder if it doesn't exist
            os.makedirs(folder, exist_ok=True)

            for filetype in filetypes:
                filepath = f"{folder}/{base_filename}.{filetype}"
                if filetype == "csv":
                    obj_set.object_library.to_csv(filepath, index=False)
                elif filetype == "json":
                    obj_set.object_library.to_json(
                        filepath, orient="records", indent=2
                    )
                else:
                    raise ValueError(f"Unsupported file type: '{filetype}'")
                exported_files.append(filepath)

        return obj_set, exported_files


@dataclass(kw_only=True)
class VerifiedObjectLibrary:
    """
    Compares generated object library against verification data.

    Performs error analysis and generates verification reports for
    validating generated data against external sources.
    """

    object_library: pd.DataFrame
    verification_library: pd.DataFrame
    lookup_index: str

    result_df: pd.DataFrame = field(init=False)
    report_df: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.result_df = self.check_error()
        self.report_df = self.error_report()

    def check_error(self):
        """
        Compare object library against verification library and calculate errors.

        Returns:
            DataFrame with error calculations for each parameter
        """
        lib_df = self.object_library
        verify_df = self.verification_library
        lib_df = lib_df.set_index(self.lookup_index)
        verify_df = verify_df.set_index(self.lookup_index)

        error_df = pd.DataFrame(index=lib_df.index, columns=lib_df.columns)

        for i, c in error_df.iterrows():
            if i in verify_df.index:
                for param in error_df.columns:
                    if param in verify_df.columns:
                        verify_value = verify_df.loc[i, param]
                        generated_value = lib_df.loc[i, param]
                        if verify_value == np.nan or generated_value == np.nan:
                            c[param] = np.nan
                        else:
                            c[param] = self.error_calc(
                                generated_value, verify_value, c, param
                            )
                    else:
                        c[param] = np.nan
            else:
                for param in error_df.columns:
                    c[param] = np.nan

        return error_df.reset_index()

    def error_report(self):
        """
        Generate verification report with coverage and error statistics.

        Returns:
            DataFrame with verification statistics for each parameter
        """
        lib_df = self.object_library
        verify_df = self.verification_library
        result_df = self.result_df

        report_df = pd.DataFrame(index=lib_df.columns)
        report_df.index.names = ["parameters"]

        check_list = []
        coverage_list = []
        max_error_list = []
        avg_error_list = []
        avg_abs_error_list = []
        min_error_list = []
        data_error_list = []

        for param in report_df.index:
            if param in verify_df.columns:
                check_list.append("yes")
                coverage = (
                    len(result_df[param].dropna()) / len(lib_df[param]) * 100
                )  # in percentage%
                coverage_list.append(round(coverage, 2))

                if type(result_df[param][0]) is str:  # string type data
                    max_error = "N/A"
                    avg_error = "N/A"
                    avg_abs_error = "N/A"
                    min_error = "N/A"
                    matched_num = (result_df[param] == "match").sum()
                    not_matched_num = (result_df[param] == "not match").sum()
                    data_error = (
                        1 - matched_num / (matched_num + not_matched_num)
                    ) * 100  # in percentage%
                else:
                    data_error = "N/A"
                    if len(result_df[param].dropna()) > 0:
                        max_error = max(result_df[param].dropna())
                        avg_error = sum(result_df[param].dropna()) / len(
                            result_df[param].dropna()
                        )
                        avg_abs_error = sum(abs(result_df[param].dropna())) / len(
                            result_df[param].dropna()
                        )
                        min_error = min(result_df[param].dropna())
                    else:
                        max_error = "N/A"
                        avg_error = "N/A"
                        avg_abs_error = "N/A"
                        min_error = "N/A"

                max_error_list.append(max_error)
                avg_error_list.append(avg_error)
                avg_abs_error_list.append(avg_abs_error)
                min_error_list.append(min_error)
                data_error_list.append(data_error)
            else:
                check_list.append("no")
                coverage_list.append(np.nan)
                max_error_list.append(np.nan)
                avg_error_list.append(np.nan)
                avg_abs_error_list.append(np.nan)
                min_error_list.append(np.nan)
                data_error_list.append(np.nan)

        report_df["checked or not?"] = check_list
        report_df["coverage"] = coverage_list
        report_df["max error"] = max_error_list
        report_df["avg error"] = avg_error_list
        report_df["avg abs error"] = avg_abs_error_list
        report_df["min error"] = min_error_list
        report_df["str error"] = data_error_list

        return report_df

    @staticmethod
    def error_calc(generated_value, verify_value, c, param):
        """
        Calculate error between generated and verification values.

        Args:
            generated_value: Value from generated data
            verify_value: Value from verification data
            c: Current row (unused but kept for compatibility)
            param: Parameter name (unused but kept for compatibility)

        Returns:
            Error value or match status
        """
        if type(generated_value) is str:
            return "match" if generated_value == verify_value else "not match"
        elif verify_value == 0:
            return (
                0
                if verify_value == generated_value
                else generated_value / generated_value * 100
            )
        else:
            result = (
                (float(generated_value) - float(verify_value))
                / float(verify_value)
                * 100
            )  # in percentage%
            return round(result, 3)
