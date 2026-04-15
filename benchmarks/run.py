#!/usr/bin/env python3
"""
snaf benchmark — porównanie zużycia tokenów: bez pluginu (--bare) vs snaf plugin

Używa claude CLI z --plugin-dir dla realnej aktywacji pluginu przez SessionStart hook.
Multi-turn: wykrywa pytania w odpowiedzi i kontynuuje sesję przez --resume.

Użycie:
    python3 run.py                          # pełny benchmark, model haiku
    python3 run.py --model sonnet           # inny model
    python3 run.py --prompt react-rerender  # jeden prompt
    python3 run.py --dry-run               # tylko sprawdź konfigurację

Wymaga:
    pip3 install tiktoken --break-system-packages
    claude CLI zalogowany (claude login)
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

try:
    import tiktoken
except ImportError:
    print("Brakuje tiktoken. Uruchom: pip3 install tiktoken --break-system-packages")
    sys.exit(1)

BENCHMARKS_DIR = Path(__file__).parent
PROMPTS_FILE = BENCHMARKS_DIR / "prompts.json"
RESULTS_DIR = BENCHMARKS_DIR / "results"
SNAF_ROOT = BENCHMARKS_DIR.parent  # katalog główny pluginu snaf

DEFAULT_MODEL = "haiku"
MAX_TURNS = 4


def check_deps():
    if not shutil.which("claude"):
        print("Nie znaleziono 'claude' CLI. Zainstaluj Claude Code.")
        sys.exit(1)
    if not (SNAF_ROOT / ".claude-plugin" / "plugin.json").exists():
        print(f"Nie znaleziono pluginu snaf w: {SNAF_ROOT}")
        sys.exit(1)


def load_prompts():
    with open(PROMPTS_FILE) as f:
        return json.load(f)["prompts"]


def strip_insight_blocks(text: str) -> str:
    """Usuń bloki ★ Insight dodawane przez learning-output-style plugin."""
    return re.sub(r'`★ Insight\s*─+`[\s\S]*?`─+`', '', text).strip()


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(strip_insight_blocks(text)))


def is_asking_question(text: str) -> bool:
    """Wykryj czy odpowiedź pyta o coś zamiast odpowiadać."""
    stripped = text.strip()
    text_no_code = re.sub(r'```[\s\S]*?```', '', stripped)
    text_no_code = re.sub(r'`[^`\n]*`', '', text_no_code)

    lines = [l.strip() for l in text_no_code.split("\n") if l.strip()]
    if not lines:
        return False
    last_line = lines[-1]
    if last_line.endswith("?") and not last_line.startswith(("#", "-", "*")):
        return True
    if len(text_no_code.strip()) < 150 and "?" in text_no_code:
        return True
    return False


def call_claude(
    prompt: str,
    model: str,
    session_id: str,
    resume: bool = False,
    with_plugin: bool = False,
) -> str:
    cmd = [
        "claude", "-p",
        "--model", model,
        "--output-format", "text",
        "--permission-mode", "bypassPermissions",
    ]

    if resume:
        cmd += ["--resume", session_id]
    else:
        cmd += ["--session-id", session_id]

    cmd.append(prompt)

    # Baseline: SNAF_DEFAULT_MODE=off wyłącza hook aktywacji — snaf jest globalnie
    # zainstalowany, ale nie wstrzykuje reguł. Snaf: normalnie (mode=on).
    env = None
    if not with_plugin:
        import os
        env = {**os.environ, "SNAF_DEFAULT_MODE": "off"}

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI błąd:\n{result.stderr.strip()}")
    return result.stdout.strip()


def run_conversation(
    prompt: str, model: str, with_plugin: bool, label: str
) -> tuple[int, list[dict]]:
    """
    Przeprowadź potencjalnie wieloturową rozmowę.
    Zwraca: (suma tokenów wyjściowych, lista tur)
    """
    session_id = str(uuid.uuid4())
    turns = []
    total_tokens = 0

    # Tura 1
    response = call_claude(prompt, model, session_id, resume=False, with_plugin=with_plugin)
    tok = count_tokens(response)
    turns.append({"turn": 1, "response": response, "tokens": tok, "was_question": False})
    total_tokens += tok

    # Kolejne tury jeśli odpowiedź pyta o więcej info
    for turn_num in range(2, MAX_TURNS + 1):
        if not is_asking_question(turns[-1]["response"]):
            break

        turns[-1]["was_question"] = True
        follow_up = "Nie pytaj — zrób założenie typowego przypadku i odpowiedz bezpośrednio."
        time.sleep(0.5)

        response = call_claude(follow_up, model, session_id, resume=True, with_plugin=with_plugin)
        tok = count_tokens(response)
        turns.append({"turn": turn_num, "response": response, "tokens": tok, "was_question": False})
        total_tokens += tok

    return total_tokens, turns


def print_table(rows: list[dict], model: str):
    title = f"WYNIKI BENCHMARK — snaf plugin vs baseline  (model: {model})"
    print(f"\n{'='*85}")
    print(f"  {title}")
    print(f"{'='*85}")
    print(f"{'Prompt':<28} {'Kategoria':<16} {'Baseline':>9} {'Snaf':>7} {'Oszczędność':>12} {'Tury b/s':>9}")
    print(f"{'-'*28} {'-'*16} {'-'*9} {'-'*7} {'-'*12} {'-'*9}")

    total_base = total_snaf = 0
    by_category: dict[str, list[float]] = {}

    for row in rows:
        saving = (1 - row["snaf"] / row["base"]) * 100 if row["base"] > 0 else 0
        turns = f"{row['base_turns']}/{row['snaf_turns']}"
        marker = "▲" if saving < 0 else ""
        print(
            f"{row['id']:<28} {row['category']:<16} {row['base']:>9} {row['snaf']:>7} "
            f"{saving:>10.1f}%{marker:>1} {turns:>9}"
        )
        total_base += row["base"]
        total_snaf += row["snaf"]
        by_category.setdefault(row["category"], []).append(saving)

    total_saving = (1 - total_snaf / total_base) * 100 if total_base > 0 else 0
    print(f"{'-'*28} {'-'*16} {'-'*9} {'-'*7} {'-'*12} {'-'*9}")
    print(f"{'RAZEM':<28} {'':<16} {total_base:>9} {total_snaf:>7} {total_saving:>11.1f}%")

    print(f"\n{'='*60}")
    print("  WG KATEGORII")
    print(f"{'='*60}")
    print(f"{'Kategoria':<20} {'Promptów':>9} {'Avg oszczędność':>16}")
    print(f"{'-'*20} {'-'*9} {'-'*16}")
    for cat, savings in sorted(by_category.items(), key=lambda x: -sum(x[1]) / len(x[1])):
        avg = sum(savings) / len(savings)
        bar = "█" * max(0, int(avg / 5))
        neg = " ▲ REGRESJA" if avg < 0 else ""
        print(f"{cat:<20} {len(savings):>9} {avg:>15.1f}%  {bar}{neg}")


def run_benchmark(model: str, prompt_filter: str | None = None, limit: int | None = None):
    prompts = load_prompts()
    if prompt_filter:
        prompts = [p for p in prompts if p["id"] == prompt_filter]
        if not prompts:
            print(f"Nie znaleziono promptu: {prompt_filter}")
            sys.exit(1)
    if limit:
        prompts = prompts[:limit]

    print(f"\nModel: {model}  |  Promptów: {len(prompts)}")
    print(f"Plugin: {SNAF_ROOT}")
    print(f"Baseline: SNAF_DEFAULT_MODE=off (snaf zainstalowany ale nieaktywny)\n")

    rows = []

    for p in prompts:
        print(f"  → {p['id']}")

        print(f"      baseline...", end="", flush=True)
        base_tokens, base_turns = run_conversation(p["prompt"], model, with_plugin=False, label="base")
        print(f" {base_tokens} tok ({len(base_turns)} tur)")
        time.sleep(1)

        print(f"      snaf...   ", end="", flush=True)
        snaf_tokens, snaf_turns = run_conversation(p["prompt"], model, with_plugin=True, label="snaf")
        saving = (1 - snaf_tokens / base_tokens) * 100 if base_tokens > 0 else 0
        print(f" {snaf_tokens} tok ({len(snaf_turns)} tur)  →  {saving:.1f}%")
        time.sleep(1)

        rows.append({
            "id": p["id"],
            "category": p["category"],
            "base": base_tokens,
            "snaf": snaf_tokens,
            "base_turns": len(base_turns),
            "snaf_turns": len(snaf_turns),
            "base_detail": base_turns,
            "snaf_detail": snaf_turns,
        })

    print_table(rows, model)

    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"benchmark_{int(time.time())}.json"
    # Pełne dane z tekstami odpowiedzi
    out.write_text(json.dumps({"model": model, "results": rows}, indent=2, ensure_ascii=False))
    print(f"\nWyniki zapisane: {out}")


def main():
    parser = argparse.ArgumentParser(description="snaf benchmark — plugin vs baseline")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model: haiku, sonnet (domyślnie: haiku)")
    parser.add_argument("--prompt", help="ID konkretnego promptu (test pojedynczego)")
    parser.add_argument("--limit", type=int, help="Ogranicz do N pierwszych promptów")
    parser.add_argument("--dry-run", action="store_true", help="Sprawdź konfigurację bez uruchamiania")
    args = parser.parse_args()

    check_deps()

    if args.dry_run:
        print(f"✓ claude CLI: {shutil.which('claude')}")
        print(f"✓ snaf plugin: {SNAF_ROOT / '.claude-plugin' / 'plugin.json'}")
        print(f"✓ prompts: {PROMPTS_FILE} ({len(load_prompts())} promptów)")
        print(f"  model: {args.model}")
        return

    print(f"Backend: claude CLI (subskrypcja Claude Code)")
    run_benchmark(args.model, args.prompt, args.limit)


if __name__ == "__main__":
    main()
