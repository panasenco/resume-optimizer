# resume-optimizer
Use AI to ensure your resume passes ATS keyword screening.

## Installation

Recommended to install in an isolated environment with [pipx](https://pipx.pypa.io/stable/):

```
pipx install git+https://github.com/panasenco/resume-optimizer.git
```

## Usage

What you need:
- Your resume in the [JSON Resume](https://jsonresume.org/) format.
  Note that resume-optimizer only modifies the **highlights** lists of the **work** entries.
  If you don't already have a JSON Resume, I recommend initializing one with
  [jsonresume-docx](https://github.com/panasenco/jsonresume-docx): `jsonresume-docx init -r default-resume.json`.
- An [OpenAI API Key](https://www.howtogeek.com/885918/how-to-get-an-openai-api-key/)
- The job description
- The job title

What the tool outputs:
- Your JSON Resume, with work > highlights rewritten to contain the ATS keywords extracted from the resume.

Usage example:
```
export OPENAI_API_KEY="..."
resume-optimizer --resume-file default-resume.json --output-file optimized-resume.json --job-description-file job-description.txt --job-title 'Senior Data Engineer'
```

It's also possible to use a job description directly from the clipboard by setting the file to the dash (`-`):

In Linux (requires [xclip](https://linuxconfig.org/how-to-use-xclip-on-linux)):
```
xclip -selection c -o | resume-optimizer [...] --job-description-file -
```

On Mac OS:
```
pbpaste | resume-optimizer [...] --job-description-file -
```

In Windows PowerShell:
```
Get-Clipboard | resume-optimizer [...] --job-description-file -
```

## Rendering the resume

Unless you're applying for a *really* cool job, you probably can't submit your JSON resume directly.
You'll need to render it with one of the following approaches:
- [**jsonresume-docx**](https://github.com/panasenco/jsonresume-docx) (officially supported):
  Python command line tool that will render your JSON resume in a Microsoft Word docx format loved by recruiters.
  This option is what I personally use and is going to be supported best.
- [resumed](https://github.com/rbardini/resumed):
  JavaScript command line tool that allows you to render your resume in a variety of
  [themes](https://www.npmjs.com/search?q=jsonresume-theme).
- [Reactive Resume](https://rxresu.me/):
  Online resume builder that allows JSON Resume import (though I got a status code 400 when trying to import mine).

## Legal

Copyright (C) 2024 Aram Panasenco

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.