#!/usr/bin/env python3
"""
CLI Test Runner

Convenient command-line interface for running tests.
"""

import sys
import os
import click
import subprocess
from pathlib import Path


@click.command()
@click.option('-m', '--marker', 'markers', multiple=True,
              help='Run tests with specific markers (e.g., -m smoke -m can_bus)')
@click.option('-s', '--suite', help='Run specific test suite (e.g., can_bus, diagnostics)')
@click.option('-c', '--category', help='Run tests by category (e.g., smoke, regression)')
@click.option('-p', '--priority', help='Run tests by priority (e.g., critical, high)')
@click.option('--exec-profile', help='Run tests from execution profile (e.g., smoke, hil, nightly)')
@click.option('--list-profiles', is_flag=True, help='List available execution profiles')
@click.option('--hardware', '--platform', 'platform',
              help='Hardware platform to use (default: from env or ecu_platform_a)')
@click.option('--allure', 'use_allure', is_flag=True, default=False,
              help='Generate Allure report (disabled by default)')
@click.option('--html', is_flag=True, default=True, help='Generate HTML report (default: enabled)')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('-x', '--exitfirst', is_flag=True, help='Exit on first failure')
@click.option('--parallel', '-n', type=int, help='Run tests in parallel (number of workers)')
@click.option('--collect-only', is_flag=True, help='Only collect tests, don\'t run')
@click.argument('tests', nargs=-1)
def main(markers, suite, category, priority, exec_profile, list_profiles, platform, use_allure, html, verbose, exitfirst,
         parallel, collect_only, tests):
    """
    Automotive Test Framework - CLI Test Runner

    Examples:
        # Run execution profiles (NEW!)
        python run_tests.py --exec-profile smoke
        python run_tests.py --exec-profile hil --platform ecu_platform_a
        python run_tests.py --exec-profile nightly

        # List available execution profiles
        python run_tests.py --list-profiles

        # Filter tests from execution profile
        python run_tests.py --exec-profile smoke --suite can_bus
        python run_tests.py --exec-profile regression --priority critical

        # Traditional usage (still supported)
        python run_tests.py -m smoke
        python run_tests.py --suite can_bus
        python run_tests.py --category smoke --platform ecu_platform_b
        python run_tests.py tests/suites/can_bus/test_can_communication.py
        python run_tests.py -n 4 -m regression
    """
    
    # Set platform if specified
    if platform:
        os.environ['HARDWARE_PLATFORM'] = platform

    # Handle execution profiles
    if list_profiles:
        _list_execution_profiles()
        return

    if exec_profile:
        _validate_and_apply_execution_profile(exec_profile, suite, category, priority, tests)

    # Build pytest command
    cmd = ['pytest']
    
    # Add verbosity
    if verbose:
        cmd.append('-vv')
    else:
        cmd.append('-v')
    
    # Add markers
    for marker in markers:
        cmd.extend(['-m', marker])

    # Add category as marker
    if category:
        cmd.extend(['-m', category])

    # Add priority as marker
    if priority:
        cmd.extend(['-m', priority])
    
    # Add suite
    if suite:
        suite_path = Path('tests') / 'suites' / suite
        if suite_path.exists():
            cmd.append(str(suite_path))
        else:
            click.echo(f"Error: Suite '{suite}' not found at {suite_path}", err=True)
            sys.exit(1)
    
    # Add test paths
    if tests:
        cmd.extend(tests)
    
    # Add Allure report
    if use_allure:
        cmd.extend(['--alluredir=reports/allure-results'])
    
    # Add HTML report
    if html:
        cmd.extend(['--html=reports/report.html', '--self-contained-html'])
    
    # Add exit first
    if exitfirst:
        cmd.append('-x')
    
    # Add parallel execution
    if parallel:
        cmd.extend(['-n', str(parallel)])
    
    # Add collect only
    if collect_only:
        cmd.append('--collect-only')
    
    # Display command
    click.echo("Running: " + " ".join(cmd))
    click.echo()
    
    # Run pytest
    result = subprocess.run(cmd)
    
    # Display report instructions if generated
    if html and not collect_only and result.returncode != 5:  # 5 = no tests collected
        click.echo()
        click.echo("=" * 70)
        click.echo("HTML Report generated: reports/report.html")
        click.echo("To view report, run:")
        click.echo("  xdg-open reports/report.html")
        click.echo("  # or")
        click.echo("  python3 -m http.server 8000 -d reports/")
        click.echo("  # then open: http://localhost:8000/report.html")
        click.echo("=" * 70)

    if use_allure and not collect_only and result.returncode != 5:  # 5 = no tests collected
        click.echo()
        click.echo("=" * 70)
        click.echo("To view Allure report, run:")
        click.echo("  allure serve reports/allure-results")
        click.echo("=" * 70)
    
    sys.exit(result.returncode)


def _list_execution_profiles():
    """List available execution profiles"""
    try:
        from framework.core.split_registry import get_split_registry
        registry = get_split_registry()
        profiles = registry.get_available_execution_profiles()

        if not profiles:
            click.echo("No execution profiles found.")
            click.echo("Run: python scripts/migrate_registry.py to create default profiles.")
            return

        click.echo("Available execution profiles:")
        for profile_name in sorted(profiles):
            profile_info = registry.get_execution_profile_info(profile_name)
            if profile_info:
                click.echo(f"  {profile_name}: {profile_info.description}")
            else:
                click.echo(f"  {profile_name}")

        click.echo("\nUsage:")
        click.echo("  python run_tests.py --exec-profile smoke")
        click.echo("  python run_tests.py --exec-profile hil --platform ecu_platform_a")

    except Exception as e:
        click.echo(f"Error loading execution profiles: {e}", err=True)
        sys.exit(1)


def _validate_and_apply_execution_profile(exec_profile, suite, category, priority, tests):
    """Validate execution profile and apply filters"""
    try:
        from framework.core.split_registry import get_split_registry
        registry = get_split_registry()

        # Validate profile exists
        available_profiles = registry.get_available_execution_profiles()
        if exec_profile not in available_profiles:
            click.echo(f"Error: Execution profile '{exec_profile}' not found.", err=True)
            click.echo(f"Available profiles: {', '.join(available_profiles)}", err=True)
            sys.exit(1)

        # Get tests from execution profile
        profile_registry = registry.get_execution_registry(exec_profile)
        profile_info = registry.get_execution_profile_info(exec_profile)

        if not profile_registry:
            click.echo(f"Warning: Execution profile '{exec_profile}' contains no tests.")
            return

        click.echo(f"Using execution profile: {exec_profile}")
        if profile_info:
            click.echo(f"Description: {profile_info.description}")

        # Apply additional filters if specified
        filtered_tests = list(profile_registry.values())

        if suite:
            filtered_tests = [t for t in filtered_tests if t.suite == suite]
            click.echo(f"Filtered by suite: {suite}")

        if category:
            filtered_tests = [t for t in filtered_tests if t.category == category]
            click.echo(f"Filtered by category: {category}")

        if priority:
            filtered_tests = [t for t in filtered_tests if t.priority == priority]
            click.echo(f"Filtered by priority: {priority}")

        if tests:
            test_names = set(tests)
            filtered_tests = [t for t in filtered_tests if t.name in test_names]
            click.echo(f"Filtered by test names: {', '.join(tests)}")

        click.echo(f"Total tests to run: {len(filtered_tests)}")

        if not filtered_tests:
            click.echo("No tests match the specified criteria.")
            sys.exit(0)

        # Store filtered test names for pytest to use
        os.environ['VORTEX_EXECUTION_PROFILE'] = exec_profile
        os.environ['VORTEX_FILTERED_TESTS'] = ','.join([t.name for t in filtered_tests])

    except Exception as e:
        click.echo(f"Error processing execution profile: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
