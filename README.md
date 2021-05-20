# A PDF renamer for linguistics

This python script renames PDFs from a few linguistics journals (so far
*Glossa*, *Natural Language & Linguistic Theory*, *Syntax*, and *Linguistic
Inquiry*) based on information gathered from the PDF's metadata and the
document's first page.

Many papers from the following journals are recognised automatically:

- Behavioral and Brain Sciences
- Cognitive Psychology
- Cognitive Science
- Glossa
- Journal of Comparative Germanic Linguistics
- Journal of Germanic Linguistics
- Journal of Language Modelling
- Journal of Linguistics
- Language (with a Project Muse titlepage)
- Language and Linguistics Compass
- Lingua (not very old volumes)
- Linguistic Inquiry
- Linguistic Typology
- Linguistic Vanguard
- Natural Language & Linguistic Theory
- Natural Language Semantics
- Syntax
- The Linguistic Review
- Theoretical Linguistics
- Zeitschrift für Sprachwissenschaft

In addition to renaming files, the script can also output a `biblatex` entry
for the file.

The format of the renamed files is `Author [and Author [and Author]] (Year) - Title.pdf`.
The script now handles more than two authors consistently. The bibliography
entry is using `biblatex` fields (e.g. `journaltitle`) but can be adapted
easily. The script also recognises subtitles when introduced by ‘:’.

## Help

```
> python pdf-rename.py --help
usage: pdf-rename.py [-h] [--biblatex] [--copy] [--rename] filename

Rename PDFs automatically to include author(s), year, and title.

positional arguments:
  filename    PDF to rename

optional arguments:
  -h, --help  show this help message and exit
  --biblatex  create biblatex entry
  --copy      rename PDF file and keep original
  --rename    rename PDF file and delete original
```

## Examples

![Examples of pdf-rename.py](./img/pdf-renamev1.png)
