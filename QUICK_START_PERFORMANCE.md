# Quick Start: Performance Analysis

## One-Command Execution

Run this single command to generate complete performance analysis:

```bash
python project_performance_analysis.py
```

## What It Does

1. ✅ Benchmarks all major system components
2. ✅ Measures execution times (milliseconds)
3. ✅ Generates `performance_results.csv` with detailed metrics
4. ✅ Creates `vtu_performance_report.md` (VTU-ready)

## Output Files

- **`performance_results.csv`** - Detailed timing data (for analysis)
- **`vtu_performance_report.md`** - Complete VTU report (ready to include in project)

## For VTU Report

Simply include the `vtu_performance_report.md` file in your project documentation.

The report contains:
- Introduction and methodology
- Component descriptions
- Performance tables
- Analysis and findings
- Conclusion

## Troubleshooting

**Database Error?**
- Ensure PostgreSQL is running
- Check `app/config.py` for correct database settings

**Import Errors?**
- Install dependencies: `pip install -r requirements.txt`

**No PDF Files?**
- PDF extraction benchmark will be skipped (optional component)

---

**That's it!** Run the script and use the generated report for your VTU submission.


