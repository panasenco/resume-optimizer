from itertools import product

from ortools.linear_solver import pywraplp


def assign(*, compatibility: list[list[int]], count_weights: list[int] = []) -> list[tuple[int, int]]:
    """Assigns keywords to resume sections to maximize compatibility.
    The compatibility matrix has tuple keys (keyword_index, resume_section_index) and integer values.
    Conventionally the values are 0-3 but it doesn't really matter.
    The solution process can be described as analogous to a game.
    You have some keywords and assigning them to resume sections yields points depending on how compatible
    the resume section is to a keyword.
    There are also rules:
    - Each keyword can only be assigned to at most 1 resume section.
    - The total number of keywords assignable to a resume section is fixed to match count_weights.
    """
    solver = pywraplp.Solver.CreateSolver("SCIP")
    n_resume_sections = len(compatibility)
    n_keywords = len(compatibility[0])
    assignment = {indices: solver.IntVar(0, 1, "") for indices in product(range(n_keywords), range(n_resume_sections))}
    # Each keyword is assigned to exactly 1 resume section.
    for keyword_index in range(n_keywords):
        solver.Add(
            solver.Sum(
                [assignment[keyword_index, resume_section_index] for resume_section_index in range(n_resume_sections)]
            )
            == 1
        )
    # Each resume section has an exact number of keywords assigned in accordance with count_weights
    actual_weights = [
        count_weights[resume_section_index] if resume_section_index < len(count_weights) else 1
        for resume_section_index in range(n_resume_sections)
    ]
    total_weight = sum(actual_weights)
    n_keywords_assigned = 0
    for resume_section_index in range(n_resume_sections):
        n_keywords_assigned_cumulative = min(
            n_keywords, round(n_keywords / total_weight * sum(actual_weights[0 : resume_section_index + 1]))
        )
        solver.Add(
            solver.Sum([assignment[keyword_index, resume_section_index] for keyword_index in range(n_keywords)])
            == n_keywords_assigned_cumulative - n_keywords_assigned
        )
        n_keywords_assigned = n_keywords_assigned_cumulative
    assert n_keywords_assigned == n_keywords, f"Algorithm error: {n_keywords_assigned} assigned / {n_keywords} total"
    # Maximize sum of assignment * compatibility
    solver.Maximize(solver.Sum([assignment[indices] * compatibility[indices[1]][indices[0]] for indices in assignment]))
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        # Allow tolerance for floating point arithmetic when getting the solution value
        return [indices for indices in assignment if assignment[indices].solution_value() > 0.5]
    else:
        raise RuntimeError("No feasible keyword - resume section assignment found.")
