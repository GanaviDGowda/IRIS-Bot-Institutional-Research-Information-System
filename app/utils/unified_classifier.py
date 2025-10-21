"""
Unified Classification System for Research Papers

This module provides a consistent, logical system for classifying research papers
based on their journal, publisher, and other metadata. It determines:
1. Indexing Status (SCI, Scopus, Both, Conference, Preprint, Open Access, Unknown)
2. Quartile Ranking (Q1, Q2, Q3, Q4, N/A)
3. Impact Factor (High, Medium, Low, N/A)

The system uses a hierarchical approach where indexing status determines the base
classification, and quartile/impact are derived from that.
"""

from typing import Dict, Any, Tuple, List
import logging
from .quartile_fetcher import QuartileFetcher

logger = logging.getLogger(__name__)

class UnifiedPaperClassifier:
    """
    Unified classifier for research papers that provides consistent
    indexing status, quartile, and impact factor assignments.
    """
    
    def __init__(self):
        """Initialize the classifier with predefined journal databases."""
        self._initialize_journal_databases()
        self.quartile_fetcher = QuartileFetcher()
    
    def _initialize_journal_databases(self):
        """Initialize comprehensive journal databases for classification."""
        
        # Tier 1: SCI + Scopus (Highest Impact) - Q1
        self.tier1_journals = {
            'nature', 'science', 'cell', 'lancet', 'nejm', 'jama',
            'ieee transactions on', 'acm computing', 'physical review letters',
            'journal of machine learning research', 'neural information processing systems',
            'nucleic acids research', 'genome research', 'bioinformatics',
            'journal of the american chemical society', 'angewandte chemie',
            'advanced materials', 'nature materials', 'nature nanotechnology',
            'proceedings of the national academy of sciences', 'plos biology',
            'cell metabolism', 'molecular cell', 'developmental cell',
            'cancer cell', 'immunity', 'neuron', 'current biology',
            'nature medicine', 'nature genetics', 'nature biotechnology',
            'science advances', 'nature communications', 'cell reports'
        }
        
        # SCI (Science Citation Index) journals
        self.sci_journals = {
            'nature', 'science', 'cell', 'lancet', 'nejm', 'jama',
            'ieee transactions', 'acm computing', 'physical review letters',
            'journal of machine learning research', 'neural information processing systems',
            'nucleic acids research', 'genome research', 'bioinformatics',
            'journal of the american chemical society', 'angewandte chemie',
            'advanced materials', 'nature materials', 'nature nanotechnology',
            'proceedings of the national academy of sciences', 'plos biology',
            'cell metabolism', 'molecular cell', 'developmental cell',
            'cancer cell', 'immunity', 'neuron', 'current biology',
            'nature medicine', 'nature genetics', 'nature biotechnology',
            'science advances', 'nature communications', 'cell reports',
            'physical review', 'journal of the american chemical society',
            'angewandte chemie', 'advanced materials', 'nature materials'
        }
        
        # ESCI (Emerging Sources Citation Index) journals
        self.esci_journals = {
            'frontiers in', 'plos one', 'scientific reports', 'applied sciences',
            'materials', 'sensors', 'molecules', 'polymers', 'catalysts',
            'energies', 'sustainability', 'water', 'atmosphere', 'forests',
            'agronomy', 'plants', 'animals', 'microorganisms', 'viruses',
            'pathogens', 'toxins', 'marine drugs', 'pharmaceuticals',
            'medicines', 'vaccines', 'antibiotics', 'antioxidants',
            'nutrients', 'foods', 'beverages', 'fermentation',
            'processes', 'systems', 'algorithms', 'mathematics',
            'statistics', 'probability', 'engineering', 'technology',
            'innovation', 'research', 'studies', 'international journal',
            'journal of', 'european journal', 'asian journal', 'american journal'
        }
        
        # DOAJ (Directory of Open Access Journals) patterns
        self.doaj_journals = {
            'plos', 'frontiers', 'bmc', 'hindawi', 'mdpi', 'cogent',
            'f1000research', 'peerj', 'scientific reports', 'nature communications',
            'open access', 'open science', 'public library of science',
            'biomed central', 'springer open', 'wiley open access',
            'elsevier open access', 'taylor francis open', 'sage open',
            'emerald open research', 'ieee open access', 'acm open'
        }
        
        # EI (Engineering Index) journals
        self.ei_journals = {
            'ieee', 'acm', 'springer', 'elsevier', 'wiley', 'taylor',
            'engineering', 'technology', 'computer', 'software', 'hardware',
            'electrical', 'electronic', 'mechanical', 'civil', 'chemical',
            'materials', 'manufacturing', 'automation', 'robotics',
            'artificial intelligence', 'machine learning', 'data science',
            'cybersecurity', 'networks', 'communications', 'signal processing',
            'control systems', 'optimization', 'algorithms', 'computing',
            'information technology', 'computer science', 'engineering science',
            'applied mathematics', 'statistics', 'operations research'
        }
        
        # PubMed journals (Medical/Biological)
        self.pubmed_journals = {
            'new england journal of medicine', 'lancet', 'jama', 'bmj',
            'nature medicine', 'cell', 'science', 'nature', 'cell metabolism',
            'molecular cell', 'developmental cell', 'cancer cell', 'immunity',
            'neuron', 'current biology', 'plos medicine', 'plos biology',
            'plos one', 'scientific reports', 'nature communications',
            'cell reports', 'molecular therapy', 'cancer research',
            'journal of clinical investigation', 'blood', 'circulation',
            'journal of the american medical association', 'annals of internal medicine',
            'archives of internal medicine', 'mayo clinic proceedings',
            'cleveland clinic journal of medicine', 'johns hopkins medical journal'
        }
        
        # UGC CARE (University Grants Commission) journals
        self.ugc_care_journals = {
            'indian journal', 'journal of indian', 'indian academy',
            'national academy', 'indian institute', 'indian university',
            'indian statistical institute', 'tata institute', 'iisc',
            'iit', 'nit', 'iim', 'indian institute of science',
            'indian institute of technology', 'national institute of technology',
            'indian institute of management', 'all india institute of medical sciences',
            'post graduate institute', 'sri sathya sai institute',
            'indian council of medical research', 'council of scientific',
            'indian national science academy', 'indian academy of sciences',
            'indian academy of engineering', 'indian academy of management'
        }
        
        # Google Scholar indexed (Broader coverage)
        self.google_scholar_journals = {
            'arxiv', 'researchgate', 'academia', 'ssrn', 'zenodo',
            'figshare', 'mendeley', 'zotero', 'endnote', 'refworks',
            'scholar', 'academic', 'university', 'institute', 'college',
            'research', 'studies', 'journal', 'proceedings', 'conference',
            'workshop', 'symposium', 'international', 'national', 'regional',
            'local', 'department', 'faculty', 'school', 'division'
        }
        
        # Tier 2: Scopus Only (High Impact) - Q2
        self.tier2_journals = {
            'elsevier', 'wiley', 'springer', 'taylor', 'sage', 'emerald',
            'plos one', 'scientific reports', 'applied physics letters',
            'journal of applied physics', 'materials science', 'chemistry of materials',
            'journal of materials chemistry', 'biomaterials', 'journal of biomedical materials research',
            'oxford university press', 'cambridge university press', 'mit press',
            'harvard university press', 'stanford university press', 'academic press',
            'elsevier science', 'wiley-blackwell', 'springer nature',
            'frontiers in', 'bmc', 'hindawi', 'mdpi'
        }
        
        # Tier 3: Conference Proceedings (Medium Impact) - Q3
        self.tier3_journals = {
            'conference', 'proceedings', 'workshop', 'symposium', 'international conference',
            'ieee conference', 'acm conference', 'international workshop',
            'annual meeting', 'symposium on', 'conference on', 'workshop on',
            'international symposium', 'conference proceedings', 'workshop proceedings'
        }
        
        # Tier 4: Preprint/ArXiv (Lower Impact) - Q4
        self.tier4_journals = {
            'arxiv', 'biorxiv', 'medrxiv', 'chemrxiv', 'preprint', 'preprints',
            'research square', 'ssrn', 'zenodo', 'figshare'
        }
        
        # Open Access Journals (Special Category)
        self.oa_journals = {
            'plos', 'frontiers', 'bmc', 'hindawi', 'mdpi', 'cogent',
            'f1000research', 'peerj', 'scientific reports', 'nature communications'
        }
        
        # Publisher patterns for additional classification
        self.tier1_publishers = {
            'nature publishing', 'cell press', 'elsevier', 'wiley', 'springer',
            'ieee', 'acm', 'oxford university press', 'cambridge university press'
        }
        
        self.tier2_publishers = {
            'taylor', 'sage', 'emerald', 'inderscience', 'igi global',
            'world scientific', 'de gruyter', 'brill', 'karger'
        }
    
    def classify_paper(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Classify a research paper and return indexing status, quartile, and impact factor.
        
        Args:
            metadata: Dictionary containing paper metadata (journal, publisher, etc.)
            
        Returns:
            Dictionary with 'indexing_status', 'quartile', 'impact_factor', and 'confidence'
        """
        journal = (metadata.get('journal', '') or '').lower().strip()
        publisher = (metadata.get('publisher', '') or '').lower().strip()
        issn = (metadata.get('issn', '') or '').strip()
        
        # Determine classification
        classification = self._determine_classification(journal, publisher, issn)
        
        # Convert impact factor to numeric value
        impact_factor = self._convert_impact_factor_to_numeric(classification['impact_factor'])
        
        return {
            'indexing_status': classification['indexing_status'],
            'quartile': classification['quartile'],
            'impact_factor': impact_factor,
            'confidence': classification['confidence']
        }
    
    def _determine_classification(self, journal: str, publisher: str, issn: str) -> Dict[str, str]:
        """Determine the classification based on journal and publisher information."""
        
        # Determine all applicable indexing databases
        indexing_databases = self._get_indexing_databases(journal, publisher)
        
        # Determine quartile and impact factor based on indexing
        quartile, impact_factor, confidence = self._determine_quartile_and_impact(
            journal, publisher, indexing_databases
        )
        
        # Format indexing status
        indexing_status = self._format_indexing_status(indexing_databases)
        
        return {
            'indexing_status': indexing_status,
            'quartile': quartile,
            'impact_factor': impact_factor,
            'confidence': confidence
        }
    
    def _get_indexing_databases(self, journal: str, publisher: str) -> List[str]:
        """Determine which indexing databases the journal belongs to."""
        databases = []
        
        # Check SCI
        if self._matches_sci(journal, publisher):
            databases.append('SCI')
        
        # Check Scopus
        if self._matches_scopus(journal, publisher):
            databases.append('Scopus')
        
        # Check ESCI
        if self._matches_esci(journal, publisher):
            databases.append('ESCI')
        
        # Check DOAJ
        if self._matches_doaj(journal, publisher):
            databases.append('DOAJ')
        
        # Check EI
        if self._matches_ei(journal, publisher):
            databases.append('EI')
        
        # Check PubMed
        if self._matches_pubmed(journal, publisher):
            databases.append('PubMed')
        
        # Check UGC CARE
        if self._matches_ugc_care(journal, publisher):
            databases.append('UGC CARE')
        
        # Check Google Scholar
        if self._matches_google_scholar(journal, publisher):
            databases.append('Google Scholar')
        
        # Check for conference proceedings
        if self._matches_conference(journal, publisher):
            databases.append('Conference')
        
        # Check for preprint servers
        if self._matches_preprint(journal, publisher):
            databases.append('Preprint')
        
        return databases
    
    def _determine_quartile_and_impact(self, journal: str, publisher: str, databases: List[str]) -> Tuple[str, str, str]:
        """Determine quartile and impact factor based on indexing databases."""
        
        # Only assign quartiles to SCI and Scopus indexed journals
        if 'SCI' in databases or 'Scopus' in databases:
            # Fetch actual quartile data from authorized sources
            quartile_data = self.quartile_fetcher.fetch_quartile_data(journal, publisher)
            
            if quartile_data.success and quartile_data.quartile != "N/A":
                # Convert quartile to impact level
                if quartile_data.quartile == "Q1":
                    impact_level = "High"
                elif quartile_data.quartile == "Q2":
                    impact_level = "Medium"
                elif quartile_data.quartile == "Q3":
                    impact_level = "Low"
                else:
                    impact_level = "N/A"
                
                return quartile_data.quartile, impact_level, 'High'
            else:
                # Fallback to basic classification for SCI/Scopus journals
                if 'SCI' in databases and 'Scopus' in databases:
                    return 'Q1', 'High', 'High'
                elif 'SCI' in databases:
                    return 'Q1', 'High', 'High'
                elif 'Scopus' in databases:
                    return 'Q2', 'Medium', 'High'
        
        # For non-SCI/Scopus journals, determine impact level but no quartile
        if 'ESCI' in databases and 'DOAJ' in databases:
            return 'N/A', 'Medium', 'High'
        elif 'ESCI' in databases:
            return 'N/A', 'Medium', 'High'
        elif 'DOAJ' in databases and 'PubMed' in databases:
            return 'N/A', 'Medium', 'High'
        elif 'DOAJ' in databases:
            return 'N/A', 'Medium', 'High'
        elif 'EI' in databases and 'Google Scholar' in databases:
            return 'N/A', 'Medium', 'High'
        elif 'PubMed' in databases:
            return 'N/A', 'Medium', 'High'
        elif 'UGC CARE' in databases and 'Google Scholar' in databases:
            return 'N/A', 'Medium', 'High'
        elif 'Conference' in databases:
            return 'N/A', 'Low', 'High'
        elif 'Google Scholar' in databases and len(databases) == 1:
            return 'N/A', 'Low', 'Medium'
        elif 'Preprint' in databases:
            return 'N/A', 'N/A', 'High'
        
        # Default: Unknown (N/A, N/A Impact)
        return 'N/A', 'N/A', 'Low'
    
    def _format_indexing_status(self, databases: List[str]) -> str:
        """Format the indexing status string based on databases."""
        if not databases:
            return 'Unknown'
        
        # Remove duplicates and sort for consistent output
        unique_databases = sorted(list(set(databases)))
        
        # Special cases for common combinations
        if 'SCI' in unique_databases and 'Scopus' in unique_databases:
            return 'SCI + Scopus'
        elif 'SCI' in unique_databases:
            return 'SCI'
        elif 'Scopus' in unique_databases and 'ESCI' in unique_databases:
            return 'Scopus + ESCI'
        elif 'Scopus' in unique_databases:
            return 'Scopus'
        elif 'ESCI' in unique_databases and 'DOAJ' in unique_databases:
            return 'ESCI + DOAJ'
        elif 'ESCI' in unique_databases:
            return 'ESCI'
        elif 'DOAJ' in unique_databases and 'PubMed' in unique_databases:
            return 'DOAJ + PubMed'
        elif 'DOAJ' in unique_databases:
            return 'DOAJ'
        elif 'EI' in unique_databases and 'Google Scholar' in unique_databases:
            return 'EI + Google Scholar'
        elif 'EI' in unique_databases:
            return 'EI'
        elif 'PubMed' in unique_databases:
            return 'PubMed'
        elif 'UGC CARE' in unique_databases and 'Google Scholar' in unique_databases:
            return 'UGC CARE + Google Scholar'
        elif 'UGC CARE' in unique_databases:
            return 'UGC CARE'
        elif 'Conference' in unique_databases:
            return 'Conference Proceedings'
        elif 'Preprint' in unique_databases:
            return 'Preprint'
        elif 'Google Scholar' in unique_databases:
            return 'Google Scholar'
        else:
            return ' + '.join(unique_databases)
    
    def _matches_tier1(self, journal: str, publisher: str) -> bool:
        """Check if journal matches Tier 1 (SCI + Scopus, Q1) criteria."""
        # Check journal name
        if any(keyword in journal for keyword in self.tier1_journals):
            return True
        
        # Check publisher
        if any(keyword in publisher for keyword in self.tier1_publishers):
            return True
        
        return False
    
    def _matches_tier2(self, journal: str, publisher: str) -> bool:
        """Check if journal matches Tier 2 (Scopus, Q2) criteria."""
        # Check journal name
        if any(keyword in journal for keyword in self.tier2_journals):
            return True
        
        # Check publisher
        if any(keyword in publisher for keyword in self.tier2_publishers):
            return True
        
        return False
    
    def _matches_tier3(self, journal: str, publisher: str) -> bool:
        """Check if journal matches Tier 3 (Conference, Q3) criteria."""
        return any(keyword in journal for keyword in self.tier3_journals)
    
    def _matches_tier4(self, journal: str, publisher: str) -> bool:
        """Check if journal matches Tier 4 (Preprint, Q4) criteria."""
        return any(keyword in journal for keyword in self.tier4_journals)
    
    def _matches_oa(self, journal: str, publisher: str) -> bool:
        """Check if journal matches Open Access criteria."""
        return any(keyword in journal for keyword in self.oa_journals)
    
    def _matches_sci(self, journal: str, publisher: str) -> bool:
        """Check if journal matches SCI criteria."""
        return any(keyword in journal for keyword in self.sci_journals)
    
    def _matches_scopus(self, journal: str, publisher: str) -> bool:
        """Check if journal matches Scopus criteria."""
        return any(keyword in journal for keyword in self.tier2_journals) or any(keyword in publisher for keyword in self.tier2_publishers)
    
    def _matches_esci(self, journal: str, publisher: str) -> bool:
        """Check if journal matches ESCI criteria."""
        return any(keyword in journal for keyword in self.esci_journals)
    
    def _matches_doaj(self, journal: str, publisher: str) -> bool:
        """Check if journal matches DOAJ criteria."""
        return any(keyword in journal for keyword in self.doaj_journals)
    
    def _matches_ei(self, journal: str, publisher: str) -> bool:
        """Check if journal matches EI criteria."""
        return any(keyword in journal for keyword in self.ei_journals)
    
    def _matches_pubmed(self, journal: str, publisher: str) -> bool:
        """Check if journal matches PubMed criteria."""
        return any(keyword in journal for keyword in self.pubmed_journals)
    
    def _matches_ugc_care(self, journal: str, publisher: str) -> bool:
        """Check if journal matches UGC CARE criteria."""
        return any(keyword in journal for keyword in self.ugc_care_journals)
    
    def _matches_google_scholar(self, journal: str, publisher: str) -> bool:
        """Check if journal matches Google Scholar criteria."""
        return any(keyword in journal for keyword in self.google_scholar_journals)
    
    def _matches_conference(self, journal: str, publisher: str) -> bool:
        """Check if journal matches conference criteria."""
        return any(keyword in journal for keyword in self.tier3_journals)
    
    def _matches_preprint(self, journal: str, publisher: str) -> bool:
        """Check if journal matches preprint criteria."""
        return any(keyword in journal for keyword in self.tier4_journals)
    
    def _matches_sci_only(self, journal: str, publisher: str) -> bool:
        """Check if journal matches SCI-only criteria (specific high-impact journals)."""
        sci_only_keywords = {
            'physical review', 'journal of the american chemical society',
            'angewandte chemie', 'advanced materials', 'nature materials'
        }
        return any(keyword in journal for keyword in sci_only_keywords)
    
    def _convert_impact_factor_to_numeric(self, impact_level: str) -> float:
        """Convert impact factor level to numeric value."""
        impact_mapping = {
            'High': 15.0,
            'Medium': 4.0,
            'Low': 1.5,
            'N/A': 0.5
        }
        return impact_mapping.get(impact_level, 0.5)
    
    def get_classification_summary(self) -> Dict[str, int]:
        """Get a summary of the classification system."""
        return {
            'sci_journals': len(self.sci_journals),
            'esci_journals': len(self.esci_journals),
            'doaj_journals': len(self.doaj_journals),
            'ei_journals': len(self.ei_journals),
            'pubmed_journals': len(self.pubmed_journals),
            'ugc_care_journals': len(self.ugc_care_journals),
            'google_scholar_journals': len(self.google_scholar_journals),
            'tier1_journals': len(self.tier1_journals),
            'tier2_journals': len(self.tier2_journals),
            'tier3_journals': len(self.tier3_journals),
            'tier4_journals': len(self.tier4_journals),
            'oa_journals': len(self.oa_journals),
            'tier1_publishers': len(self.tier1_publishers),
            'tier2_publishers': len(self.tier2_publishers)
        }
