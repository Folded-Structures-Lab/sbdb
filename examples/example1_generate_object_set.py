# NOTE - requires steelas python package to be installed
from steelas.component.bolt import Bolt

from sbdb import ObjectSet, DesignVariableSet

# component set information
component_name = "AUS_bolt"
component_class = Bolt
report_attributes = [
    "name",
    "bolt_des",
    "bolt_cat",
    "threads_included",
    "d_f",
    "d_h",
    "a_e_min",
    "s_p_min",
    "phiV_f",
    "phiN_tf",
]

# get design variable set (input parameters)
input_file = component_name + ".json"

# generate data collection
des_vars = DesignVariableSet.from_json(input_file)
object_set = ObjectSet(
    reference_class=component_class,
    param_list=des_vars.param_list,
    report_attrs=report_attributes,
)

# print and export object library
df = object_set.object_library
print(df)
df.to_csv("AUS_bolt_library.csv")
