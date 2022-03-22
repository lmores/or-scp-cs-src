# Result format

The description of the format for result files related to the execution of the linear models SCP-CS_BIN and SCP-CS_MIP, and for the parallel GRASP algorithm can be found in [docs/output.md](../docs/output.md).

The csv result file related to the execution of the SCP-CS_QO model has the following columns.

```txt
    instance            : the path of the data set file relative to the `dataset/` folder
    conflict_threshold  : two subsets are considered to be in conflict if the cardinality
                          of their intersection is greater than this (integer) value
    action              : the value `SCCS_QO``
    status              : either OPTIMAL, TIME_LIMIT or RUNTIME_EXCEPTION
    time_to_best        : the time taken to find the final solution returned
    time                : the time taken to execute the procedure
    obj_bound           : the cost of the best solution found for the relazed problem
    obj_value           : the cost of the best solution found
                          (i.e. the value of the objective function)
```
