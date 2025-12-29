# Performance Analysis Guide
## VTU Academic Performance Analysis

This guide explains how to run the performance analysis for your VTU project report.

---

## Files Created

1. **`performance_timer.py`** - Timing decorator and statistics collection
2. **`project_performance_analysis.py`** - Main benchmark script
3. **`generate_performance_report.py`** - Report generator
4. **`vtu_performance_report.md`** - Generated performance report (VTU-ready)
5. **`performance_results.csv`** - Detailed timing results

---

## How to Run Performance Analysis

### Step 1: Ensure Dependencies
Make sure all project dependencies are installed:
```bash
pip install -r requirements.txt
```

### Step 2: Run Performance Benchmark
Execute the analysis script:
```bash
python project_performance_analysis.py
```

This will:
- Run benchmark tests on major system components
- Measure execution times (milliseconds)
- Save results to `performance_results.csv`
- Automatically generate `vtu_performance_report.md`

### Step 3: Review Results
- **CSV Results**: `performance_results.csv` contains detailed timing data
- **Markdown Report**: `vtu_performance_report.md` is ready for inclusion in your VTU report

---

## Components Tested

### Database Operations
- Paper addition (`database_add_paper`)
- Paper search (`database_search_papers`)
- List all papers (`database_list_all`)

### Search Operations
- Hybrid search (`hybrid_search`)
- Semantic search (`semantic_search`)

### Processing Operations
- PDF metadata extraction (`pdf_extraction`)
- Paper verification (`paper_verification`)
- Complete PDF processing pipeline (`integration_process_pdf`)

---

## Metrics Collected

For each operation:
- **Average Time**: Mean execution time across iterations
- **Minimum Time**: Best-case performance
- **Maximum Time**: Worst-case performance
- **Standard Deviation**: Performance consistency

---

## Customization

### Adjust Iteration Counts
Edit `project_performance_analysis.py` in the `main()` function:

```python
iterations = {
    'database': 50,      # Increase for more accurate database metrics
    'search': 30,        # Increase for more search tests
    'verification': 20,  # Increase for verification tests
    'pdf_extraction': 10 # Requires actual PDF files
}
```

### Add Custom Benchmarks
Add new benchmark functions using the `@timed_function` decorator:

```python
@timed_function("custom_operation")
def benchmark_custom_operation():
    # Your code here
    pass
```

---

## Understanding Results

### Fast Operations (< 100ms)
- Simple database queries
- Basic metadata retrieval

### Moderate Operations (100-500ms)
- Complex searches
- PDF extraction

### Slower Operations (> 500ms)
- External API calls
- Complete processing pipelines

---

## For VTU Report

The generated `vtu_performance_report.md` includes:
- ✅ Introduction and methodology
- ✅ Component descriptions
- ✅ Performance tables
- ✅ Analysis and findings
- ✅ Conclusion

You can directly include this report or sections of it in your VTU project documentation.

---

## Troubleshooting

### Database Connection Errors
Ensure PostgreSQL is running and configured correctly in `app/config.py`

### Missing Dependencies
Install all required packages:
```bash
pip install -r requirements.txt
```

### PDF Extraction Fails
PDF extraction requires actual PDF files. If no test PDFs are available, this benchmark will be skipped.

---

## Notes

- This analysis measures **execution time only** (no optimization performed)
- Results may vary based on system resources and database size
- Run benchmarks multiple times for more reliable averages
- The report format is VTU-academic style ready

---

**For VTU Submission**: Include the `vtu_performance_report.md` in your project documentation along with the `performance_results.csv` as supporting data.


