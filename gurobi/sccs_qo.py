import csv
import logging
import os
import sys
from datetime import datetime
from itertools import product
from pathlib import Path
from time import time

import gurobipy as gp
from gurobipy import GRB
from psutil import Process

from utils.analysis import analyse_solution
from utils.cmd_args import Action
from utils.config import DATASETS_DIR_PATH, LOG_FILE_NAME_TEMPLATE, LOGS_DIR_PATH
from utils.datamodels import GurobiResult, InstanceData, ResultStatus
from utils.instance import read_instance
from utils.misc import current_human_datetime, to_human_datetime
from utils.vprint import v0_print

from .utils import ONE_INDEX_SUBSET_VAR_REGEXP, TWO_INDEX_CONFLICT_VAR_REGEXP, write_log


LOGGER = logging.getLogger(__name__)

CSV_HEADER = (
    'instance', 'conflict_threshold', 'action',
    'status', 'time_to_best', 'time', 'obj_bound', 'obj_value',
)


def build_sccs_qo_model(data: InstanceData):
    model = gp.Model(f'{data.id}_scpcs_qo')

    SC = gp.tupledict(enumerate(data.subset_costs))
    X = model.addVars(SC.keys(), vtype=GRB.BINARY, name="X")

    obj_func = gp.QuadExpr()
    for i, sc in enumerate(data.subset_costs):
        obj_func.add(X[i], sc)
    for (i, j), cc in data.conflict_costs.items():
        if i < j:
            obj_func.add(X[i] * X[j], cc)
    model.setObjective(obj_func, GRB.MINIMIZE)

    LinExpr = gp.LinExpr
    model.addConstrs(
        (LinExpr((1, X[j]) for j, s in enumerate(data.subsets) if i in s) >= 1
        for i in range(data.n_elements)), name="cov"
    )

    model.update()

    return model


def run_sccs_qo(data: InstanceData, time_limit=None, relaxed=False,
        mip_focus=0, initial_solution=None, save_model=False) -> GurobiResult:

    if mip_focus:
        raise ValueError("Unsupported argument: 'mip_focus'")
    if relaxed:
        raise ValueError("Unsupported argument: 'relaxed'")
    if initial_solution:
        raise ValueError("Unsupported argument: 'initial_solution'")

    start_at = time()

    v0_print(
        f"\n{'-' * 80}\n"  "[{}] Solving '{}' SCP-CS QUADRATIC OBJ PROBLEM\n"
        "(n_elements={}, n_subsets={}, conflict_threshold={}, "
        "time_limit={}, save_model={})\n"  f"{'-' * 80}",
        current_human_datetime(), data.id, data.n_elements, data.n_subsets,
        data.conflict_threshold, time_limit, save_model
    )

    start_at = time()
    log_file_path = Path(LOGS_DIR_PATH, LOG_FILE_NAME_TEMPLATE.format(
        base=os.path.splitext(data.id)[0],
        type='qo',
        datetime=to_human_datetime(start_at)
    ))
    os.makedirs(log_file_path.parent, exist_ok=True)

    result = GurobiResult(instance_id=data.id, action=Action.SCCS_QO,
        cmd_args=sys.argv, cpu_count=os.cpu_count(), time_limit=time_limit,
        relaxed=relaxed, log_file_path=log_file_path)
    result.add_instance_data(data)

    # Init model
    init_time_start = time()
    model = build_sccs_qo_model(data)
    model.params.mipfocus = mip_focus
    model.params.jsonSolDetail = 1
    model.params.logFile = str(log_file_path.with_suffix('.gurobi.log'))
    if time_limit is not None:
        model.params.timeLimit = time_limit
    result.init_time = time() - init_time_start

    # Save model
    if save_model:
        model.write(str(log_file_path.with_suffix('.lp')))

    result.time_to_best = -1
    model._obj_best = GRB.INFINITY
    def _cb(model, where):
        if where == GRB.Callback.MIPSOL:
            sol_obj = model.cbGet(GRB.Callback.MIPSOL_OBJ)
            if sol_obj < model._obj_best:
                model._obj_best = sol_obj
                result.time_to_best = model.cbGet(GRB.Callback.RUNTIME)

    try:
        process = Process()
        start_cpu_times = process.cpu_times()
        model.optimize(_cb)
        end_cpu_times = process.cpu_times()
        end_at = time()
    except gp.GurobiError as e:
        LOGGER.error("Error during Gurobi optimization", exc_info=e)

    # Save execution info
    result.status = ResultStatus(model.status)
    result.user_time = (
        end_cpu_times.user - start_cpu_times.user +
        end_cpu_times.children_user - start_cpu_times.children_user
    )
    result.system_time = (
        end_cpu_times.system - start_cpu_times.system +
        end_cpu_times.children_system - start_cpu_times.children_system
    )
    result.solve_time = model.runtime
    result.total_time = end_at - start_at

    # Save solution info
    result.solution_cost = model.ObjVal
    result.solution_best_bound = model.ObjBound
    result.solution_gap = model.MIPGap

    result.solution = []
    for var in model.getVars():
        if var.X != 0:
            var_name = var.VarName
            match = ONE_INDEX_SUBSET_VAR_REGEXP.match(var_name)
            if match:
                result.solution.append(int(match.group(1)))
            else:
                v0_print("[ERROR] Unexpected gurobi var name: {}", var_name)
    result.solution.sort()
    solution_info = analyse_solution(result.solution, result.solution_cost, data)
    result.add_solution_info(solution_info)

    # Save result
    model.write(str(log_file_path.with_suffix('.sol')))
    model.write(str(log_file_path.with_suffix('.json')))
    write_log(result, model)

    model.dispose()

    return result


def main():
    exec_id = datetime.utcnow().isoformat().replace(':', '_')

    result_file = Path(f'results-qo-{exec_id}.csv')
    if not result_file.exists():
        with open(result_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            writer.writeheader()

    conflict_thresholds = (1, 2)
    beasley_dir = Path(DATASETS_DIR_PATH, "beasley")
    instance_ids: list[str] = [
        str(Path("beasley", f.name))
        for f in beasley_dir.iterdir()
        if f.is_file() and f.suffix == '.txt'
    ]
    instance_ids.sort()

    LOGGER.info("Solving %s instance(s) with k=%s", len(instance_ids), conflict_thresholds)
    for k, instance_id in product(conflict_thresholds, instance_ids):
        try:
            instance = read_instance(instance_id, k)
            result = run_sccs_qo(instance, time_limit=3600)
        except Exception as e:
            LOGGER.critical(
                "Exception raised while solving instance %s with k=%s",
                instance.id, k, exc_info=e
            )
            continue

        try:
            with open(result_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
                writer.writerow(result)
        except Exception as e:
            LOGGER.critical(
                "Exception raised while saving result of instance %s with k=%s, "
                "result: %s", instance.id, k, result, exc_info=e
            )


if __name__ == '__main__':
    main()
