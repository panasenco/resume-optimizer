from ortools.linear_solver import pywraplp

if __name__ == "__main__":
    # Create the linear solver with the GLOP backend.
    solver = pywraplp.Solver.CreateSolver("GLOP")


def assign(compatibility: dict[tuple[int, int], int]) -> list[tuple[int, int]]:
    """Assigns keywords to job descriptions to maximize compatibility.
    The compatibility matrix has tuple keys (keyword_index, job_description_index) and integer values.
    Conventionally the values are 0-3 but it doesn't really matter.
    """
    n_keywords = max(keyword_index for keyword_index, _ in compatibility) + 1
    n_job_descriptions = max(job_description_index for _, job_description_index in compatibility) + 1
    solver = pywraplp.Solver.CreateSolver("SCIP")
    assignment = {indices: solver.IntVar(0, 1, "") for indices in compatibility.keys()}
    # Each keyword is assigned to at most 1 job description.
    for keyword_index in range(n_keywords):
        solver.Add(
            solver.Sum(
                [
                    assignment[keyword_index, job_description_index]
                    for job_description_index in range(n_job_descriptions)
                ]
            )
            <= 1
        )
    # Maximize sum of assignment * compatibility
    solver.Maximize(solver.Sum([compatibility[indices] * assignment[indices] for indices in compatibility]))
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        print(f"Total cost = {solver.Objective().Value()}\n")
        # Allow tolerance for floating point arithmetic when getting the solution value
        return [indices for indices in assignment if assignment[indices].solution_value() > 0.5]
    else:
        raise RuntimeError("No feasible keyword - job description assignment found.")
