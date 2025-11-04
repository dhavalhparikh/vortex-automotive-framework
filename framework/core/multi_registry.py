"""
Multi-File Test Registry Manager

Loads test metadata from multiple YAML files for better maintainability.
Supports both single-file legacy format and new multi-file structure.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from framework.core.test_registry import MetadataConfig

logger = logging.getLogger(__name__)


class MultiFileRegistryManager:
    """
    Enhanced registry manager that loads from multiple files
    """

    def __init__(self, registry_dir: Optional[Path] = None):
        """
        Initialize multi-file registry manager

        Args:
            registry_dir: Directory containing registry files
                         Defaults to <project_root>/config/test_registry/
        """
        if registry_dir is None:
            project_root = Path(__file__).parent.parent.parent
            self.registry_dir = project_root / "config" / "test_registry"
        else:
            self.registry_dir = Path(registry_dir)

        # Legacy single file fallback
        self.legacy_file = Path(__file__).parent.parent.parent / "config" / "test_registry.yaml"

        self._registry = {}
        self._globals = {}
        self._suite_info = {}
        self.load_registry()

    def load_registry(self):
        """Load test registry from multiple files or legacy single file"""
        try:
            if self.registry_dir.exists():
                logger.info(f"Loading multi-file registry from {self.registry_dir}")
                self._load_multi_file_registry()
            elif self.legacy_file.exists():
                logger.info(f"Loading legacy registry from {self.legacy_file}")
                self._load_legacy_registry()
            else:
                logger.warning("No test registry found - creating empty registry")

        except Exception as e:
            logger.error(f"Failed to load test registry: {e}")
            raise

    def _load_multi_file_registry(self):
        """Load from multiple YAML files in registry directory"""

        # Load globals first
        globals_file = self.registry_dir / "_globals.yaml"
        if globals_file.exists():
            with open(globals_file, 'r') as f:
                self._globals = yaml.safe_load(f) or {}

        # Load each suite file
        for suite_file in self.registry_dir.glob("*.yaml"):
            if suite_file.name.startswith("_"):
                continue  # Skip special files like _globals.yaml

            suite_name = suite_file.stem
            logger.debug(f"Loading suite: {suite_name}")

            with open(suite_file, 'r') as f:
                suite_data = yaml.safe_load(f)

            if not suite_data:
                continue

            # Store suite info
            self._suite_info[suite_name] = suite_data.get('suite_info', {})

            # Process tests from this suite
            for test_config in suite_data.get('tests', []):
                test_config = self._apply_defaults(test_config, suite_name)

                test_metadata = MetadataConfig(
                    name=test_config['name'],
                    suite=suite_name,
                    category=test_config['category'],
                    priority=test_config['priority'],
                    description=test_config['description'],
                    platforms=test_config.get('platforms', ['all']),
                    requirements_hardware=test_config.get('requirements_hardware', False),
                    max_duration=test_config.get('max_duration')
                )

                self._registry[test_config['name']] = test_metadata

    def _load_legacy_registry(self):
        """Load from legacy single file format"""
        with open(self.legacy_file, 'r') as f:
            config = yaml.safe_load(f)

        # Load legacy format (same as existing logic)
        for suite_name, suite_config in config.get('test_suites', {}).items():
            for test_config in suite_config.get('tests', []):
                test_metadata = MetadataConfig(
                    name=test_config['name'],
                    suite=suite_name,
                    category=test_config['category'],
                    priority=test_config['priority'],
                    description=test_config['description'],
                    platforms=test_config.get('platforms', ['all']),
                    requirements_hardware=test_config.get('requirements_hardware', False),
                    max_duration=test_config.get('max_duration')
                )

                self._registry[test_config['name']] = test_metadata

        # Load legacy globals
        self._globals = {
            'categories': config.get('categories', {}),
            'priorities': config.get('priorities', {})
        }

    def _apply_defaults(self, test_config: Dict[str, Any], suite_name: str) -> Dict[str, Any]:
        """Apply default values from globals and suite info"""

        # Apply global defaults
        defaults = self._globals.get('defaults', {})
        for key, default_value in defaults.items():
            if key not in test_config:
                test_config[key] = default_value

        # Apply suite defaults
        suite_info = self._suite_info.get(suite_name, {})
        suite_defaults = suite_info.get('default_platforms')
        if suite_defaults and 'platforms' not in test_config:
            test_config['platforms'] = suite_defaults

        return test_config

    def get_test_metadata(self, test_name: str) -> Optional[MetadataConfig]:
        """Get metadata for a specific test"""
        return self._registry.get(test_name)

    def get_tests_by_suite(self, suite: str) -> List[MetadataConfig]:
        """Get all tests in a specific suite"""
        return [test for test in self._registry.values() if test.suite == suite]

    def get_available_suites(self) -> List[str]:
        """Get list of all available test suites"""
        return list(set(test.suite for test in self._registry.values()))

    def get_suite_info(self, suite_name: str) -> Dict[str, Any]:
        """Get information about a specific suite"""
        return self._suite_info.get(suite_name, {})

    def list_registry_files(self) -> List[Path]:
        """List all registry files being used"""
        if self.registry_dir.exists():
            return list(self.registry_dir.glob("*.yaml"))
        elif self.legacy_file.exists():
            return [self.legacy_file]
        else:
            return []

    # Maintain compatibility with existing RegistryManager interface
    def get_pytest_markers(self, test_name: str) -> List[str]:
        """Generate pytest markers for a test - compatibility method"""
        metadata = self.get_test_metadata(test_name)
        if not metadata:
            return []

        markers = [
            metadata.category,
            metadata.suite,
            metadata.priority
        ]

        # Add platform markers
        if "all" in metadata.platforms:
            markers.append("all_platforms")
        else:
            for platform in metadata.platforms:
                markers.append(f"platform_{platform}")

        if metadata.requirements_hardware:
            markers.append("requires_hardware")

        return markers


# Global registry instance - compatible with existing code
_multi_registry_instance = None

def get_multi_file_registry() -> MultiFileRegistryManager:
    """Get global multi-file registry instance"""
    global _multi_registry_instance
    if _multi_registry_instance is None:
        _multi_registry_instance = MultiFileRegistryManager()
    return _multi_registry_instance