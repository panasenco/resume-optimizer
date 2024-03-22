import logging
from textwrap import dedent

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import MarkdownListOutputParser, NumberedListOutputParser, StrOutputParser
from langchain_core.prompts.chat import (
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

EXTRACT_KEYWORDS_CHAIN = (
    ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=dedent(
                    """\
                    Background:
                    You are an expert ATS (applicant tracking system) keyword extractor.

                    Objective:
                    Extract ATS keywords from the job description provided by the user that are relevant to the provided
                    job title, if any.

                    Combine all ATS keywords from all text sections into a single set.

                    Don't include a college/university degree as an ATS keyword.
                    WRONG:
                    - Bachelor's Degree in Computer Science

                    Don't combine multiple ATS keywords into a single one
                    WRONG:
                    - Diverse data sources and data formats (xml, json, yaml, parquet, avro, delta)
                    RIGHT:
                    - data sources
                    - data formats
                    - xml
                    - json
                    - yaml
                    - parquet
                    - avro
                    - delta

                    Only include parentheses if it's an abbreviation, otherwise split into multiple keywords.
                    RIGHT:
                    - SQL Server Integration Services (SSIS)

                    WRONG:
                    - Streaming (Kafka)
                    RIGHT:
                    - Streaming
                    - Kafka

                    Output the keywords as a numbered list, e.g.:
                    1. Keyword 1
                    2. Keyword 2
                    3. Keyword 3
                    """
                )
            ),
            HumanMessagePromptTemplate.from_template(
                template=dedent(
                    """\
                    Job Title: {job_title}
                    Job Description:
                    {job_description}
                    """
                )
            ),
        ]
    )
    | ChatOpenAI(model_name="gpt-4")
    | NumberedListOutputParser()
)


def extract_keywords(
    *,
    job_description: str,
    job_title: str,
) -> list[str]:
    """Extract ATS keywords from the job description and distribute them among resume positions."""
    return EXTRACT_KEYWORDS_CHAIN.invoke(
        {
            "job_description": job_description,
            "job_title": job_title,
        }
    )


KEYWORD_COMPATIBILITY_CHAIN = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            # Note literal '{' and '}' need to be doubled up in an f-string.
            # See https://docs.python.org/3/library/string.html#format-string-syntax
            template=dedent(
                """\
                    Objective: Estimate how compatible a resume section is to a list of keywords.

                    Compatibility values are numbers ranging from 0 to 3:
                    - 0: There is no indication that the keyword could apply to the resume section.
                    - 0: There is no mention of the keyword, and a competing technology keyword is mentioned instead.
                    - 1: There is some indication that the keyword could apply to the resume section.
                    - 2: The keyword definitely applies somewhat to the resume section.
                    - 3: The keyword definitely applies strongly to the resume section.

                    Output the compatibilities in a numbered list in sequential order and matching the corresponding
                    keyword numbers.

                    Example:
                    1. 0
                    2. 2
                    3. 3
                    ...

                    Output the compatibility values for all {n_keywords} keywords in a numbered list, no other text.

                    Resume section to estimate compatibility for:
                    {resume_section}
                    """
            ),
        ),
        HumanMessagePromptTemplate.from_template(
            template=dedent(
                """\
                    Job description keywords to estimate compatibility for:
                    {numbered_job_description_keywords}
                    """
            ),
        ),
    ]
) | ChatOpenAI(
    model_name="gpt-3.5-turbo",
    # model_name="gpt-4",
)


def get_compatibility(
    *,
    job_description_keywords: list[str],
    position_highlights: list[tuple[str, str]],
) -> dict[tuple[int, int], int]:
    """Compute a compatibility matrix between job description keywords and (position, highlights) resume section tuples."""
    numbered_keywords = "\n".join(f"{i}. {k}" for i, k in enumerate(job_description_keywords, start=1))
    logging.info("numbered_keywords=")
    logging.info(numbered_keywords)
    logging.info("---")
    raw_compatibilities = KEYWORD_COMPATIBILITY_CHAIN.batch(
        [
            {
                "numbered_job_description_keywords": numbered_keywords,
                "resume_section": f"Job title: {position}\nHighlights:\n{highlights}",
                "n_keywords": len(job_description_keywords),
            }
            for position, highlights in position_highlights
        ]
    )
    logging.debug(f"{raw_compatibilities=}")
    dict_compatibilities = [
        {int(pair[0]): int(pair[1]) for pair in [row.split(". ") for row in section.content.split("\n")]}
        for section in raw_compatibilities
    ]
    logging.debug(f"{dict_compatibilities=}")
    expected_score_keys = list(range(1, len(job_description_keywords) + 1))
    for compatibility in dict_compatibilities:
        score_keys = list(compatibility.keys())
        assert score_keys == expected_score_keys, f"Numbering mismatch: {expected_score_keys=}, {score_keys=}"
    return [list(compatibility.values()) for compatibility in dict_compatibilities]


SUMMARIZE_RESUME_SECTION_CHAIN = (
    ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=dedent(
                    """
                    Background:
                    You are an expert resume section summarizer.
                    You value understanding a candidate's skills beyond the exact technologies used.
                    You always strive to summarize what the candidate did from a big picture perspective rather than
                    parroting the exact tools and technologies they listed.

                    Objective:
                    Summarize the resume section from a high-level perspective.
                    Don't include the job title in your summary.
                    Prioritize including any quantifiable results (e.g. "resolved over 200 support tickets") in your
                    summary.

                    Write in third-person without pronouns.
                    WRONG: "The candidate has significant experience in widgets"
                    RIGHT: "Has significant experience in widgets"

                    Write in a conservative tone, avoid grandiose statements.
                    WRONG: "Has profound experience with gadgets."
                    RIGHT: "Experienced with gadgets."

                    Please replace all instances of specific names of technologies, frameworks, tools, formats, etc.
                    with bigger-picture concepts that allow the reader to understand the impact of the work.

                    WRONG: "Has experience working with CSV, JSON, and XML/HTML data."
                    WRONG: "Has experience working with various data formats such as CSV, JSON, and XML/HTML."
                    RIGHT: "Has experience working with multiple data formats."

                    WRONG: "Confident in various technologies including Python, dbt, Terraform, GitLab CI."
                    RIGHT: "Confident in programming, using analytics engineering frameworks, and tools for infrastructure-as-code and automated deployments."

                    WRONG: "Experienced in deploying AWS resources with Terraform."
                    RIGHT: "Experienced in deploying cloud resources through infrastructure-as-code tools."
                    """
                )
            ),
            HumanMessagePromptTemplate.from_template(
                template="""
                    Job title: {position}
                    Highlights:
                    {highlights}
                    """
            ),
        ]
    )
    | ChatOpenAI(model_name="gpt-4", max_tokens=300)
    | StrOutputParser()
)


def summarize_resume_sections(*, position_highlights: list[tuple[str, str]]) -> list[str]:
    # Summarize each section of the default resume to eliminate any ATS keywords that are already there.
    return SUMMARIZE_RESUME_SECTION_CHAIN.batch(
        [
            {
                "position": position,
                "highlights": highlights,
            }
            for position, highlights in position_highlights
        ]
    )


def insert_keywords(
    position_summary: str,
    position_keywords: list[str],
    highlight_count: int,
    tokens_per_highlight: int,
    /,
) -> list[str]:
    return (
        ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    # Note literal '{' and '}' need to be escaped by doubling in an f-string.
                    # See https://docs.python.org/3/library/string.html#format-string-syntax
                    template=dedent(
                        """\
                    You are an expert resume writer.
                    Your objective is to turn a resume position summary into a list of {highlight_count} position
                    highlights that contain the required ATS (applicant tracking system) keywords.

                    Output the highlights as a Markdown list, e.g.:
                    - Highlight 1
                    - Highlight 2
                    - Highlight 3

                    POSITION SUMMARY:
                    {position_summary}

                    ---
                    
                    Write just the highlight string itself without any other metadata in each highlight string.
                    WRONG:
                    - Highlight 1: Demonstrated expertise
                    RIGHT:
                    - Demonstrated expertise
                    
                    Use a third person neutral tone. Avoid pronouns.
                    WRONG:
                    - My engineering expertise was pivotal
                    RIGHT:
                    - Provided pivotal engineering expertise
                    
                    Don't allow quotes around the keywords you insert, sound natural.

                    WRONG:
                    - Streamlined 'data pipelines'
                    RIGHT:
                    - Streamlined data pipelines
                    WRONG:
                    - Enhanced 'Big data' pipelines
                    RIGHT:
                    - Enhanced Big data pipelines
                    
                    Only answer with the specified Markdown list format, no other text.
                    Remember to keep the number of generated highlights to {highlight_count} highlights while inserting
                    as many provided ATS keywords into them as possible!
                    """
                    ),
                ),
                HumanMessagePromptTemplate.from_template(
                    template=dedent(
                        """\
                    Generate position highlights for the following ATS keywords:
                    {position_keywords}
                    """
                    )
                ),
            ]
        )
        | ChatOpenAI(model_name="gpt-4", max_tokens=tokens_per_highlight * highlight_count)
        | MarkdownListOutputParser()
    ).invoke(
        {
            "position_summary": position_summary,
            "position_keywords": position_keywords,
            "highlight_count": highlight_count,
        }
    )
