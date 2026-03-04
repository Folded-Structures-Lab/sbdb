"""
Core set-based data structures for generalised structural design.

This module contains the fundamental dataclasses for managing design variable sets,
object sets, and verification data sets in set-based structural design workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import itertools
import json
from typing import Callable, Tuple

import pandas as pd
import numpy as np


@dataclass(kw_only=True)
class DesignVariableSet:
    """
    Manages design variable sets for combinatorial design space generation.
    
    Creates all possible combinations of design variables using Cartesian product,
    enabling systematic exploration of design spaces.
    """
    design_var_sets: dict[str, object]
    param_list: list[dict] = field(init=False)

    def __post_init__(self):
        self.solve_me()

    def solve_me(self):
        """Generate parameter list from design variable sets."""
        self.param_list = self.read_design_variable_set()

    def read_design_variable_set(self) -> list[dict]:
        """
        Returns a design variable set (list of dict, with dict containing class instancing attributes).
        
        Uses Cartesian product to generate all possible combinations of design variables.
        """
        design_var_dicts = []
        data = self.design_var_sets
        keys = list(data.keys())
        design_var_cross_product = itertools.product(*data.values())
        for d in design_var_cross_product:
            design_var_dicts.append(dict(zip(keys, list(d))))
        return design_var_dicts

    def replace_variable(self, var_name: str, op: Callable):
        """
        Apply an operation to a named design variable and rebuild the parameter list.
        
        Args:
            var_name: Name of the design variable to modify
            op: Function to apply to each value in the variable set
        """
        self.design_var_sets[var_name] = [op(v) for v in self.design_var_sets[var_name]]
        self.solve_me()

    def create_value_function(self) -> dict[str, float]:
        """
        Create value function for design variables (descending order preference).
        
        Returns:
            Dictionary mapping variable names to value functions
        """
        val_fn = {}
        for key, val in self.design_var_sets.items():
            N = len(val)
            # Descending order - first items have higher value
            v_i = [(N - v) / N for v in list(range(N))]
            val_fn_dict = dict(zip(val, v_i))
            val_fn[key] = val_fn_dict
        return val_fn

    @classmethod
    def from_json(cls, filename):
        """
        Create DesignVariableSet from JSON file.
        
        Args:
            filename: Path to JSON file containing design variable sets
        """
        with open(filename) as json_file:
            data = json.load(json_file)
            return cls(design_var_sets=data)

    @classmethod
    def merge_parameter_lists(cls, merge_list: list[DesignVariableSet]) -> list[dict]:
        """
        Returns a merged parameter list, combined from multiple DesignVariableSets.
        
        Args:
            merge_list: List of DesignVariableSet instances to merge
        """
        param_list = []
        for m in merge_list:
            for p in m.param_list:
                param_list.append(p)
        return param_list


@dataclass(kw_only=True)
class ObjectSet:
    """
    Generates object sets from design variables using a reference class.
    
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
        Calculate the object sets and object libraries from the provided reference class and design variable list.
        
        Returns:
            Tuple of (object_set, object_library_dataframe)
        """
        df_columns = self.report_attrs
        df = pd.DataFrame(data=None, columns=df_columns)
        obj_set = []

        # Keep track of which indices are skipped
        self.skipped_indices = []
        count = 0

        for i, p in enumerate(self.param_list):
            try:
                p_instance = self.reference_class(**p)
                obj_set.append(p_instance)
                # Add all class attributes to the dataframe
                attr_value_list = []
                for attr_name in df_columns:
                    if hasattr(p_instance, attr_name):
                        attr_value_list.append(getattr(p_instance, attr_name))
                    else:
                        raise ValueError(
                            f'Error: reportable attribute "{attr_name}" is not available in class definition.'
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
        Returns the object set as a named dictionary, using the object_library dataframe column index_name.
        
        Args:
            index_name: Column name to use as dictionary keys
        """
        vals = self.object_set
        keys = list(self.object_library[index_name])
        return dict(zip(keys, vals))


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
