# resume-optimizer
Use AI to ensure your resume passes ATS keyword screening.

## Installation

```
pipx install git+https://github.com/panasenco/resume-optimizer.git
```

## Usage

```
export OPENAI_API_KEY="..."
resume-optimizer --resume-file default-resume.json --output-file optimized-resume.json --job-description-file job-description.txt --job-title 'Senior Data Engineer'
```