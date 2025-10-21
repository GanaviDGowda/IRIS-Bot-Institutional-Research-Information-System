"""
Department Manager
Manages predefined engineering departments and allows custom department addition.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DepartmentInfo:
    """Information about a department."""
    name: str
    code: str
    category: str
    description: str


class DepartmentManager:
    """Manages engineering departments with predefined options and custom additions."""
    
    def __init__(self):
        """Initialize with predefined engineering departments."""
        self.departments = self._load_predefined_departments()
        self.custom_departments = []  # For user-added departments
    
    def _load_predefined_departments(self) -> List[DepartmentInfo]:
        """Load predefined engineering departments."""
        return [
            DepartmentInfo(
                name="Civil Engineering",
                code="CE",
                category="Engineering",
                description="Infrastructure, construction, and structural engineering"
            ),
            DepartmentInfo(
                name="Mechanical Engineering", 
                code="ME",
                category="Engineering",
                description="Mechanical systems, thermodynamics, and manufacturing"
            ),
            DepartmentInfo(
                name="Electrical & Electronics Engineering",
                code="EEE", 
                category="Engineering",
                description="Electrical systems, power, and electronics"
            ),
            DepartmentInfo(
                name="Electronics & Communication Engineering",
                code="ECE",
                category="Engineering", 
                description="Electronics, telecommunications, and signal processing"
            ),
            DepartmentInfo(
                name="Computer Science & Engineering",
                code="CSE",
                category="Engineering",
                description="Computer science, software engineering, and algorithms"
            ),
            DepartmentInfo(
                name="Electronics & Instrumentation Engineering",
                code="EIE",
                category="Engineering",
                description="Electronics, instrumentation, and control systems"
            ),
            DepartmentInfo(
                name="Information Science & Engineering",
                code="ISE",
                category="Engineering",
                description="Information systems, databases, and software development"
            ),
            DepartmentInfo(
                name="Artificial Intelligence & Machine Learning",
                code="AIML",
                category="Engineering",
                description="AI, machine learning, deep learning, and data science"
            ),
            # Additional common departments
            DepartmentInfo(
                name="Chemical Engineering",
                code="CHE",
                category="Engineering",
                description="Chemical processes, materials, and industrial chemistry"
            ),
            DepartmentInfo(
                name="Aerospace Engineering",
                code="AE",
                category="Engineering", 
                description="Aircraft, spacecraft, and aerodynamics"
            ),
            DepartmentInfo(
                name="Biomedical Engineering",
                code="BME",
                category="Engineering",
                description="Medical devices, healthcare technology, and bioengineering"
            ),
            DepartmentInfo(
                name="Environmental Engineering",
                code="ENV",
                category="Engineering",
                description="Environmental systems, sustainability, and pollution control"
            ),
            DepartmentInfo(
                name="Industrial Engineering",
                code="IE",
                category="Engineering",
                description="Operations research, manufacturing, and systems optimization"
            ),
            DepartmentInfo(
                name="Materials Science & Engineering",
                code="MSE",
                category="Engineering",
                description="Materials properties, nanotechnology, and advanced materials"
            ),
            DepartmentInfo(
                name="Mining Engineering",
                code="MIN",
                category="Engineering",
                description="Mining operations, mineral processing, and geological engineering"
            ),
            DepartmentInfo(
                name="Petroleum Engineering",
                code="PE",
                category="Engineering",
                description="Oil and gas extraction, drilling, and reservoir engineering"
            ),
            DepartmentInfo(
                name="Textile Engineering",
                code="TE",
                category="Engineering",
                description="Textile manufacturing, fibers, and textile technology"
            ),
            DepartmentInfo(
                name="Agricultural Engineering",
                code="AGE",
                category="Engineering",
                description="Agricultural machinery, irrigation, and food processing"
            ),
            DepartmentInfo(
                name="Marine Engineering",
                code="MAR",
                category="Engineering",
                description="Ship design, marine systems, and ocean engineering"
            ),
            DepartmentInfo(
                name="Automotive Engineering",
                code="AUTO",
                category="Engineering",
                description="Vehicle design, automotive systems, and transportation"
            ),
            # Non-engineering departments
            DepartmentInfo(
                name="Mathematics",
                code="MATH",
                category="Science",
                description="Pure and applied mathematics, statistics, and operations research"
            ),
            DepartmentInfo(
                name="Physics",
                code="PHY",
                category="Science", 
                description="Theoretical and applied physics, quantum mechanics, and optics"
            ),
            DepartmentInfo(
                name="Chemistry",
                code="CHEM",
                category="Science",
                description="Organic, inorganic, physical chemistry, and materials chemistry"
            ),
            DepartmentInfo(
                name="Biology",
                code="BIO",
                category="Science",
                description="Molecular biology, genetics, ecology, and biotechnology"
            ),
            DepartmentInfo(
                name="Management Studies",
                code="MS",
                category="Management",
                description="Business administration, finance, marketing, and operations"
            ),
            DepartmentInfo(
                name="Architecture",
                code="ARCH",
                category="Design",
                description="Architectural design, urban planning, and building technology"
            ),
            DepartmentInfo(
                name="Pharmacy",
                code="PHARM",
                category="Health Sciences",
                description="Pharmaceutical sciences, drug development, and clinical pharmacy"
            ),
            DepartmentInfo(
                name="Other",
                code="OTHER",
                category="General",
                description="Other departments not listed above"
            )
        ]
    
    def get_all_departments(self) -> List[str]:
        """Get list of all department names."""
        all_departments = [dept.name for dept in self.departments]
        all_departments.extend([dept.name for dept in self.custom_departments])
        return sorted(all_departments)
    
    def get_predefined_departments(self) -> List[str]:
        """Get list of predefined department names only."""
        return [dept.name for dept in self.departments]
    
    def get_departments_by_category(self, category: str) -> List[str]:
        """Get departments by category."""
        departments = [dept.name for dept in self.departments if dept.category == category]
        departments.extend([dept.name for dept in self.custom_departments if dept.category == category])
        return sorted(departments)
    
    def get_categories(self) -> List[str]:
        """Get list of all categories."""
        categories = list(set(dept.category for dept in self.departments))
        categories.extend([dept.category for dept in self.custom_departments])
        return sorted(list(set(categories)))
    
    def get_department_info(self, department_name: str) -> Optional[DepartmentInfo]:
        """Get information about a specific department."""
        # Check predefined departments
        for dept in self.departments:
            if dept.name == department_name:
                return dept
        
        # Check custom departments
        for dept in self.custom_departments:
            if dept.name == department_name:
                return dept
        
        return None
    
    def validate_department(self, department_name: str) -> bool:
        """Check if a department name is valid."""
        return department_name in self.get_all_departments()
    
    def add_custom_department(self, name: str, code: str = "", category: str = "Custom", description: str = "") -> bool:
        """Add a custom department."""
        try:
            # Check if department already exists
            if self.validate_department(name):
                logger.warning(f"Department '{name}' already exists")
                return False
            
            # Create new department
            new_dept = DepartmentInfo(
                name=name,
                code=code or name[:3].upper(),
                category=category,
                description=description or f"Custom department: {name}"
            )
            
            self.custom_departments.append(new_dept)
            logger.info(f"Added custom department: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding custom department: {e}")
            return False
    
    def remove_custom_department(self, department_name: str) -> bool:
        """Remove a custom department (cannot remove predefined ones)."""
        try:
            for i, dept in enumerate(self.custom_departments):
                if dept.name == department_name:
                    del self.custom_departments[i]
                    logger.info(f"Removed custom department: {department_name}")
                    return True
            
            logger.warning(f"Custom department '{department_name}' not found")
            return False
            
        except Exception as e:
            logger.error(f"Error removing custom department: {e}")
            return False
    
    def get_department_code(self, department_name: str) -> str:
        """Get department code."""
        dept_info = self.get_department_info(department_name)
        return dept_info.code if dept_info else ""
    
    def get_department_category(self, department_name: str) -> str:
        """Get department category."""
        dept_info = self.get_department_info(department_name)
        return dept_info.category if dept_info else "Unknown"
    
    def get_department_description(self, department_name: str) -> str:
        """Get department description."""
        dept_info = self.get_department_info(department_name)
        return dept_info.description if dept_info else ""
    
    def search_departments(self, query: str) -> List[str]:
        """Search departments by name or code."""
        query_lower = query.lower()
        matching_departments = []
        
        for dept in self.departments + self.custom_departments:
            if (query_lower in dept.name.lower() or 
                query_lower in dept.code.lower() or
                query_lower in dept.description.lower()):
                matching_departments.append(dept.name)
        
        return sorted(matching_departments)
    
    def get_departments_for_dropdown(self) -> Dict[str, List[str]]:
        """Get departments organized for dropdown display."""
        result = {}
        
        for category in self.get_categories():
            result[category] = self.get_departments_by_category(category)
        
        return result
    
    def get_statistics(self) -> Dict:
        """Get department statistics."""
        return {
            "total_departments": len(self.get_all_departments()),
            "predefined_departments": len(self.departments),
            "custom_departments": len(self.custom_departments),
            "categories": len(self.get_categories()),
            "engineering_departments": len(self.get_departments_by_category("Engineering")),
            "science_departments": len(self.get_departments_by_category("Science")),
        }


# Global instance
department_manager = DepartmentManager()


def get_all_departments() -> List[str]:
    """Get list of all department names."""
    return department_manager.get_all_departments()


def get_predefined_departments() -> List[str]:
    """Get list of predefined department names only."""
    return department_manager.get_predefined_departments()


def get_departments_by_category(category: str) -> List[str]:
    """Get departments by category."""
    return department_manager.get_departments_by_category(category)


def get_departments_for_dropdown() -> Dict[str, List[str]]:
    """Get departments organized for dropdown display."""
    return department_manager.get_departments_for_dropdown()


def add_custom_department(name: str, code: str = "", category: str = "Custom", description: str = "") -> bool:
    """Add a custom department."""
    return department_manager.add_custom_department(name, code, category, description)


def validate_department(department_name: str) -> bool:
    """Check if a department name is valid."""
    return department_manager.validate_department(department_name)
