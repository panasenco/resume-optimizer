import json
import logging
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
    logging.debug("keywords=")
    logging.debug(json.dumps(keywords, indent=4))
    logging.debug("---")
    logging.debug("position_summaries=")
    logging.debug(json.dumps(position_summaries, indent=4))
    logging.debug("---")

    # Stage 2: Assign keywords to resume sections while maximizing overall compatibility.
    compatibility = get_compatibility(job_description_keywords=keywords, position_highlights=default_highlights)
    # Print compatibility matrix in compact yet usable format
    logging.info("compatibility=")
    logging.info("    " + "".join(f"{d/10:.0f}" if d % 10 == 0 and d > 0 else " " for d in range(1, len(keywords) + 1)))
    logging.info("    " + "".join(f"{d%10:.0f}" for d in range(1, len(keywords) + 1)))
    logging.info("    " + "".join("-" for _ in range(len(keywords))))
    logging.info("\n".join([f"{i+1:<2}| " + "".join(map(str, row)) for i, row in enumerate(compatibility)]))
    # Remove keywords that don't clearly apply to any job while warning the user.
    removed_keywords = []
    x_string = ""
    # Go in reversed order to not throw off the indexing of subsequent elements when deleting
    for keyword_index, keyword in reversed(list(enumerate(keywords))):
        if (
            max(
                compatibility[resume_section_index][keyword_index]
                for resume_section_index in range(len(default_highlights))
            )
            == 0
        ):
            removed_keywords.append(keyword)
            x_string += "x"
            del keywords[keyword_index]
            for resume_section_index in range(len(default_highlights)):
                del compatibility[resume_section_index][keyword_index]
        else:
            x_string += " "
    logging.info("    " + x_string[::-1])
    logging.info("---")
    if len(removed_keywords) > 0:
        logging.warning(
            "WARNING: Some keywords won't be inserted because GPT-3.5 couldn't associate them with any resume section:"
        )
        logging.warning("\n".join(f"- {keyword}" for keyword in removed_keywords))
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
    logging.info("position_keywords=")
    logging.info(json.dumps(position_keywords, indent=4))
    logging.info("---")

    # Stage 3: Insert the keywords into the corresponding optimal summarized resume sections
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
