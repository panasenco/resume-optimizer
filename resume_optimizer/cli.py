import argparse
import fileinput
import json

from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache

from .optimize import optimize_resume

def cli():
    # See https://docs.python.org/3/howto/argparse.html
    parser = argparse.ArgumentParser()
    # Use cache to avoid executing some tasks that only use the default resume over and over again
    set_llm_cache(SQLiteCache(database_path=".langchain.db"))

    # Extract the initial JSON resume from default-resume.json
    with open("default-resume.json") as default_resume_file:
        resume = json.loads(default_resume_file.read())
    
    # Optimize the resume
    resume = optimize_resume(resume=resume, job_description="".join(fileinput.input()))

    # Save the updated resume to resume.json.
    with open("resume.json", "w") as resume_file:
        resume_file.write(json.dumps(resume, indent=4))


if __name__ == "__main__":
    cli()
