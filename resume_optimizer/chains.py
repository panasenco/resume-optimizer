import logging
from operator import itemgetter
from textwrap import dedent

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import MarkdownListOutputParser, NumberedListOutputParser, StrOutputParser
from langchain_core.prompts.chat import (
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

OPENAI_REPRODUCIBILITY_SEED = 338598

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


KEYWORD_DIFFICULTY_CHAIN = ChatPromptTemplate.from_messages(
    [
        SystemMessage(
            content=dedent(
                """\
                    Consider an average professional with the job title provided by the user.
                    Assign difficulty values to each keyword based on how difficult it would be to learn for that
                    average professional.
                     1: The keyword corresponds to a skill that would either take less than a month for the average
                        professional to learn OR is something that the average professional is already expected to know.
                     2: The keyword corresponds to a vague skill that would take over a month to learn OR a *concrete*
                        technology or skill that would take between 1 and 3 months for the average professional to
                        learn.
                     3: The keyword corresponds to a *concrete* technology or skill that would take over 3 months for
                        the average professional to learn.

                    Note that you should only assign the score of 3 to technologies or skills that are both difficult
                    and *concrete*, not to buzzwords.
                    E.g. keywords like "modernize for scale" or "building data warehouses" or "cloud stack" should not
                    ever be assigned a score of 3 because they are vague and buzzwordy.

                    Output the difficulty score in a numbered list in sequential order and matching the corresponding
                    keyword numbers.

                    Example:
                    1. 2
                    2. 1
                    3. 3
                    ...
                    """
            )
        ),
        HumanMessagePromptTemplate.from_template(
            template=dedent(
                """\
                        Job title:
                        {job_title}
                        Job description keywords to estimate difficulty for:
                        {numbered_job_description_keywords}
                        """
            ),
        ),
        SystemMessagePromptTemplate.from_template(
            template="Output the difficulty values for all {n_keywords} keywords in a numbered list, no other text."
        ),
    ]
) | ChatOpenAI(
    temperature=0,
    model_kwargs={"seed": OPENAI_REPRODUCIBILITY_SEED},
    model_name="gpt-4",
)


def get_difficulties(
    *,
    job_description_keywords: list[str],
    job_title: str,
) -> list[int]:
    """Compute a compatibility matrix between job description keywords and (position, highlights) resume section tuples."""
    raw_difficulties = KEYWORD_DIFFICULTY_CHAIN.invoke(
        {
            "job_title": job_title,
            "numbered_job_description_keywords": "\n".join(
                f"{i}. {k}" for i, k in enumerate(job_description_keywords, start=1)
            ),
            "n_keywords": len(job_description_keywords),
        }
    )
    logging.debug(f"{raw_difficulties=}")
    dict_difficulties = {
        int(pair[0]): int(pair[1]) for pair in [row.split(". ") for row in raw_difficulties.content.split("\n")]
    }
    logging.debug(f"{dict_difficulties=}")
    expected_score_keys = list(range(1, len(job_description_keywords) + 1))
    score_keys = list(dict_difficulties.keys())
    assert score_keys == expected_score_keys, f"Numbering mismatch: {expected_score_keys=}, {score_keys=}"
    return list(dict_difficulties.values())


KEYWORD_COMPATIBILITY_CHAIN = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            template=dedent(
                """\
                    Objective: Estimate how compatible a resume section is to a list of keywords.

                    Compatibility values are numbers ranging from 0 to 2:
                    - 0: There is no indication that the keyword could apply to the resume section.
                    - 1: There is some indication that the keyword could apply to the resume section.
                    - 2: The keyword definitely applies to the resume section.

                    Output the compatibilities in a numbered list in sequential order and matching the corresponding
                    keyword numbers.

                    Example:
                    1. 0
                    2. 2
                    3. 1
                    ...

                    Output the compatibility values for all {n_keywords} keywords in a numbered list, no other text.

                    """
            ),
        ),
        HumanMessagePromptTemplate.from_template(
            template=dedent(
                """\
                    Resume section to estimate compatibility for:
                    {resume_section}
                    Job description keywords to estimate compatibility for:
                    {numbered_job_description_keywords}
                    """
            ),
        ),
        SystemMessagePromptTemplate.from_template(
            template="Output the compatibility values for all {n_keywords} keywords in a numbered list, no other text."
        ),
    ]
) | ChatOpenAI(
    temperature=0,
    model_kwargs={"seed": OPENAI_REPRODUCIBILITY_SEED},
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
    job_title: str,
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
                    template=dedent(
                        """\
                        You are a resume writer, expert in tailoring resumes to jobs with the title {job_title}.
                        Your objective is to turn a resume position summary into a list of position highlights that
                        contain the required ATS (applicant tracking system) keywords.

                        Write just the highlight string itself without any other metadata in each highlight string.
                        WRONG:
                        - Highlight 1: Demonstrated expertise in ...
                        RIGHT:
                        - Demonstrated expertise in ...
                        
                        Associate big accomplishments with keywords corresponding to difficult skills and major,
                        relevant technologies.
                        WRONG:
                        - Developed state-of-the art data architecture using Lucid Charts.
                        RIGHT:
                        - Developed state-of-the-art data architecture using Snowflake, Terraform, and dbt.
                        """
                    ),
                ),
                HumanMessagePromptTemplate.from_template(
                    template=dedent(
                        """\
                        Job title to optimize for: {job_title}.
                        Position summmary to insert keywords into:
                        {position_summary}

                        ------

                        ATS keywords to inject into the position summary:
                        {position_keywords}
                        """
                    )
                ),
                SystemMessagePromptTemplate.from_template(
                    template=dedent(
                        """\
                        Output the {highlight_count} highlights as a Markdown list, e.g.:
                        - Highlight 1
                        - Highlight 2
                        - Highlight 3

                        Only answer with the specified Markdown list format, no other text.
                        Remember to keep the number of generated highlights to {highlight_count} highlights while
                        inserting as many provided ATS keywords into them as possible!
                        """
                    ),
                ),
            ]
        )
        | ChatOpenAI(model_name="gpt-4", max_tokens=tokens_per_highlight * highlight_count)
        | MarkdownListOutputParser()
    ).invoke(
        {
            "job_title": job_title,
            "position_summary": position_summary,
            "position_keywords": position_keywords,
            "highlight_count": highlight_count,
        }
    )


def refine_highlights(
    *,
    job_title: str,
    highlights_keywords: list[tuple[str, list[str]]],
    tokens_per_highlight: int,
) -> list[str]:
    logging.debug(f"{highlights_keywords=}")
    batch_input = [
        {
            "job_title": job_title,
            "resume_section": resume_section,
            "keywords": "\n".join(f"- {keyword}" for keyword in keywords),
            "tokens_per_highlight": tokens_per_highlight,
        }
        for resume_section, keywords in highlights_keywords
    ]
    logging.debug(f"{batch_input=}")
    return (
        {
            "section_criticisms": (
                ChatPromptTemplate.from_messages(
                    [
                        SystemMessagePromptTemplate.from_template(
                            template=dedent(
                                """\
                            You are a manager hiring for a position with the title '{job_title}'.
                            Your objective is to evaluate a resume section.

                            Think step by step. List weaknesses that exist within the section, if any.
                            Some examples to consider:
                            - Does the person appear professional by writing in a third person, neutral tone?
                                WRONG:
                                - My engineering expertise was pivotal
                                RIGHT:
                                - Provided pivotal engineering expertise
                            - Does the person appear unnatural by using quotes around some keywords?
                                WRONG:
                                - Streamlined 'data pipelines'
                                RIGHT:
                                - Streamlined data pipelines
                                WRONG:
                                - Enhanced 'Big data' pipelines
                                RIGHT:
                                - Enhanced Big data pipelines
                            
                            Don't limit yourself to the above examples, think of any other shortcomings of the section
                            from the perspective of a manager hiring for a '{job_title}' job that make the candidate appear
                            unprofessional, illogical, or unnatural.
                            """
                            ),
                        ),
                        HumanMessagePromptTemplate.from_template(template="Resume section:\n{resume_section}"),
                    ]
                )
                | ChatOpenAI(model_name="gpt-4")
                | StrOutputParser()
            ),
            "job_title": itemgetter("job_title"),
            "keywords": itemgetter("keywords"),
            "resume_section": itemgetter("resume_section"),
            "tokens_per_highlight": itemgetter("tokens_per_highlight"),
        }
        | ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    template=dedent(
                        """\
                        You are a resume writer, expert in tailoring resumes to jobs with the title {job_title}.
                        Rewrite the provided resume section using the provided criticisms.
                        IMPORTANT: Be careful to not remove the provided ATS keywords while rewriting!
                        Limit the output to {tokens_per_highlight} tokens.
                        """
                    ),
                ),
                HumanMessagePromptTemplate.from_template(
                    template=dedent(
                        """\
                        Job title to optimize for: {job_title}.
                        Resume section:
                        {resume_section}
                        ---
                        Criticisms:
                        {section_criticisms}
                        ---
                        ATS keywords to preserve:
                        {keywords}
                        """
                    )
                ),
            ]
        )
        | ChatOpenAI(model_name="gpt-4", max_tokens=tokens_per_highlight)
        | StrOutputParser()
    ).batch(
        [
            {
                "job_title": job_title,
                "resume_section": resume_section,
                "keywords": "\n".join(f"- {keyword}" for keyword in keywords),
                "tokens_per_highlight": tokens_per_highlight,
            }
            for resume_section, keywords in highlights_keywords
        ]
    )
