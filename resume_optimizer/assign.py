from ortools.linear_solver import pywraplp

if __name__ == "__main__":
    # Create the linear solver with the GLOP backend.
    solver = pywraplp.Solver.CreateSolver("GLOP")


def assign(*, compatibility: dict[tuple[int, int], int], count_weights: list[int] = []) -> list[tuple[int, int]]:
    """Assigns keywords to job descriptions to maximize compatibility.
    The compatibility matrix has tuple keys (keyword_index, job_description_index) and integer values.
    Conventionally the values are 0-3 but it doesn't really matter.
    The solution process can be described as analogous to a game.
    You have some keywords and assigning them to job descriptions yields points depending on how compatible
    the job description is to a keyword.
    There are also rules:
    - Each keyword can only be assigned to at most 1 job description.
    - The total number of keywords assigned to a job description is fixed to match count_weights.
    """
    solver = pywraplp.Solver.CreateSolver("SCIP")
    assignment = {indices: solver.IntVar(0, 1, "") for indices in compatibility.keys()}
    # Each keyword is assigned to exactly 1 job description.
    n_keywords = max(keyword_index for keyword_index, _ in compatibility) + 1
    n_job_descriptions = max(job_description_index for _, job_description_index in compatibility) + 1
    for keyword_index in range(n_keywords):
        solver.Add(
            solver.Sum(
                [
                    assignment[keyword_index, job_description_index]
                    for job_description_index in range(n_job_descriptions)
                ]
            )
            == 1
        )
    # Each job description has an exact number of keywords assigned in accordance with count_weights
    actual_weights = [
        count_weights[job_description_index] if job_description_index < len(count_weights) else 1
        for job_description_index in range(n_job_descriptions)
    ]
    total_weight = sum(actual_weights)
    n_keywords_assigned = 0
    for job_description_index in range(n_job_descriptions):
        n_keywords_assigned_cumulative = min(
            n_keywords, round(n_keywords / total_weight * sum(actual_weights[0 : job_description_index + 1]))
        )
        solver.Add(
            solver.Sum([assignment[keyword_index, job_description_index] for keyword_index in range(n_keywords)])
            == n_keywords_assigned_cumulative - n_keywords_assigned
        )
        n_keywords_assigned = n_keywords_assigned_cumulative
    assert n_keywords_assigned == n_keywords, f"Algorithm error: {n_keywords_assigned} assigned / {n_keywords} total"
    # Maximize sum of assignment * compatibility
    solver.Maximize(solver.Sum([compatibility[indices] * assignment[indices] for indices in compatibility]))
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        print(f"Total cost = {solver.Objective().Value()}\n")
        # Allow tolerance for floating point arithmetic when getting the solution value
        return [indices for indices in assignment if assignment[indices].solution_value() > 0.5]
    else:
        raise RuntimeError("No feasible keyword - job description assignment found.")
