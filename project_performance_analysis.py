"""
Project Performance Analysis Script
Performs benchmark tests on major system components for VTU performance analysis.
"""

import sys
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from performance_timer import get_timer, timed_function
from app.database_unified import get_unified_database_manager, get_unified_paper_repository
try:
    from app.utils.enhanced_pdf_extractor import extract_paper_metadata, EnhancedPDFExtractor
except ImportError as e:
    logger.warning(f"Could not import PDF extractor: {e}")
    extract_paper_metadata = None

try:
    from app.utils.post_import_verifier import post_import_verifier
except ImportError as e:
    logger.error(f"Could not import verifier: {e}")
    sys.exit(1)

try:
    from app.utils.hybrid_search_engine import HybridSearchEngine
    from app.utils.semantic_search_engine import SemanticSearchEngine
except ImportError as e:
    logger.warning(f"Could not import search engines: {e}")
    HybridSearchEngine = None
    SemanticSearchEngine = None

try:
    from app.integration_manager import get_integration_manager
except ImportError as e:
    logger.warning(f"Could not import integration manager: {e}")
    get_integration_manager = None


# Instrumented wrapper functions
@timed_function("database_add_paper")
def benchmark_add_paper(repo, paper_data: Dict[str, Any]) -> int:
    """Benchmark paper addition to database."""
    return repo.add_paper(paper_data)


@timed_function("database_search_papers")
def benchmark_search_papers(repo, query: str, limit: int = 50):
    """Benchmark paper search operation."""
    return repo.search_papers(query, limit=limit)


@timed_function("database_list_all")
def benchmark_list_all(repo):
    """Benchmark listing all papers."""
    return repo.list_all()


@timed_function("pdf_extraction")
def benchmark_pdf_extraction(file_path: str):
    """Benchmark PDF metadata extraction."""
    return extract_paper_metadata(file_path)


@timed_function("paper_verification")
def benchmark_verification(paper: Dict[str, Any]):
    """Benchmark paper verification."""
    return post_import_verifier.verify_paper(paper)


@timed_function("hybrid_search")
def benchmark_hybrid_search(engine: HybridSearchEngine, query: str):
    """Benchmark hybrid search operation."""
    return engine.search(query, top_k=10)


@timed_function("semantic_search")
def benchmark_semantic_search(engine: SemanticSearchEngine, query: str):
    """Benchmark semantic search operation."""
    return engine.search(query, top_k=10)


# Note: Integration process_pdf benchmark removed as it requires actual PDF files
# and is covered by individual component benchmarks


class PerformanceBenchmark:
    """Performance benchmarking class."""
    
    def __init__(self):
        self.repo = get_unified_paper_repository()
        
        if HybridSearchEngine:
            self.search_engine = HybridSearchEngine(self.repo)
        else:
            self.search_engine = None
            
        if SemanticSearchEngine:
            self.semantic_engine = SemanticSearchEngine(self.repo)
        else:
            self.semantic_engine = None
            
        if get_integration_manager:
            self.integration_manager = get_integration_manager()
        else:
            self.integration_manager = None
            
        self.timer = get_timer()
        
    def prepare_test_data(self) -> Dict[str, Any]:
        """Prepare sample test paper data."""
        return {
            'title': 'Performance Analysis of Research Paper Management Systems',
            'authors': 'Test Author, Another Author',
            'year': 2024,
            'abstract': 'This paper presents a comprehensive performance analysis of research paper management systems.',
            'doi': '10.1234/test.2024.001',
            'journal': 'Test Journal of Computing',
            'publisher': 'Test Publishers',
            'file_path': 'test_paper.pdf',
            'full_text': 'Full text content for testing purposes.',
        }
    
    def benchmark_database_operations(self, iterations: int = 50):
        """Benchmark database operations."""
        logger.info(f"Benchmarking database operations ({iterations} iterations)...")
        
        test_paper = self.prepare_test_data()
        
        # Test add_paper
        logger.info("  Testing add_paper...")
        for i in range(iterations):
            paper_data = test_paper.copy()
            paper_data['title'] = f"{test_paper['title']} - Iteration {i}"
            try:
                benchmark_add_paper(self.repo, paper_data)
            except Exception as e:
                logger.warning(f"  Add paper failed: {e}")
        
        # Test search_papers
        logger.info("  Testing search_papers...")
        queries = ['performance', 'analysis', 'system', 'research', 'paper']
        for i in range(iterations):
            query = queries[i % len(queries)]
            try:
                benchmark_search_papers(self.repo, query, limit=20)
            except Exception as e:
                logger.warning(f"  Search failed: {e}")
        
        # Test list_all
        logger.info("  Testing list_all...")
        for i in range(iterations):
            try:
                benchmark_list_all(self.repo)
            except Exception as e:
                logger.warning(f"  List all failed: {e}")
    
    def benchmark_search_operations(self, iterations: int = 30):
        """Benchmark search operations."""
        logger.info(f"Benchmarking search operations ({iterations} iterations)...")
        
        if not self.search_engine or not self.semantic_engine:
            logger.warning("  Search engines not available, skipping search benchmarks")
            return
        
        queries = [
            'machine learning algorithms',
            'deep learning neural networks',
            'data mining techniques',
            'artificial intelligence',
            'computer vision applications'
        ]
        
        for i in range(iterations):
            query = queries[i % len(queries)]
            
            # Test hybrid search
            try:
                benchmark_hybrid_search(self.search_engine, query)
            except Exception as e:
                logger.warning(f"  Hybrid search failed: {e}")
            
            # Test semantic search
            try:
                benchmark_semantic_search(self.semantic_engine, query)
            except Exception as e:
                logger.warning(f"  Semantic search failed: {e}")
    
    def benchmark_verification(self, iterations: int = 20):
        """Benchmark paper verification."""
        logger.info(f"Benchmarking paper verification ({iterations} iterations)...")
        
        test_paper = self.prepare_test_data()
        
        for i in range(iterations):
            paper = test_paper.copy()
            paper['id'] = i + 1
            paper['title'] = f"{test_paper['title']} - Test {i}"
            try:
                benchmark_verification(paper)
            except Exception as e:
                logger.warning(f"  Verification failed: {e}")
    
    def benchmark_pdf_extraction(self, test_pdf_path: str = None, iterations: int = 10):
        """Benchmark PDF extraction."""
        if extract_paper_metadata is None:
            logger.warning("  PDF extraction module not available, skipping benchmark")
            return
            
        logger.info(f"Benchmarking PDF extraction ({iterations} iterations)...")
        
        # Try to find a test PDF file
        if test_pdf_path and Path(test_pdf_path).exists():
            for i in range(iterations):
                try:
                    benchmark_pdf_extraction(test_pdf_path)
                except Exception as e:
                    logger.warning(f"  PDF extraction failed: {e}")
        else:
            logger.warning("  No test PDF file provided, skipping PDF extraction benchmark")
    
    def run_all_benchmarks(self, iterations: Dict[str, int] = None):
        """Run all benchmarks."""
        if iterations is None:
            iterations = {
                'database': 50,
                'search': 30,
                'verification': 20,
                'pdf_extraction': 10
            }
        
        logger.info("=" * 60)
        logger.info("Starting Performance Benchmark Suite")
        logger.info("=" * 60)
        
        self.timer.clear()
        
        try:
            # Run benchmarks
            self.benchmark_database_operations(iterations.get('database', 50))
            self.benchmark_search_operations(iterations.get('search', 30))
            self.benchmark_verification(iterations.get('verification', 20))
            # PDF extraction requires actual PDF files, so it's optional
            
            logger.info("=" * 60)
            logger.info("Benchmark Suite Complete")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error during benchmarking: {e}")
            raise
    
    def save_results(self, output_file: str = "performance_results.csv"):
        """Save benchmark results to CSV file."""
        logger.info(f"Saving results to {output_file}...")
        
        stats = self.timer.get_all_statistics()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Function',
                'Iterations',
                'Avg Time (ms)',
                'Min Time (ms)',
                'Max Time (ms)',
                'Std Dev (ms)'
            ])
            
            for function_name, stat in sorted(stats.items()):
                writer.writerow([
                    function_name,
                    int(stat['count']),
                    f"{stat['avg']:.3f}",
                    f"{stat['min']:.3f}",
                    f"{stat['max']:.3f}",
                    f"{stat['std_dev']:.3f}"
                ])
        
        logger.info(f"Results saved to {output_file}")
        return stats


def generate_report():
    """Generate the performance report from results."""
    try:
        from generate_performance_report import generate_report
        generate_report()
        logger.info("Performance report generated successfully")
    except Exception as e:
        logger.warning(f"Could not generate report: {e}")


def main():
    """Main function to run performance analysis."""
    print("VTU Performance Analysis - Research Paper Management System")
    print("=" * 60)
    
    benchmark = PerformanceBenchmark()
    
    # Run benchmarks with specified iterations
    iterations = {
        'database': 50,      # Database operations
        'search': 30,        # Search operations
        'verification': 20,  # Verification operations
        'pdf_extraction': 10 # PDF extraction (optional)
    }
    
    try:
        benchmark.run_all_benchmarks(iterations)
        stats = benchmark.save_results("performance_results.csv")
        
        # Print summary
        print("\n" + "=" * 60)
        print("Performance Summary")
        print("=" * 60)
        print(f"{'Function':<30} {'Avg (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12}")
        print("-" * 60)
        
        for name, stat in sorted(stats.items()):
            print(f"{name:<30} {stat['avg']:>10.3f}   {stat['min']:>10.3f}   {stat['max']:>10.3f}")
        
        print("=" * 60)
        print("Results saved to performance_results.csv")
        
        # Generate report
        print("\nGenerating performance report...")
        generate_report()
        print("Report generated: vtu_performance_report.md")
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

