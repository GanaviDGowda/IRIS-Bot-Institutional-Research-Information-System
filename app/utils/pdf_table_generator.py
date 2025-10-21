"""
PDF Table Generator for Research Paper Browser
Generates PDF reports of table data with proper formatting.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    # Define dummy classes for type hints when reportlab is not available
    TableStyle = None

logger = logging.getLogger(__name__)


class PDFTableGenerator:
    """Generate PDF reports from table data."""
    
    def __init__(self):
        if not HAS_REPORTLAB:
            raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Header style
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            alignment=TA_CENTER
        )
        
        # Data style (left-aligned)
        self.data_style = ParagraphStyle(
            'CustomData',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            alignment=TA_LEFT
        )

        # Center-aligned data style
        self.data_style_center = ParagraphStyle(
            'CustomDataCenter',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            alignment=TA_CENTER
        )
        
        # Footer style
        self.footer_style = ParagraphStyle(
            'CustomFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Oblique',
            textColor=colors.grey,
            alignment=TA_CENTER
        )
    
    def generate_paper_table_pdf(self, papers: List[Dict[str, Any]], 
                                output_path: str, 
                                title: str = "Research Papers Report",
                                include_filters: Optional[Dict] = None,
                                selected_columns: Optional[List[List[str]]] = None,
                                author_mode: str = "all") -> bool:
        """
        Generate PDF report of papers table.
        
        Args:
            papers: List of paper dictionaries
            output_path: Path to save the PDF file
            title: Title for the PDF report
            include_filters: Optional filters applied to the data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use landscape orientation for better table display
            from reportlab.lib.pagesizes import landscape
            doc = SimpleDocTemplate(output_path, pagesize=landscape(A4))
            story = []
            
            # Add title
            story.append(Paragraph(title, self.title_style))
            story.append(Spacer(1, 12))
            
            # Add generation info
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            info_text = f"Generated on: {current_time} | Total Papers: {len(papers)}"
            if include_filters:
                filter_text = " | Filters: " + ", ".join([f"{k}={v}" for k, v in include_filters.items() if v])
                info_text += filter_text
            story.append(Paragraph(info_text, self.footer_style))
            story.append(Spacer(1, 20))
            
            if not papers:
                story.append(Paragraph("No papers found.", self.data_style))
            else:
                # Create table data
                table_data = self._prepare_table_data(papers, selected_columns, author_mode)
                
                # Create table with proper column widths
                table = Table(table_data, repeatRows=1)
                header_row = table_data[0] if table_data else []
                table.setStyle(self._get_table_style(header_row))
                
                # Set column widths for better layout
                col_widths = self._calculate_column_widths(table_data[0] if table_data else [])
                table._argW = col_widths

                # Reduce cell padding for tighter layout
                table.setStyle(TableStyle([
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                
                story.append(table)
            
            # Add footer
            story.append(Spacer(1, 20))
            story.append(Paragraph("Generated by Research Paper Browser", self.footer_style))
            
            # Build PDF
            doc.build(story)
            logger.info(f"PDF report generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return False
    
    def _prepare_table_data(self, papers: List[Dict[str, Any]], selected_columns: Optional[List[List[str]]], author_mode: str) -> List[List[Any]]:
        """Prepare table data for PDF generation."""
        if not papers:
            return []
        
        # If caller specified columns, use them, else default set
        if selected_columns:
            # Expect list of [header, key]
            columns = [(c[0], c[1]) for c in selected_columns if len(c) >= 2]
        else:
            columns = [
                ("Title", "title"),
                ("Authors", "authors"),
                ("Year", "year"),
                ("Journal", "journal"),
                ("Department", "department"),
                ("Research Domain", "research_domain"),
                ("Indexing", "indexing_status"),
                ("Citations", "citation_count")
            ]
        
        # Create header row
        table_data = [[Paragraph(col[0], self.header_style) for col in columns]]
        
        # Add data rows
        for paper in papers:
            row = []
            for _, key in columns:
                value = paper.get(key, "")
                # Authors mode: keep only first author if requested
                if key == "authors" and value:
                    if author_mode == "first":
                        # Split on common separators and take first
                        for sep in [';', ',', ' and ']:
                            if sep in value:
                                value = value.split(sep)[0].strip()
                                break
                if value is None:
                    value = ""
                elif isinstance(value, bool):
                    value = "Yes" if value else "No"
                elif isinstance(value, (int, float)):
                    value = str(value)
                else:
                    value = str(value)
                
                # Wrap long text using Paragraphs for automatic line wrapping
                row.append(Paragraph(value, self.data_style))
            table_data.append(row)
        
        return table_data
    
    def _calculate_column_widths(self, header_row: List[str]) -> List[float]:
        """Calculate optimal column widths for the table based on headers."""
        num_columns = len(header_row)
        if num_columns == 0:
            return []
        
        # Total available width in landscape A4 (approximately 10.5 inches)
        total_width = 10.5 * 72  # Convert to points
        
        # Define relative widths (increase Title breadth, reduce height need)
        column_widths = {
            "Title": 4.0,            # 38% - Wider title
            "Authors": 1.6,          # 15%
            "Year": 0.5,             # 5%
            "Journal": 1.2,          # 11%
            "Department": 0.8,       # 8%
            "Research Domain": 1.2,  # 11%
            "Indexing": 0.4,         # 4%
            "Citations": 0.3,        # 3%
            "Quartile": 0.4,         # 4%
            "Verification": 0.6      # 5%
        }
        
        # Calculate actual widths
        widths = []
        for header in header_row:
            # header may be a Paragraph; extract text
            header_text = header.getPlainText() if hasattr(header, 'getPlainText') else str(header)
            relative_width = column_widths.get(header_text, 0.8)
            actual_width = total_width * relative_width / 12.0
            widths.append(actual_width)
        
        return widths
    
    def _get_table_style(self, header_row: List[Any]):
        """Get table styling; center-align specific columns and apply alternating rows."""
        # Map headers to indexes
        header_texts = [h.getPlainText() if hasattr(h, 'getPlainText') else str(h) for h in header_row]
        def idx_of(name: str) -> Optional[int]:
            try:
                return header_texts.index(name)
            except ValueError:
                return None

        year_idx = idx_of("Year")
        indexing_idx = idx_of("Indexing")
        quartile_idx = idx_of("Quartile")

        style = [
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]

        # Default all data columns LEFT
        style.append(('ALIGN', (0, 1), (-1, -1), 'LEFT'))
        # Override specific columns to CENTER if present
        for col_idx in [year_idx, indexing_idx, quartile_idx]:
            if col_idx is not None:
                style.append(('ALIGN', (col_idx, 1), (col_idx, -1), 'CENTER'))

        return TableStyle(style)
    
    def generate_summary_pdf(self, papers: List[Dict[str, Any]], 
                           output_path: str,
                           title: str = "Research Papers Summary") -> bool:
        """
        Generate a summary PDF with statistics and charts.
        
        Args:
            papers: List of paper dictionaries
            output_path: Path to save the PDF file
            title: Title for the PDF report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # Add title
            story.append(Paragraph(title, self.title_style))
            story.append(Spacer(1, 12))
            
            # Add generation info
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            story.append(Paragraph(f"Generated on: {current_time}", self.footer_style))
            story.append(Spacer(1, 20))
            
            if not papers:
                story.append(Paragraph("No papers found.", self.data_style))
            else:
                # Generate statistics
                stats = self._calculate_statistics(papers)
                
                # Add statistics table
                story.append(Paragraph("Summary Statistics", self.styles['Heading2']))
                story.append(Spacer(1, 12))
                
                stats_data = [
                    ["Metric", "Value"],
                    ["Total Papers", str(len(papers))],
                    ["Verified Papers", str(stats.get('verified_count', 0))],
                    ["Student Papers", str(stats.get('student_count', 0))],
                    ["Average Year", f"{stats.get('avg_year', 0):.1f}"],
                    ["Departments", str(stats.get('department_count', 0))],
                    ["Research Domains", str(stats.get('domain_count', 0))],
                    ["Total Citations", str(stats.get('total_citations', 0))],
                ]
                
                stats_table = Table(stats_data)
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                story.append(stats_table)
                story.append(Spacer(1, 20))
                
                # Add department breakdown
                if stats.get('department_breakdown'):
                    story.append(Paragraph("Department Breakdown", self.styles['Heading2']))
                    story.append(Spacer(1, 12))
                    
                    dept_data = [["Department", "Count"]]
                    for dept, count in stats['department_breakdown'].items():
                        dept_data.append([dept, str(count)])
                    
                    dept_table = Table(dept_data)
                    dept_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))
                    
                    story.append(dept_table)
            
            # Add footer
            story.append(Spacer(1, 20))
            story.append(Paragraph("Generated by Research Paper Browser", self.footer_style))
            
            # Build PDF
            doc.build(story)
            logger.info(f"Summary PDF report generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating summary PDF: {e}")
            return False
    
    def _calculate_statistics(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics from papers data."""
        if not papers:
            return {}
        
        stats = {
            'verified_count': 0,
            'student_count': 0,
            'total_citations': 0,
            'years': [],
            'departments': set(),
            'domains': set(),
            'department_breakdown': {}
        }
        
        for paper in papers:
            # Count verified papers
            if paper.get('review_status') == 'verified':
                stats['verified_count'] += 1
            
            # Count student papers
            if paper.get('student'):
                stats['student_count'] += 1
            
            # Sum citations
            citations = paper.get('citation_count', 0)
            if isinstance(citations, (int, float)):
                stats['total_citations'] += citations
            
            # Collect years
            year = paper.get('year')
            if year and isinstance(year, (int, float)):
                stats['years'].append(year)
            
            # Collect departments
            dept = paper.get('department')
            if dept:
                stats['departments'].add(dept)
                stats['department_breakdown'][dept] = stats['department_breakdown'].get(dept, 0) + 1
            
            # Collect domains
            domain = paper.get('research_domain')
            if domain:
                stats['domains'].add(domain)
        
        # Calculate averages
        if stats['years']:
            stats['avg_year'] = sum(stats['years']) / len(stats['years'])
        else:
            stats['avg_year'] = 0
        
        stats['department_count'] = len(stats['departments'])
        stats['domain_count'] = len(stats['domains'])
        
        return stats


def generate_paper_table_pdf(papers: List[Dict[str, Any]], 
                           output_path: str, 
                           title: str = "Research Papers Report",
                           include_filters: Optional[Dict] = None,
                           selected_columns: Optional[List[List[str]]] = None,
                           author_mode: str = "all") -> bool:
    """Convenience function to generate PDF table report."""
    try:
        generator = PDFTableGenerator()
        return generator.generate_paper_table_pdf(
            papers, output_path, title, include_filters, selected_columns, author_mode
        )
    except ImportError:
        logger.error("reportlab is required for PDF generation. Install with: pip install reportlab")
        return False
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return False


def generate_summary_pdf(papers: List[Dict[str, Any]], 
                        output_path: str,
                        title: str = "Research Papers Summary") -> bool:
    """Convenience function to generate PDF summary report."""
    try:
        generator = PDFTableGenerator()
        return generator.generate_summary_pdf(papers, output_path, title)
    except ImportError:
        logger.error("reportlab is required for PDF generation. Install with: pip install reportlab")
        return False
    except Exception as e:
        logger.error(f"Error generating summary PDF: {e}")
        return False
