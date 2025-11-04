#!/usr/bin/env python3
"""
Test Registry Migration Script

Migrates from monolithic test_registry.yaml to split structure:
- config/test_registry/suites/*.yaml (test definitions)
- config/test_registry/execution/*.yaml (execution profiles)
- config/test_registry/_globals.yaml (shared config)
"""

import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, List


class RegistryMigrator:
    """Migrates test registry from monolithic to split structure"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.old_file = self.project_root / "config" / "test_registry.yaml"
        self.new_dir = self.project_root / "config" / "test_registry"
        self.suites_dir = self.new_dir / "suites"
        self.execution_dir = self.new_dir / "execution"

    def migrate(self, backup: bool = True):
        """
        Perform the migration

        Args:
            backup: Whether to backup the original file
        """
        print("🚀 Starting test registry migration...")

        if not self.old_file.exists():
            print(f"❌ Source file not found: {self.old_file}")
            return False

        # Create backup
        if backup:
            backup_file = self.old_file.with_suffix('.yaml.backup')
            shutil.copy2(self.old_file, backup_file)
            print(f"📋 Created backup: {backup_file}")

        # Load existing registry
        with open(self.old_file, 'r') as f:
            old_config = yaml.safe_load(f)

        # Create directory structure
        self._create_directories()

        # Migrate components
        self._migrate_globals(old_config)
        self._migrate_suites(old_config)
        self._create_default_execution_profiles(old_config)

        print("✅ Migration completed successfully!")
        print(f"📁 New registry structure created in: {self.new_dir}")
        return True

    def _create_directories(self):
        """Create the new directory structure"""
        self.new_dir.mkdir(exist_ok=True)
        self.suites_dir.mkdir(exist_ok=True)
        self.execution_dir.mkdir(exist_ok=True)
        print(f"📁 Created directory structure in {self.new_dir}")

    def _migrate_globals(self, config: Dict[str, Any]):
        """Create _globals.yaml with shared configuration"""
        globals_config = {
            'categories': config.get('categories', {
                'smoke': {'description': 'Critical smoke tests that must pass', 'execution_order': 1},
                'regression': {'description': 'Regression test suite', 'execution_order': 2},
                'integration': {'description': 'Cross-component integration tests', 'execution_order': 3},
                'performance': {'description': 'Performance and load tests', 'execution_order': 4}
            }),
            'priorities': config.get('priorities', {
                'critical': {'description': 'Must-pass critical tests', 'severity_level': 'blocker'},
                'high': {'description': 'High priority tests', 'severity_level': 'critical'},
                'medium': {'description': 'Medium priority tests', 'severity_level': 'normal'},
                'low': {'description': 'Low priority tests', 'severity_level': 'minor'}
            }),
            'defaults': {
                'platforms': ['all'],
                'category': 'regression',
                'priority': 'medium',
                'requirements_hardware': False,
                'max_duration': None
            },
            'validation': {
                'required_fields': ['name', 'category', 'priority', 'description'],
                'valid_categories': ['smoke', 'regression', 'integration', 'performance'],
                'valid_priorities': ['critical', 'high', 'medium', 'low']
            }
        }

        globals_file = self.new_dir / "_globals.yaml"
        with open(globals_file, 'w') as f:
            yaml.dump(globals_config, f, default_flow_style=False, sort_keys=False)

        print(f"📄 Created: {globals_file}")

    def _migrate_suites(self, config: Dict[str, Any]):
        """Create individual suite files"""
        test_suites = config.get('test_suites', {})

        for suite_name, suite_config in test_suites.items():
            suite_file_config = {
                'suite_info': {
                    'name': suite_name,
                    'description': suite_config.get('description', f"{suite_name.replace('_', ' ').title()} tests"),
                    'default_platforms': suite_config.get('platforms', ['all'])
                },
                'tests': suite_config.get('tests', [])
            }

            suite_file = self.suites_dir / f"{suite_name}.yaml"
            with open(suite_file, 'w') as f:
                yaml.dump(suite_file_config, f, default_flow_style=False, sort_keys=False)

            print(f"📄 Created: {suite_file}")

    def _create_default_execution_profiles(self, config: Dict[str, Any]):
        """Create default execution profiles based on categories"""

        # Analyze existing tests to create smart execution profiles
        test_suites = config.get('test_suites', {})

        # Group tests by category
        tests_by_category = {}
        for suite_name, suite_config in test_suites.items():
            for test in suite_config.get('tests', []):
                category = test.get('category', 'regression')
                if category not in tests_by_category:
                    tests_by_category[category] = []
                tests_by_category[category].append((suite_name, test['name']))

        # Create execution profiles
        execution_profiles = {
            'smoke': {
                'execution_profile': {
                    'name': 'smoke',
                    'description': 'Critical smoke tests for fast feedback',
                    'timeout': 300
                },
                'include': []
            },
            'regression': {
                'execution_profile': {
                    'name': 'regression',
                    'description': 'Full regression test suite',
                    'timeout': 1800
                },
                'include': []
            },
            'integration': {
                'execution_profile': {
                    'name': 'integration',
                    'description': 'Integration and cross-component tests',
                    'timeout': 900
                },
                'include': []
            },
            'nightly': {
                'execution_profile': {
                    'name': 'nightly',
                    'description': 'Comprehensive nightly test run',
                    'timeout': 3600
                },
                'include': []
            }
        }

        # Populate execution profiles based on test categories
        for category, tests in tests_by_category.items():
            if category in execution_profiles:
                # Group tests by suite for cleaner organization
                suite_tests = {}
                for suite_name, test_name in tests:
                    if suite_name not in suite_tests:
                        suite_tests[suite_name] = []
                    suite_tests[suite_name].append(test_name)

                # Add to execution profile
                for suite_name, test_names in suite_tests.items():
                    include_entry = {'suite': suite_name}

                    # If all tests from suite are in this category, include entire suite
                    all_suite_tests = [t['name'] for t in test_suites[suite_name].get('tests', [])]
                    if set(test_names) == set(all_suite_tests):
                        # Include entire suite
                        pass  # Don't add 'tests' key
                    else:
                        # Include specific tests
                        include_entry['tests'] = test_names

                    # Add category-specific overrides
                    if category == 'smoke':
                        include_entry['overrides'] = {
                            'timeout': 60,
                            'priority': 'critical'
                        }

                    execution_profiles[category]['include'].append(include_entry)

        # Add nightly as comprehensive profile (all suites)
        execution_profiles['nightly']['include'] = [
            {'suite': suite_name} for suite_name in test_suites.keys()
        ]

        # Write execution profile files
        for profile_name, profile_config in execution_profiles.items():
            if profile_config['include']:  # Only create if there are tests
                profile_file = self.execution_dir / f"{profile_name}.yaml"
                with open(profile_file, 'w') as f:
                    yaml.dump(profile_config, f, default_flow_style=False, sort_keys=False)
                print(f"📄 Created: {profile_file}")

    def validate_migration(self) -> bool:
        """Validate that migration was successful"""
        print("🔍 Validating migration...")

        required_files = [
            self.new_dir / "_globals.yaml",
        ]

        # Check required files exist
        for file_path in required_files:
            if not file_path.exists():
                print(f"❌ Missing required file: {file_path}")
                return False

        # Check we have suite files
        suite_files = list(self.suites_dir.glob("*.yaml"))
        if not suite_files:
            print("❌ No suite files created")
            return False

        # Check we have execution files
        execution_files = list(self.execution_dir.glob("*.yaml"))
        if not execution_files:
            print("❌ No execution profile files created")
            return False

        print(f"✅ Validation passed: {len(suite_files)} suites, {len(execution_files)} execution profiles")
        return True


def main():
    """Main migration function"""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate test registry to split structure")
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip creating backup of original file')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate existing migration')

    args = parser.parse_args()

    migrator = RegistryMigrator()

    if args.validate_only:
        success = migrator.validate_migration()
        exit(0 if success else 1)

    success = migrator.migrate(backup=not args.no_backup)
    if success:
        migrator.validate_migration()

    exit(0 if success else 1)


if __name__ == "__main__":
    main()