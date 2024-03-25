import json
import logging
from multiprocessing import Pool
from typing import Any


from .assign import assign
from .chains import extract_keywords, get_compatibility, get_difficulties, summarize_resume_sections, insert_keywords


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
    logging.info("keywords=")
    logging.info("\n".join(f"{i+1}. {k}" for i, k in enumerate(keywords)))
    logging.info("---")
    logging.debug("position_summaries=")
    logging.debug(json.dumps(position_summaries, indent=4))
    logging.debug("---")

    # Stage 2: Assign special compatibility level of 3 to keywords that appear verbatim in the default resume
    compatibility = [[None for _k in range(len(keywords))] for _r in range(len(default_highlights))]
    present_keyword_indices = set()
    for resume_section_index, (position, highlights) in enumerate(default_highlights):
        logging.debug(f"{highlights=}")
        for keyword_index, keyword in enumerate(keywords):
            if keyword.lower() in position.lower() or keyword.lower() in highlights.lower():
                compatibility[resume_section_index][keyword_index] = 3
                present_keyword_indices.add(keyword_index)
    # Set all other compatibilities for present keywords to zero
    for resume_section_index in range(len(default_highlights)):
        for present_keyword_index in present_keyword_indices:
            if compatibility[resume_section_index][present_keyword_index] is None:
                compatibility[resume_section_index][present_keyword_index] = 0
    logging.info(f"Keywords present in default resume = {[i+1 for i in present_keyword_indices]}")
    logging.debug(f"{compatibility=}")

    # Stage 3: Estimate keyword difficulty based on the job title
    difficulties = get_difficulties(job_description_keywords=keywords, job_title=job_title)
    logging.info("difficulties=")
    logging.info("\n".join(f"{i+1}. {d}" for i, d in enumerate(difficulties)))
    logging.info("---")
    # Remove difficult keywords that are not verbatim in the default resume
    removed_keyword_indices = {
        keyword_index
        for keyword_index, difficulty in enumerate(difficulties)
        if difficulty >= 3 and keyword_index not in present_keyword_indices
    }
    if len(removed_keyword_indices) > 0:
        logging.warning(
            "WARNING: Some keywords won't be inserted because the LLM gauged them as very difficult skills and "
            "they weren't mentioned explicitly in the default resume:"
        )
        logging.warning("\n".join(f"- {keywords[keyword_index]}" for keyword_index in removed_keyword_indices))
        logging.info("---")

    # Stage 4: Assign keywords that are neither present verbatim nor too difficult to resume sections while maximizing
    # overall compatibility.
    questionable_keyword_indices = sorted(set(range(len(keywords))) - present_keyword_indices - removed_keyword_indices)
    questionable_compatibility = get_compatibility(
        job_description_keywords=[keywords[i] for i in questionable_keyword_indices],
        position_highlights=default_highlights,
    )
    for resume_section_index in range(len(default_highlights)):
        for sequential_keyword_index, questionable_keyword_index in enumerate(questionable_keyword_indices):
            compatibility[resume_section_index][questionable_keyword_index] = questionable_compatibility[
                resume_section_index
            ][sequential_keyword_index]
    # Print compatibility matrix in compact yet usable format
    logging.info("compatibility=")
    logging.info("    " + "".join(f"{d/10:.0f}" if d % 10 == 0 and d > 0 else " " for d in range(1, len(keywords) + 1)))
    logging.info("    " + "".join(f"{d%10:.0f}" for d in range(1, len(keywords) + 1)))
    logging.info("    " + "".join("-" for _ in range(len(keywords))))
    logging.info(
        "\n".join(
            [
                f"{i+1:<2}| " + "".join([str(v) if v is not None else "N" for v in row])
                for i, row in enumerate(compatibility)
            ]
        )
    )
    logging.info("---")
    # Stage 5: Assign undeleted keywords to resume sections
    # Sorting the keywords in order from most to least difficult encourages the LLM to use the most important ones first
    difficulty_sorted_keyword_indices = [
        sorted_keyword_index
        for _difficulty, sorted_keyword_index in sorted(
            [
                (difficulties[keyword_index], keyword_index)
                for keyword_index in (set(range(len(keywords))) - removed_keyword_indices)
            ],
            reverse=True,
        )
    ]
    highlight_counts = [3, 3, 2]
    assignment = assign(
        compatibility=[
            [compatibility_row[keyword_index] for keyword_index in difficulty_sorted_keyword_indices]
            for compatibility_row in compatibility
        ],
        count_weights=highlight_counts,
    )
    logging.debug(f"{assignment=}")
    position_keywords = [
        [
            keywords[difficulty_sorted_keyword_indices[internal_index]]
            for internal_index, resume_section_index in assignment
            if resume_section_index == current_resume_section_index
        ]
        for current_resume_section_index in range(len(default_highlights))
    ]
    logging.info("position_keywords=")
    logging.info(json.dumps(position_keywords, indent=4))
    logging.info("---")

    # Stage 6: Insert the keywords into the corresponding optimal summarized resume sections
    n_experiences = len(default_highlights)
    logging.debug("optimized_highlights=")
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
    logging.debug(optimized_highlights)
    logging.debug("---")

    # Replace the highlights with the generated ones
    for i in range(n_experiences):
        resume["work"][i]["highlights"] = optimized_highlights[i]

    return resume
