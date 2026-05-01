#!/usr/bin/env python3
"""
B2B Automation Pitch Generator
Generates a 30-day B2B automation consultancy pitch roadmap for any target industry.
Uses claude-opus-4-7 with prompt caching and assistant-turn prefill.

Usage:
    python run_pitch_generator.py --industry "flooring contractor"
    python run_pitch_generator.py --industry "property management"
"""

import anthropic
import argparse
import os
import sys


def load_system_prompt() -> str:
    skill_path = os.path.join(os.path.dirname(__file__), "..", "SKILL.md")
    with open(os.path.normpath(skill_path)) as f:
        content = f.read()
    # Strip YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content


def generate_pitch(industry: str, verbose: bool = False) -> str:
    client = anthropic.Anthropic()
    system_prompt = load_system_prompt()

    user_message = (
        f"<target_industry>\n{industry}\n</target_industry>\n\n"
        "Generate the full 30-day B2B automation pitch roadmap for this industry. "
        "Complete your scratchpad analysis first, validate all constraints, "
        "then output the complete <roadmap>."
    )

    if verbose:
        print(f"[INFO] Model: claude-opus-4-7")
        print(f"[INFO] Industry: {industry}")
        print(f"[INFO] Sending request...\n")

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        temperature=0,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {"role": "user", "content": user_message},
            # Prefill assistant turn to force scratchpad CoT before roadmap
            {"role": "assistant", "content": "<scratchpad>"},
        ],
    )

    if verbose:
        usage = response.usage
        print(f"[INFO] Input tokens: {usage.input_tokens}")
        print(f"[INFO] Output tokens: {usage.output_tokens}")
        cache_read = getattr(usage, "cache_read_input_tokens", 0)
        cache_write = getattr(usage, "cache_creation_input_tokens", 0)
        print(f"[INFO] Cache read: {cache_read} | Cache write: {cache_write}\n")

    # Reconstruct full output (prefill + completion)
    return "<scratchpad>" + response.content[0].text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a 30-day B2B automation pitch roadmap"
    )
    parser.add_argument(
        "--industry",
        required=True,
        help="Target client industry (e.g. 'flooring contractor', 'property management')",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show token usage and cache stats"
    )
    parser.add_argument(
        "--output", help="Write output to file instead of stdout"
    )
    args = parser.parse_args()

    print(f"Generating 30-day B2B automation pitch for: {args.industry}\n")
    print("=" * 70)

    result = generate_pitch(args.industry, verbose=args.verbose)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Output written to: {args.output}")
    else:
        print(result)

    print("=" * 70)


if __name__ == "__main__":
    main()
