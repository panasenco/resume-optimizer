import argparse
import fileinput
import json

from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache

from .optimize import optimize_resume


def cli():
    # See https://docs.python.org/3/howto/argparse.html
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r",
        "--resume-file",
        help="filepath (or '-' for standard input) containing the default JSON resume",
        required=True,
    )
    parser.add_argument(
        "-j",
        "--job-description-file",
        help="filepath (or '-' for standard input) containing the job description",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--job-title",
        help="Title of the job in the job description",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="File to output the optimized JSON resume into. Defaults to 'optimized-resume.json'.",
        default="optimized-resume.json",
    )
    args = parser.parse_args()
    # Use cache to avoid executing some tasks that only use the default resume over and over again
    set_llm_cache(SQLiteCache(database_path=".langchain.db"))

    # Optimize the resume, reading the resume and job description contents from the provided files (or stdin)
    resume = optimize_resume(
        resume=json.loads("".join(fileinput.input(files=[args.resume_file]))),
        job_description="".join(fileinput.input(files=[args.job_description_file])),
        job_title=args.job_title,
    )

    # Save the updated resume to resume.json.
    with open(args.output, "w") as resume_file:
        resume_file.write(json.dumps(resume, indent=4))


if __name__ == "__main__":
    cli()
