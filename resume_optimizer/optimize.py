import json
from multiprocessing import Pool
from typing import Any


from .assign import assign
from .chains import extract_keywords, get_compatibility, summarize_resume_sections, insert_keywords


def optimize_resume(*, resume: dict[str, Any], job_description: str, job_title: str) -> dict[str, Any]:
    default_highlights = [
        (
            experience["position"],
            "\n".join(f"- {highlight}" for highlight in experience["highlights"]),
        )
        for experience in resume["work"]
    ]
    # Stage 1: Summarize resume sections and extract job description keywords in parallel
    with Pool(2) as pool:
        keywords_result = pool.apply_async(
            func=extract_keywords,
            kwds={
                "job_description": job_description,
                "job_title": job_title,
            },
        )
        position_summaries_result = pool.apply_async(
            func=summarize_resume_sections,
            kwds={
                "position_highlights": default_highlights,
            },
        )
        keywords = keywords_result.get()
        position_summaries = position_summaries_result.get()
    print("keywords=")
    print(json.dumps(keywords, indent=4))
    print("---")
    print("position_summaries=")
    print(json.dumps(position_summaries, indent=4))
    print("---")

    # Stage 2: Assign keywords to resume sections while maximizing overall compatibility.
    compatibility = get_compatibility(job_description_keywords=keywords, position_highlights=default_highlights)
    print("compatibility=")
    print("\n".join(["".join(map(str, row)) for row in compatibility]))
    print("---")
    highlight_counts = [3, 3, 2]
    assignment = assign(compatibility=compatibility, count_weights=highlight_counts)
    position_keywords = [
        [
            keywords[keyword_index]
            for keyword_index, resume_section_index in assignment
            if resume_section_index == current_resume_section_index
        ]
        for current_resume_section_index in range(len(default_highlights))
    ]
    print("position_keywords=")
    print(json.dumps(position_keywords, indent=4))
    print("---")
    # Stage 3: Insert the keywords into the corresponding optimal summarized resume sections

    n_experiences = len(default_highlights)
    print("optimized_highlights=")
    # Have to do a pool rather than run batch() on the chain because the chain itself must be changed depending on
    # how many sections we have to return.
    with Pool(n_experiences) as pool:
        optimized_highlights = pool.starmap(
            func=insert_keywords,
            iterable=zip(
                position_summaries,
                position_keywords,
                [[3, 3, 2][i] if i < 3 else 1 for i in range(n_experiences)],
                [60] * n_experiences,
            ),
        )
    print(optimized_highlights)
    print("---")

    # Replace the highlights with the generated ones
    for i in range(n_experiences):
        resume["work"][i]["highlights"] = optimized_highlights[i]

    return resume
