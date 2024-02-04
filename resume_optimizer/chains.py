from operator import itemgetter
from textwrap import dedent

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser, MarkdownListOutputParser, StrOutputParser
from langchain_core.prompts.chat import (
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

DISTRIBUTE_KEYWORDS_CHAIN = (
    {
        "job_description_keywords": (
            ChatPromptTemplate.from_messages(
                [
                    SystemMessage(
                        content=dedent(
                            """\
                            Background:
                            You are an expert ATS (applicant tracking system) keyword extractor.

                            Objective:
                            Extract ATS keywords from the below job description that are relevant to the provided
                            position title, if any.

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

                            Output the keywords as a Markdown list, e.g.:
                            - Keyword 1
                            - Keyword 2
                            - Keyword 3
                            """
                        )
                    ),
                    HumanMessagePromptTemplate.from_template(template="{job_description}"),
                ]
            )
            | ChatOpenAI(model_name="gpt-4")
            | StrOutputParser()
        ),
        "position_highlights": itemgetter("position_highlights"),
    }
    | ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                # Note literal '{' and '}' need to be doubled up in an f-string.
                # See https://docs.python.org/3/library/string.html#format-string-syntax
                template=dedent(
                    """\
                    Objective:
                    Distribute just the following list of ATS (applicant tracking system) keywords among the resume
                    sections provided by the user:
                    {job_description_keywords}

                    ---
                    
                    Don't extract any keywords from the text, only take keywords from the list above!
                    Only assign a keyword to a section when that section could be relevant to that keyword.
                    Try to assign a keyword to the section that matches it best.
                    Use as many of the keywords as you can.

                    Don't put competing and/or mutually exclusive technologies into one section.
                    WRONG: Amazon AWS and Microsoft Azure
                    WRONG: Google BigQuery and Snowflake

                    Don't put technologies that wouldn't be found together in a technology stack into one section.
                    WRONG: Spark SQL and SQL Server Integration Services

                    Spread the keywords out, don't put them all in one section.
                    The spread of keywords among sections shouldn't be completely uniform, but instead roughly follow
                    the following weighted distribution:
                    - 3 parts for the first section
                    - 3 parts for the second section
                    - 2 parts for the third section
                    - 1 part for each subsequent section

                    Output format (use keys from the user input):
                    {{
                        "0": [
                            "ATS Keyword 1",
                            "ATS Keyword 2"
                        ],
                        "1": [
                            "ATS Keyword 3"
                        ]
                    }}
                    ---
                    
                    Only answer with the specified JSON format, no other text.
                    Maximize the number of ATS keywords matched while spreading them among the sections.
                    """
                ),
            ),
            HumanMessagePromptTemplate.from_template(template="{position_highlights}"),
            SystemMessagePromptTemplate.from_template(
                template=dedent(
                    """\
                    REMINDER: DO NOT take any keywords from user input. ONLY use keywords from this list:
                    {job_description_keywords}
                    """
                )
            ),
        ]
    )
    | ChatOpenAI(
        model_name="gpt-4-turbo-preview",
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    | JsonOutputParser()
)


def distribute_keywords(
    *,
    job_description: str,
    position_highlights: list[tuple[int, str, str]],
) -> dict[str, list[str]]:
    """Extract ATS keywords from the job description and distribute them among resume positions.
    Ideally the job description also includes the position name in the format:
    Position: {Title}
    Text:
    {Job description}
    """
    distributed_keywords_raw = DISTRIBUTE_KEYWORDS_CHAIN.invoke(
        {
            "job_description": job_description,
            "position_highlights": "\n-\n".join(
                f"Key: {i}. Position: {position}\nHighlights:\n{highlights}"
                for i, position, highlights in position_highlights
            ),
        }
    )
    assert all(key.isnumeric() for key in distributed_keywords_raw), "LLM returned non-integer keys"
    distributed_keywords = []
    for i, (key, keywords) in enumerate(distributed_keywords_raw.items()):
        assert int(key) == i, "LLM didn't return consecutive integer keys starting with 0"
        distributed_keywords.append(keywords)
    return distributed_keywords


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


def summarize_resume_sections(*, position_highlights: list[tuple[int, str, str]]) -> list[str]:
    # Summarize each section of the default resume to eliminate any ATS keywords that are already there.
    return SUMMARIZE_RESUME_SECTION_CHAIN.batch(
        [
            {
                "position": position,
                "highlights": highlights,
            }
            for i, position, highlights in position_highlights
        ]
    )


def optimize_highlights(
    position_summary: str,
    position_keywords: list[str],
    n_highlights: int,
    /,
) -> list[list[str]]:
    return (
        ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    # Note literal '{' and '}' need to be escaped by doubling in an f-string.
                    # See https://docs.python.org/3/library/string.html#format-string-syntax
                    template=dedent(
                        """\
                        You are an expert resume writer.
                        Your objective is to turn a resume position summary into a list of {n_highlights} position
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
                        Remember to keep the number of generated highlights to {n_highlights} highlights while inserting
                        as many provided ATS keywords into them as possible!
                        """
                    ),
                ),
                HumanMessagePromptTemplate.from_template(
                    template=dedent(
                        """\
                        Generate position highlights for the following ATS keywords:
                        {ats_keywords}
                        """
                    )
                ),
            ]
        )
        | ChatOpenAI(model_name="gpt-4", max_tokens=60 * n_highlights)
        | MarkdownListOutputParser()
    ).invoke(
        {
            "position_summary": position_summary,
            "ats_keywords": position_keywords,
            "n_highlights": n_highlights,
        }
    )