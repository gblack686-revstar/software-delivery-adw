#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pyyaml"]
# ///

"""UI Reviewer Agent - End-to-end testing with Playwright.

Usage:
    uv run adw_ui_review.py --adw-id abc123 [--app-url http://localhost:3000]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.adw_modules.state import ADWState


def main():
    """Main entry point for UI reviewer agent."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="UI Reviewer Agent")
    parser.add_argument("--adw-id", required=True, help="Workflow ID")
    parser.add_argument("--app-url", default="http://localhost:3000", help="Application URL")
    args = parser.parse_args()

    print(f"\n🧪 Starting UI Review Phase")
    print(f"📋 ADW ID: {args.adw_id}")
    print(f"🌐 App URL: {args.app_url}")

    # Load state
    state = ADWState.load_from_id(args.adw_id)
    if not state:
        print(f"❌ Error: No state found for ADW ID: {args.adw_id}")
        sys.exit(1)

    # Check prerequisites
    user_flows = state.get("scoping.user_flows")
    if not user_flows:
        print("❌ Error: Scoping phase not complete (no user flows)")
        sys.exit(1)

    # Update state
    state.update_phase("ui_review", started=True, app_url=args.app_url)
    state.save()

    # Create test output directories
    test_dir = Path(f"agents/{args.adw_id}/ui_reviewer_agent")
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "e2e_tests").mkdir(exist_ok=True)
    (test_dir / "videos").mkdir(exist_ok=True)
    (test_dir / "screenshots").mkdir(exist_ok=True)

    print(f"\n📄 Reading user flows from: {user_flows}")
    print(f"\n🚧 This is a template script!")
    print(f"\nTo run E2E tests with Playwright:")
    print(f"1. Ensure app is running at {args.app_url}")
    print(f"2. Call Claude Code with /review_ui command")
    print(f"3. Playwright MCP will control the browser")
    print(f"4. Tests will be executed and recorded")
    print(f"5. Results saved to {test_dir}")

    # Create placeholder test report
    test_report = {
        "adw_id": args.adw_id,
        "app_url": args.app_url,
        "executed_at": datetime.now().isoformat(),
        "total_flows": 0,
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "flows": [],
        "status": "not_run"
    }

    report_path = test_dir / "test_report.json"
    with open(report_path, 'w') as f:
        json.dump(test_report, f, indent=2)

    # Update state
    state.update_phase(
        "ui_review",
        completed=False,
        test_report=str(report_path),
        test_directory=str(test_dir)
    )
    state.save()

    print(f"\n✅ UI review tracking initialized")
    print(f"\n📊 Test report will be at: {report_path}")
    print(f"\n🎬 Videos will be saved to: {test_dir / 'videos'}")
    print(f"\n📸 Screenshots will be saved to: {test_dir / 'screenshots'}")


if __name__ == "__main__":
    main()
