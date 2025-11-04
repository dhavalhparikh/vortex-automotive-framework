"""
Split Test Registry Manager

Manages test registry split into suites/ and execution/ directories.
Supports execution profiles with flexible test inclusion and metadata overrides.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, replace
from copy import deepcopy

from framework.core.test_registry import MetadataConfig

logger = logging.getLogger(__name__)


@dataclass
class ExecutionProfile:
    """Execution profile configuration"""
    name: str
    description: str
    timeout: Optional[int] = None
    include: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.include is None:
            self.include = []


class SplitRegistryManager:
    """
    Registry manager for split structure with execution profiles
    """

    def __init__(self, registry_dir: Optional[Path] = None):
        """
        Initialize split registry manager

        Args:
            registry_dir: Directory containing registry files
                         Defaults to <project_root>/config/test_registry/
        """
        if registry_dir is None:
            project_root = Path(__file__).parent.parent.parent
            self.registry_dir = project_root / "config" / "test_registry"
        else:
            self.registry_dir = Path(registry_dir)

        self.suites_dir = self.registry_dir / "suites"
        self.execution_dir = self.registry_dir / "execution"
        self.globals_file = self.registry_dir / "_globals.yaml"

        # Legacy fallback
        self.legacy_file = Path(__file__).parent.parent.parent / "config" / "test_registry.yaml"

        self._base_registry = {}  # Base test definitions from suites/
        self._globals = {}        # Global configuration
        self._suite_info = {}     # Suite metadata
        self._execution_profiles = {}  # Available execution profiles

        self.load_registry()

    def load_registry(self):
        """Load registry from split structure or legacy fallback"""
        try:
            if self.registry_dir.exists():
                logger.info(f"Loading split registry from {self.registry_dir}")
                self._load_split_registry()
            elif self.legacy_file.exists():
                logger.info(f"Loading legacy registry from {self.legacy_file}")
                self._load_legacy_fallback()
            else:
                logger.warning("No test registry found - creating empty registry")

        except Exception as e:
            logger.error(f"Failed to load test registry: {e}")
            raise

    def _load_split_registry(self):
        """Load from split directory structure"""
        # Load globals
        if self.globals_file.exists():
            with open(self.globals_file, 'r') as f:
                self._globals = yaml.safe_load(f) or {}

        # Load suites
        if self.suites_dir.exists():
            for suite_file in self.suites_dir.glob("*.yaml"):
                self._load_suite_file(suite_file)

        # Load execution profiles
        if self.execution_dir.exists():
            for profile_file in self.execution_dir.glob("*.yaml"):
                self._load_execution_profile(profile_file)

    def _load_suite_file(self, suite_file: Path):
        """Load a single suite file"""
        suite_name = suite_file.stem
        logger.debug(f"Loading suite: {suite_name}")

        with open(suite_file, 'r') as f:
            suite_data = yaml.safe_load(f)

        if not suite_data:
            return

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

            self._base_registry[test_config['name']] = test_metadata

    def _load_execution_profile(self, profile_file: Path):
        """Load an execution profile"""
        profile_name = profile_file.stem
        logger.debug(f"Loading execution profile: {profile_name}")

        with open(profile_file, 'r') as f:
            profile_data = yaml.safe_load(f)

        if not profile_data:
            return

        profile_info = profile_data.get('execution_profile', {})
        profile = ExecutionProfile(
            name=profile_info.get('name', profile_name),
            description=profile_info.get('description', ''),
            timeout=profile_info.get('timeout'),
            include=profile_data.get('include', [])
        )

        self._execution_profiles[profile_name] = profile

    def _load_legacy_fallback(self):
        """Load from legacy single file format"""
        with open(self.legacy_file, 'r') as f:
            config = yaml.safe_load(f)

        # Load legacy format
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

                self._base_registry[test_config['name']] = test_metadata

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

    def get_execution_registry(self, profile_name: Optional[str] = None) -> Dict[str, MetadataConfig]:
        """
        Get registry with execution profile applied

        Args:
            profile_name: Name of execution profile to apply, None for base registry

        Returns:
            Dictionary of test_name -> MetadataConfig with overrides applied
        """
        if profile_name is None:
            return dict(self._base_registry)

        if profile_name not in self._execution_profiles:
            raise ValueError(f"Execution profile '{profile_name}' not found. "
                           f"Available: {list(self._execution_profiles.keys())}")

        profile = self._execution_profiles[profile_name]
        execution_registry = {}

        # Process each include entry in the execution profile
        for include_entry in profile.include:
            suite_name = include_entry.get('suite')
            if not suite_name:
                logger.warning(f"Include entry missing 'suite' field: {include_entry}")
                continue

            # Get tests to include from this suite
            include_tests = include_entry.get('tests')
            if include_tests is None:
                # Include all tests from suite
                suite_tests = {name: metadata for name, metadata in self._base_registry.items()
                             if metadata.suite == suite_name}
            else:
                # Include specific tests
                suite_tests = {name: metadata for name, metadata in self._base_registry.items()
                             if metadata.suite == suite_name and name in include_tests}

            # Apply overrides
            overrides = include_entry.get('overrides', {})
            for test_name, metadata in suite_tests.items():
                if overrides:
                    # Apply overrides to metadata
                    metadata = self._apply_overrides(metadata, overrides)

                execution_registry[test_name] = metadata

        return execution_registry

    def _apply_overrides(self, metadata: MetadataConfig, overrides: Dict[str, Any]) -> MetadataConfig:
        """Apply overrides to test metadata"""
        # Create a copy and apply overrides
        override_dict = {}

        # Map override keys to metadata fields
        if 'category' in overrides:
            override_dict['category'] = overrides['category']
        if 'priority' in overrides:
            override_dict['priority'] = overrides['priority']
        if 'platforms' in overrides:
            override_dict['platforms'] = overrides['platforms']
        if 'requirements_hardware' in overrides:
            override_dict['requirements_hardware'] = overrides['requirements_hardware']
        if 'max_duration' in overrides:
            override_dict['max_duration'] = overrides['max_duration']
        if 'timeout' in overrides:
            override_dict['max_duration'] = overrides['timeout']

        return replace(metadata, **override_dict)

    def get_test_metadata(self, test_name: str, profile_name: Optional[str] = None) -> Optional[MetadataConfig]:
        """Get metadata for a specific test, optionally with profile applied"""
        registry = self.get_execution_registry(profile_name)
        return registry.get(test_name)

    def get_tests_by_suite(self, suite: str, profile_name: Optional[str] = None) -> List[MetadataConfig]:
        """Get all tests in a specific suite, optionally with profile applied"""
        registry = self.get_execution_registry(profile_name)
        return [test for test in registry.values() if test.suite == suite]

    def get_tests_by_category(self, category: str, profile_name: Optional[str] = None) -> List[MetadataConfig]:
        """Get all tests in a specific category, optionally with profile applied"""
        registry = self.get_execution_registry(profile_name)
        return [test for test in registry.values() if test.category == category]

    def get_available_suites(self) -> List[str]:
        """Get list of all available test suites"""
        return list(set(test.suite for test in self._base_registry.values()))

    def get_available_execution_profiles(self) -> List[str]:
        """Get list of all available execution profiles"""
        return list(self._execution_profiles.keys())

    def get_execution_profile_info(self, profile_name: str) -> Optional[ExecutionProfile]:
        """Get information about a specific execution profile"""
        return self._execution_profiles.get(profile_name)

    def filter_tests_by_names(self, test_names: List[str], profile_name: Optional[str] = None) -> List[MetadataConfig]:
        """Filter tests by specific test names"""
        registry = self.get_execution_registry(profile_name)
        return [registry[name] for name in test_names if name in registry]

    def filter_tests_by_suites(self, suite_names: List[str], profile_name: Optional[str] = None) -> List[MetadataConfig]:
        """Filter tests by specific suite names"""
        registry = self.get_execution_registry(profile_name)
        return [test for test in registry.values() if test.suite in suite_names]

    def get_pytest_markers(self, test_name: str, profile_name: Optional[str] = None) -> List[str]:
        """Generate pytest markers for a test"""
        metadata = self.get_test_metadata(test_name, profile_name)
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

    def get_allure_labels(self, test_name: str, profile_name: Optional[str] = None) -> Dict[str, str]:
        """Generate Allure labels for a test"""
        metadata = self.get_test_metadata(test_name, profile_name)
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

    def list_registry_files(self) -> List[Path]:
        """List all registry files being used"""
        files = []
        if self.registry_dir.exists():
            files.extend(self.suites_dir.glob("*.yaml"))
            files.extend(self.execution_dir.glob("*.yaml"))
            if self.globals_file.exists():
                files.append(self.globals_file)
        elif self.legacy_file.exists():
            files.append(self.legacy_file)
        return files


# Global registry instance for compatibility
_split_registry_instance = None

def get_split_registry() -> SplitRegistryManager:
    """Get global split registry instance"""
    global _split_registry_instance
    if _split_registry_instance is None:
        _split_registry_instance = SplitRegistryManager()
    return _split_registry_instance