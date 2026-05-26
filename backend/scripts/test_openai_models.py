"""Test OpenAI model access from the backend environment.

Set your key in the environment before running:

    export OPENAI_API_KEY='...'

Or add it to `backend/.env` as `OPENAI_API_KEY=...`.
The script loads `backend/.env` automatically when present.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


DEFAULT_MODELS = [
    "gpt-4o-mini",
    "gpt-4.1-mini",
    "gpt-4.1",
]


def load_environment() -> None:
	"""Load environment variables from backend/.env if it exists."""
	root = Path(__file__).resolve().parents[1]
	load_dotenv(root / ".env")


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Test OpenAI model access")
	parser.add_argument(
		"--models",
		nargs="*",
		default=DEFAULT_MODELS,
		help="Model names to test",
	)
	return parser.parse_args()


def main() -> int:
	load_environment()
	args = parse_args()
	api_key = os.getenv("OPENAI_API_KEY")
	if not api_key:
		print("Missing OPENAI_API_KEY. Put it in backend/.env or export it in your shell.", file=sys.stderr)
		return 2

	client = OpenAI(api_key=api_key)
	failed = False

	for model in args.models:
		try:
			response = client.chat.completions.create(
				model=model,
				messages=[{"role": "user", "content": "Say hello in one short sentence."}],
			)
			text = response.choices[0].message.content or str(response)
			print(f"[OK] {model}: {text[:120]}")
		except Exception as exc:  # pragma: no cover - CLI reporting
			failed = True
			print(f"[FAIL] {model}: {exc}")

	return 1 if failed else 0


if __name__ == "__main__":
	raise SystemExit(main())
