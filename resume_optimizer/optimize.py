import json
from multiprocessing import Pool
from typing import Any


from .chains import distribute_keywords, summarize_resume_sections, optimize_highlights

def optimize_resume(*, resume: dict[str, Any], job_description: str) -> dict[str, Any]:
    default_highlights = [
        (
            i,
            experience["position"],
            "\n".join(f"- {highlight}" for highlight in experience["highlights"]),
        )
        for i, experience in enumerate(resume["work"])
    ]

    # Stage 1: Distribute keywords among resume sections and summarize resume sections in parallel
    with Pool(2) as pool:
        position_keywords_result = pool.apply_async(
            func=distribute_keywords,
            kwds={
                "position_highlights": default_highlights,
                "job_description": job_description,
            },
        )
        position_summaries_result = pool.apply_async(
            func=summarize_resume_sections,
            kwds={
                "position_highlights": default_highlights,
            },
        )
        position_keywords = position_keywords_result.get()
        position_summaries = position_summaries_result.get()
    print("position_keywords=")
    print(json.dumps(position_keywords, indent=4))
    print("---")
    print("position_summaries=")
    print(json.dumps(position_summaries, indent=4))
    print("---")

    # Stage 2: Generate optimized highlights for each resume section.

    n_experiences = len(default_highlights)
    print("optimized_highlights=")
    with Pool(n_experiences) as pool:
        optimized_highlights = pool.starmap(
            func=optimize_highlights,
            iterable=zip(
                position_summaries, position_keywords, [[3, 3, 2][i] if i < 3 else 1 for i in range(n_experiences)]
            ),
        )
    print(optimized_highlights)
    print("---")

    # Replace the highlights with the generated ones
    for i in range(n_experiences):
        resume["work"][i]["highlights"] = optimized_highlights[i]
    
    return resume