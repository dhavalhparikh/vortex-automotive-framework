"""
Test Registry Management

Manages test configuration and applies metadata dynamically.
Keeps test code clean by externalizing all pytest/allure decorators.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MetadataConfig:
    """Test metadata from configuration"""
    name: str
    suite: str
    category: str
    priority: str
    description: str
    platforms: List[str]
    requirements_hardware: bool = False
    max_duration: Optional[str] = None


class RegistryManager:
    """
    Manages test configuration and metadata.

    Loads test registry from YAML and provides methods to query
    test metadata without cluttering test code with decorators.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize test registry"""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "test_registry.yaml"

        self.config_path = config_path
        self._registry = {}
        self._categories = {}
        self._priorities = {}
        self.load_registry()

    def load_registry(self):
        """Load test registry from YAML configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            self._categories = config.get('categories', {})
            self._priorities = config.get('priorities', {})

            # Parse test suites
            for suite_name, suite_config in config.get('test_suites', {}).items():
                for test_config in suite_config.get('tests', []):
                    test_metadata = MetadataConfig(
                        name=test_config['name'],
                        suite=suite_name,
                        category=test_config['category'],
                        priority=test_config['priority'],
                        description=test_config['description'],
                        platforms=test_config['platforms'],
                        requirements_hardware=test_config.get('requirements_hardware', False)
                    )

                    # Add category max_duration if available
                    category_info = self._categories.get(test_config['category'], {})
                    test_metadata.max_duration = category_info.get('max_duration')

                    self._registry[test_config['name']] = test_metadata

            logger.info(f"Loaded {len(self._registry)} tests from registry")

        except Exception as e:
            logger.error(f"Failed to load test registry: {e}")
            raise

    def get_test_metadata(self, test_name: str) -> Optional[MetadataConfig]:
        """Get metadata for a specific test"""
        return self._registry.get(test_name)

    def get_tests_by_category(self, category: str) -> List[MetadataConfig]:
        """Get all tests in a specific category"""
        return [test for test in self._registry.values() if test.category == category]

    def get_tests_by_suite(self, suite: str) -> List[MetadataConfig]:
        """Get all tests in a specific suite"""
        return [test for test in self._registry.values() if test.suite == suite]

    def get_tests_by_platform(self, platform: str) -> List[MetadataConfig]:
        """Get all tests compatible with a platform"""
        return [
            test for test in self._registry.values()
            if platform in test.platforms or "all" in test.platforms
        ]

    def get_tests_by_priority(self, priority: str) -> List[MetadataConfig]:
        """Get all tests with specific priority"""
        return [test for test in self._registry.values() if test.priority == priority]

    def is_test_compatible(self, test_name: str, platform: str) -> bool:
        """Check if test is compatible with platform"""
        metadata = self.get_test_metadata(test_name)
        if not metadata:
            return False
        return platform in metadata.platforms or "all" in metadata.platforms

    def get_pytest_markers(self, test_name: str) -> List[str]:
        """Generate pytest markers for a test"""
        metadata = self.get_test_metadata(test_name)
        if not metadata:
            return []

        markers = [
            metadata.category,
            metadata.suite,
            metadata.priority
        ]

        # Add platform markers for all specified platforms
        if "all" in metadata.platforms:
            markers.append("all_platforms")
        else:
            for platform in metadata.platforms:
                markers.append(f"platform_{platform}")

        if metadata.requirements_hardware:
            markers.append("requires_hardware")

        return markers

    def get_allure_labels(self, test_name: str) -> Dict[str, str]:
        """Generate Allure labels for a test"""
        metadata = self.get_test_metadata(test_name)
        if not metadata:
            return {}

        return {
            'feature': metadata.suite.replace('_', ' ').title(),
            'story': metadata.description,
            'severity': self._priority_to_severity(metadata.priority),
            'tag': metadata.category
        }

    def _priority_to_severity(self, priority: str) -> str:
        """Convert priority to Allure severity"""
        mapping = {
            'critical': 'blocker',
            'high': 'critical',
            'medium': 'normal',
            'low': 'minor'
        }
        return mapping.get(priority, 'normal')

    def list_available_categories(self) -> List[str]:
        """List all available test categories"""
        return list(self._categories.keys())

    def list_available_suites(self) -> List[str]:
        """List all available test suites"""
        return list(set(test.suite for test in self._registry.values()))

    def list_available_priorities(self) -> List[str]:
        """List all available priorities"""
        return list(self._priorities.keys())


# Global registry instance
_registry_instance = None

def get_test_registry() -> RegistryManager:
    """Get global test registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = RegistryManager()
    return _registry_instance