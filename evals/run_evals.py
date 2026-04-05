#!/usr/bin/env python3
"""
Simple eval runner for SAMS PRODUCT OS.

Runs all tests and provides a summary.

Usage:
    python evals/run_evals.py           # Run all evals
    python evals/run_evals.py --mcp     # Only MCP server tests
    python evals/run_evals.py --workflows  # Only workflow tests
    python evals/run_evals.py --behavior  # Only agent behavior tests
    python evals/run_evals.py --llm     # Only LLM behavioral evals (needs ANTHROPIC_API_KEY)
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_tests(test_path: str, verbose: bool = True) -> int:
    """Run pytest on a specific path and return exit code."""
    project_root = Path(__file__).parent.parent
    cmd = ["uv", "run", "--project", str(project_root / "evals"), "python", "-m", "pytest", test_path]
    if verbose:
        cmd.append("-v")

    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run SAMS PRODUCT OS evals")
    parser.add_argument("--mcp", action="store_true", help="Only run MCP server tests")
    parser.add_argument("--workflows", action="store_true", help="Only run workflow tests")
    parser.add_argument("--behavior", action="store_true", help="Only run agent behavior tests")
    parser.add_argument("--llm", action="store_true", help="Only run LLM behavioral evals (requires ANTHROPIC_API_KEY)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Less verbose output")
    args = parser.parse_args()

    verbose = not args.quiet
    results: dict[str, int] = {}

    # Determine which tests to run
    if args.mcp:
        test_sets = [("MCP Server Tests", "tools/mcp-servers/task-manager/test_server.py")]
    elif args.workflows:
        test_sets = [("Workflow Tests", "evals/test_workflows.py")]
    elif args.behavior:
        test_sets = [("Agent Behavior Tests", "evals/test_agent_behavior.py")]
    elif args.llm:
        test_sets = [("LLM Behavioral Evals", "evals/test_llm_behavior.py")]
    else:
        test_sets = [
            ("MCP Server Tests", "tools/mcp-servers/task-manager/test_server.py"),
            ("Workflow Tests", "evals/test_workflows.py"),
            ("Agent Behavior Tests", "evals/test_agent_behavior.py"),
            ("LLM Behavioral Evals", "evals/test_llm_behavior.py"),
        ]

    # Run tests
    print("=" * 60)
    print("SAMS PRODUCT OS Evaluation Suite")
    print("=" * 60)
    print()

    for name, path in test_sets:
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print(f"{'='*60}\n")

        exit_code = run_tests(path, verbose)
        results[name] = exit_code

    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    all_passed = True
    for name, exit_code in results.items():
        status = "PASSED" if exit_code == 0 else "FAILED"
        symbol = "✓" if exit_code == 0 else "✗"
        print(f"  {symbol} {name}: {status}")
        if exit_code != 0:
            all_passed = False

    print()
    if all_passed:
        print("✓ All evals passed!")
        return 0
    else:
        print("✗ Some evals failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
