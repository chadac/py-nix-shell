#!/usr/bin/env python3
"""
Script to update the CLI usage section in README.md with current pynix --help output.
"""

import re
import subprocess
from pathlib import Path


def main() -> None:
    # Get current help output
    help_output = subprocess.check_output(
        ["uv", "run", "--", "pynix", "--help"],
    ).decode()

    # Read current README
    readme_path = Path("README.md")
    with readme_path.open("r") as f:
        content = f.read()

    # Create new CLI usage section
    new_section = f"""```
$ pynix --help
{help_output}```"""

    # Replace the CLI usage section using HTML comments as markers
    pattern = r"<!-- CLI_HELP_START -->.*?<!-- CLI_HELP_END -->"
    replacement = f"<!-- CLI_HELP_START -->\n{new_section}\n<!-- CLI_HELP_END -->"

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Write back to README
    with open(readme_path, "w") as f:
        f.write(new_content)

    print("✓ Updated README.md CLI usage section with current pynix --help output")


if __name__ == "__main__":
    main()
