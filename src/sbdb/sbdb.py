from __future__ import annotations

from dataclasses import dataclass, field

import itertools
import json
from typing import Callable, Tuple

import pandas as pd
import numpy as np


@dataclass(kw_only=True)
class DesignVariableSet:
    # filename: str
    design_var_sets: dict[str, object]
    param_list: list[dict] = field(init=False)
    # value_function: dict[str, float] = field(init=False)
    # create_value_function: bool = False

    def __post_init__(self):
        self = self.solve_me()

    def solve_me(self):
        self.param_list = self.read_design_variable_set()
        # if self.create_value_function:
        #    self.solve_value_function()

    def read_design_variable_set(self) -> list[dict]:
        """returns a design variable set (list of dict, with dict containing class instancing attributes)"""
        design_var_dicts = []
        # for full object set:
        # with open(self.filename) as json_file:
        data = self.design_var_sets
        keys = list(data.keys())
        design_var_cross_product = itertools.product(*data.values())
        for d in design_var_cross_product:
            design_var_dicts.append(dict(zip(keys, list(d))))
        return design_var_dicts

    def replace_variable(self, var_name: str, op: Callable):
        """apply an operation to a named design variable and rebuild the parameter list"""
        self.design_var_sets[var_name] = [op(v) for v in self.design_var_sets[var_name]]
        self.solve_me()

    def create_value_function(self) -> dict[str, float]:
        val_fn = {}
        for key, val in self.design_var_sets.items():
            N = len(val)
            # v_i = [(v + 1) / N for v in list(range(N))] #ascending order
            v_i = [(N - v) / N for v in list(range(N))]  # descending order
            val_fn_dict = dict(zip(val, v_i))
            val_fn[key] = val_fn_dict  # v_i single dimensional value of components
        return val_fn

    @classmethod
    def from_json(cls, filename):
        with open(filename) as json_file:
            data = json.load(json_file)
            return cls(design_var_sets=data)

    @classmethod
    def merge_parameter_lists(cls, merge_list: list[DesignVariableSet]) -> list[dict]:
        """returns a merged parameter list, combined from multiple DesignVariableSets"""
        param_list = []
        for m in merge_list:
            for p in m.param_list:
                param_list.append(p)

        return param_list


@dataclass(kw_only=True)
class ObjectSet:
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
        """calculate the object sets and object libraries from the provided reference class and design variable list"""

        df_columns = self.report_attrs
        df = pd.DataFrame(data=None, columns=df_columns)
        obj_set = []

        for p in self.param_list:
            p_instance = self.reference_class(**p)
            obj_set.append(p_instance)
            # add all class attributes to the dataframe
            attr_value_list = []
            for attr_name in df_columns:
                if hasattr(p_instance, attr_name):
                    attr_value_list.append(getattr(p_instance, attr_name))
                else:
                    raise ValueError(
                        f'Error: reportable attribute "{attr_name}" is not is available in class definition.'
                    )
            df.loc[len(df)] = attr_value_list

        # if callable(getattr(reference_class, 'row_order', None)):
        #     df = df.sort_values(by=reference_class.row_order(), ignore_index=True)
        if self.value_fn is not None:
            df["value_fn"] = self.value_fn
        return obj_set, df

    def reduce_design_space(self, query_string: str):
        """apply the query string == to the object library.
        Rebuild the ObjectSet without items that any items which return True"""
        remove_me = self.object_library.query(query_string).index
        for index in sorted(list(remove_me), reverse=True):
            del self.param_list[index]
            del self.value_fn[index]
        self.object_set, self.object_library = self.generate_object_set()

    def make_name_dict(self, index_name: str) -> dict:
        """returns the object set as a named dictionary, using the object_library dataframe column index_name"""
        vals = self.object_set
        keys = list(self.object_library[index_name])
        return dict(zip(keys, vals))


@dataclass(kw_only=True)
class VerifiedObjectLibrary:
    object_library: pd.DataFrame
    verification_library: pd.DataFrame
    lookup_index: str

    result_df: pd.DataFrame = field(init=False)
    report_df: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.result_df = self.check_error()
        self.report_df = self.error_report()

    def check_error(self):
        # lib_df.index.rename('name', inplace=True)
        # verify_df.index.rename('name', inplace=True)
        lib_df = self.object_library
        verify_df = self.verification_library
        lib_df = lib_df.set_index(self.lookup_index)
        verify_df = verify_df.set_index(self.lookup_index)
        # lap_header = verify_df.columns.intersection(lib_df.columns)
        error_df = pd.DataFrame(
            index=lib_df.index, columns=lib_df.columns
        )  # lib_df.columns

        # method 1
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
        """generate verification report"""
        lib_df = self.object_library
        verify_df = self.verification_library
        result_df = self.result_df
        # lib_df = lib_df.set_index(lookup_index)
        # verify_df = verify_df.set_index(lookup_index)
        # NOTE exclude index name in verification report, if include remove set_index
        report_df = pd.DataFrame(index=lib_df.columns)
        report_df.index.names = ["parameters"]

        check_list = []
        coverage_list = []
        # avg_error_list = []
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
                # print(param)
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
        # report_df['num error'] = avg_error_list
        report_df["max error"] = max_error_list
        report_df["avg error"] = avg_error_list
        report_df["avg abs error"] = avg_abs_error_list
        report_df["min error"] = min_error_list
        report_df["str error"] = data_error_list

        return report_df

    @staticmethod
    def error_calc(generated_value, verify_value, c, param):
        if type(generated_value) is str:
            return "match" if generated_value == verify_value else "not match"
        elif verify_value == 0:
            return (
                0
                if verify_value == generated_value
                else generated_value / generated_value * 100
            )
        # elif generated_value == 0:
        #     return 0 if verify_value == generated_value else (float(verify_value) - float(generated_value))/float(verify_value) * 100 * (-1)
        # elif type(generated_value) is None or type(verify_value) is None:
        #    a = 3
        else:
            result = (
                (float(generated_value) - float(verify_value))
                / float(verify_value)
                * 100
            )  # in percentage%
            return round(result, 3)

    # def check_error(lib_df, verify_df):
    #     df = lib_df.copy()
    #     # df.columns = df.columns.get_values()

    #     lib_dict = make_dict(df)
    #     verify_dict = make_dict(verify_df)

    #     lap_header = verify_df.columns.intersection(df.columns) #get overlapped attributes of library and verification dataset
    #     error_df = pd.DataFrame(index = df.index,columns = lap_header)

    # def generate_lib_info(df, ref_class, files):
    #     units = ref_class().get_units()
    #     info_df = make_info(df, units)
    #     toolbox_version = 'StructuralDesignToolbox v0.1'
    #     df_extra_info = pd.DataFrame({
    #         "param_name": ["generated_date", "version_info"],
    #         "unit": [datetime.today().strftime('%Y-%m-%d'), toolbox_version],
    #     })
    #     info_df.append(df_extra_info).to_csv(files['output_info'], index=False)
