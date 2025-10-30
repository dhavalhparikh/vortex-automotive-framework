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
def main(markers, suite, category, priority, platform, use_allure, html, verbose, exitfirst,
         parallel, collect_only, tests):
    """
    Automotive Test Framework - CLI Test Runner
    
    Examples:
        # Run all smoke tests
        python run_tests.py -m smoke
        
        # Run CAN bus test suite
        python run_tests.py --suite can_bus

        # Run by category
        python run_tests.py --category smoke

        # Run by priority
        python run_tests.py --priority critical

        # Run with specific platform
        python run_tests.py --platform ecu_platform_b --category smoke
        
        # Run specific test file
        python run_tests.py tests/suites/can_bus/test_can_communication.py
        
        # Run in parallel
        python run_tests.py -n 4 -m regression
    """
    
    # Set platform if specified
    if platform:
        os.environ['HARDWARE_PLATFORM'] = platform
    
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


if __name__ == '__main__':
    main()
