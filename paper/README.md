# Building the IEEE Paper

## Prerequisites
- LaTeX distribution (TeX Live or MiKTeX)
- `pdflatex` and `bibtex`

## Files
- `ieee_paper.tex`: main paper
- `references.bib`: bibliography entries
- `figures/architecture_placeholder`: provide a PDF/PNG named `architecture_placeholder.pdf` or `.png`

## Build
On Windows PowerShell or bash:
```bash
pdflatex ieee_paper.tex
bibtex ieee_paper
pdflatex ieee_paper.tex
pdflatex ieee_paper.tex
```

Resulting PDF: `ieee_paper.pdf`

## Notes
- Replace figure placeholders in `figures/` with exported diagrams (e.g., from Mermaid or draw.io)
- Update author names, affiliations, and emails in the `\author{}` block
- Expand tables in the Results section with measured values
