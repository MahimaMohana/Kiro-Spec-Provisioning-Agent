#!/usr/bin/env python3

# ─────────────────────────────────────────────
# KSPA — Kiro Standards Provisioning Agent
# Core Python Agent
# ─────────────────────────────────────────────

import re
import sys
import json
import shutil
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

CENTRAL_REPO_SSH   = "git@github.com:MahimaMohana/Kiro-Spec-Provisioning-Agent.git"
CENTRAL_REPO_LOCAL = Path.home() / ".kspa" / "standards-cache"
LOG_FILE_NAME      = ".kspa-log.json"

# Derived source roots inside the cache
COMMON_SOURCE      = CENTRAL_REPO_LOCAL / "common"
COMMON_HOOKS_ROOT  = COMMON_SOURCE / "hooks"           # common/hooks/<stack>/
COMMON_STEERING_COMMON = COMMON_SOURCE / "steering" / "common"  # common/steering/common/
COMMON_STEERING_STACK  = COMMON_SOURCE / "steering"    # common/steering/<stack>/

# Product-line source roots — each lives at <product_line>/
PRODUCT_LINE_ROOT  = CENTRAL_REPO_LOCAL               # <product_line>/hooks|steering|skills

# Destination folders inside the target repo
KIRO_HOOKS_DEST    = ".kiro/hooks"
KIRO_STEERING_DEST = ".kiro/steering"
KIRO_AGENTS_DEST   = ".kiro/agents"       # skills land here

# Maps stack identifiers to the subfolder used in common/hooks/ and common/steering/
LANGUAGE_SUBFOLDERS = {
    "java":   "java",
    "python": "python",
    "node":   "node",
}

# ─────────────────────────────────────────────
# PRODUCT LINE URL MAP
#
# Key   : normalised host+group prefix, e.g. "github.com/my-org/store-ops-group/"
#         KSPA strips scheme, "git@", the colon in scp-style URLs, ".git" suffix,
#         and the repo name before matching.
#         Use the RESERVED sentinel "__NO_MATCH__" for lines not yet configured —
#         that value can never appear in a real URL so it will never match.
#
# Value : folder name under CENTRAL_REPO_LOCAL that holds the product-line
#         hooks/, steering/, and skills/ sub-directories.
# ─────────────────────────────────────────────

_RESERVED = "__NO_MATCH__"

PRODUCT_LINE_URL_MAP: dict[str, str] = {
    # ── Configured ────────────────────────────────────────────────────────────
    # All repos under github.com/MahimaMohana/ map to the store-operations
    # product line for testing. Update to the real org/group prefix in production.
    "github.com/MahimaMohana/": "store-operations",

    # ── Reserved — update URL prefix when group is known ─────────────────────
    _RESERVED + "/data-and-platform":              "data-and-platform",
    _RESERVED + "/digital-commerce":               "digital-commerce",
    _RESERVED + "/merchandising-and-assortment":   "merchandising-and-assortment",
    _RESERVED + "/order-management":               "order-management",
    _RESERVED + "/supply-chain-and-inventory":     "supply-chain-and-inventory",
    _RESERVED + "/provisioning":                   "provisioning",
}

# ─────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────

def print_step(emoji, message):
    print(f"  {emoji}  {message}")

def print_success(message):
    print(f"\n  ✅  {message}\n")

def print_warning(message):
    print(f"  ⚠️   {message}")

def print_error(message):
    print(f"  ❌  {message}")

# ─────────────────────────────────────────────
# STEP 1 — Pull / validate standards cache
# ─────────────────────────────────────────────

def _cache_is_complete() -> bool:
    """Return True only if both common/hooks and common/steering exist in the cache."""
    return (CENTRAL_REPO_LOCAL / "common" / "hooks").exists() and \
           (CENTRAL_REPO_LOCAL / "common" / "steering").exists()

def pull_latest_standards():
    print_step("📡", "Pulling latest standards from central repo...")

    if CENTRAL_REPO_LOCAL.exists():
        if not _cache_is_complete():
            print_warning("Cache is incomplete — deleting and re-cloning.")
            shutil.rmtree(CENTRAL_REPO_LOCAL)
        else:
            result = subprocess.run(
                ["git", "-C", str(CENTRAL_REPO_LOCAL), "pull", "--quiet"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print_warning("Could not pull latest — using cached version.")
            print_step("✓", "Standards cache is up to date.")
            return

    # Clone fresh
    CENTRAL_REPO_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "clone", "--quiet", CENTRAL_REPO_SSH, str(CENTRAL_REPO_LOCAL)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print_error(f"Could not clone central repo: {result.stderr}")
        print_error("Check your GitHub SSH access and try again.")
        sys.exit(1)

    if not _cache_is_complete():
        print_error("Clone succeeded but cache is still incomplete (common/hooks or common/steering missing).")
        print_error("KSPA cannot continue with a partial cache.")
        shutil.rmtree(CENTRAL_REPO_LOCAL, ignore_errors=True)
        sys.exit(1)

    print_step("✓", "Standards cloned successfully.")

# ─────────────────────────────────────────────
# STEP 2 — Read version from central repo
# ─────────────────────────────────────────────

def get_standards_version() -> str:
    version_file = CENTRAL_REPO_LOCAL / "version.json"
    if version_file.exists():
        with open(version_file) as f:
            data = json.load(f)
            return data.get("version", "unknown")
    return "unknown"

# ─────────────────────────────────────────────
# STEP 3 — Detect stack (language) from repo root
# ─────────────────────────────────────────────

def detect_stack(repo_path: Path) -> str:
    """Return 'java', 'python', 'node', or 'unknown'."""
    if (repo_path / "pom.xml").exists() or \
       (repo_path / "build.gradle").exists() or \
       (repo_path / "build.gradle.kts").exists():
        return "java"

    if (repo_path / "requirements.txt").exists() or \
       (repo_path / "pyproject.toml").exists() or \
       (repo_path / "setup.py").exists() or \
       (repo_path / "setup.cfg").exists():
        return "python"

    if (repo_path / "package.json").exists():
        return "node"

    return "unknown"

# ─────────────────────────────────────────────
# STEP 4 — Detect product line from origin URL
# ─────────────────────────────────────────────

def get_origin_url(repo_path: Path) -> str | None:
    """Return the raw origin remote URL, or None on any failure."""
    result = subprocess.run(
        ["git", "-C", str(repo_path), "remote", "get-url", "origin"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def normalize_origin_url(raw_url: str) -> str:
    """
    Reduce a raw git remote URL to a comparable 'host/group/…/' form.

    Handles:
      https://github.com/my-org/my-group/my-repo.git  → github.com/my-org/my-group/
      git@github.com:my-org/my-group/my-repo.git      → github.com/my-org/my-group/
      ssh://git@github.com/my-org/my-group/my-repo    → github.com/my-org/my-group/

    The repo name (last path segment) is stripped so that the URL map entries
    describe group prefixes, not individual repos.
    """
    url = raw_url.strip()

    # Remove scheme (https://, ssh://, git://)
    url = re.sub(r'^[a-zA-Z][a-zA-Z0-9+\-.]*://', '', url)

    # Remove git@ or any user@ prefix
    url = re.sub(r'^[^@/]+@', '', url)

    # Convert scp-style colon separator to slash: host:path → host/path
    url = url.replace(':', '/', 1)

    # Drop .git suffix
    url = re.sub(r'\.git$', '', url)

    # Drop the last path segment (the repo name itself) so we're left with the group
    parts = url.rstrip('/').split('/')
    if len(parts) > 1:
        url = '/'.join(parts[:-1]) + '/'
    else:
        url = url.rstrip('/') + '/'

    return url


def detect_product_line(repo_path: Path) -> str:
    """
    Return the product-line folder name, or 'undetected'.

    Matching rules:
    - Normalise the origin URL to host/group/ form.
    - Case-sensitive prefix check against PRODUCT_LINE_URL_MAP keys.
    - If multiple keys match, the longest key wins.
    - _RESERVED sentinel values can never match a real URL.
    """
    raw_url = get_origin_url(repo_path)
    if not raw_url:
        print_warning("No origin remote found — product line set to undetected.")
        return "undetected"

    try:
        normalised = normalize_origin_url(raw_url)
    except Exception:
        print_warning(f"Could not parse origin URL '{raw_url}' — product line set to undetected.")
        return "undetected"

    print_step("🌐", f"Origin URL (normalised): {normalised}")

    # Longest-prefix match (excludes reserved sentinel entries)
    best_key   = None
    best_match = None
    for key, product_line in PRODUCT_LINE_URL_MAP.items():
        if _RESERVED in key:          # skip unconfigured placeholders
            continue
        if normalised.startswith(key):
            if best_key is None or len(key) > len(best_key):
                best_key   = key
                best_match = product_line

    if best_match:
        return best_match

    print_warning(f"Origin URL '{normalised}' did not match any configured product line — set to undetected.")
    return "undetected"

# ─────────────────────────────────────────────
# STEP 5 — Inject files (generic, flat copy)
# ─────────────────────────────────────────────

def inject_files(repo_path: Path, source_dir: Path, dest_relative: str, label: str):
    """
    Copy every non-dotfile from source_dir into dest_relative (flat).
    Returns (injected_list, skipped_list).
    """
    injected: list[str] = []
    skipped:  list[str] = []

    if not source_dir.exists():
        print_step("ℹ️ ", f"No {label} source at {source_dir} — skipping.")
        return injected, skipped

    source_files = sorted(
        f for f in source_dir.iterdir()
        if f.is_file() and not f.name.startswith(".")
    )

    if not source_files:
        print_step("ℹ️ ", f"No {label} files in {source_dir} — skipping.")
        return injected, skipped

    dest_path = repo_path / dest_relative
    if not dest_path.exists():
        dest_path.mkdir(parents=True, exist_ok=True)
        print_step("📁", f"Created folder: {dest_relative}")

    for source_file in source_files:
        target_file = dest_path / source_file.name
        if target_file.exists():
            skipped.append(source_file.name)
            print_step("⏭️ ", f"Skipped {label}: {source_file.name} (already exists)")
        else:
            shutil.copy2(source_file, target_file)
            injected.append(source_file.name)
            print_step("💉", f"Injected {label}: {source_file.name}")

    return injected, skipped

# ─────────────────────────────────────────────
# STEP 6 — Write injection log
# ─────────────────────────────────────────────

def write_log(repo_path: Path, version: str, stack: str, product_line: str,
              hooks_injected, hooks_skipped,
              steering_injected, steering_skipped,
              skills_injected, skills_skipped):

    log_path = repo_path / ".kiro" / LOG_FILE_NAME
    log_path.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if log_path.exists():
        with open(log_path) as f:
            try:
                existing = json.load(f)
                history  = existing.get("history", [])
            except Exception:
                history  = []

    entry = {
        "timestamp":         datetime.now().isoformat(),
        "standards_version": version,
        "stack":             stack,
        "product_line":      product_line,
        "hooks_injected":    hooks_injected,
        "hooks_skipped":     hooks_skipped,
        "steering_injected": steering_injected,
        "steering_skipped":  steering_skipped,
        "skills_injected":   skills_injected,
        "skills_skipped":    skills_skipped,
    }
    history.insert(0, entry)

    log_data = {
        "agent":   "KSPA — Kiro Standards Provisioning Agent",
        "repo":    str(repo_path),
        "history": history,
    }

    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)

    print_step("📝", f"Injection log written to .kiro/{LOG_FILE_NAME}")

# ─────────────────────────────────────────────
# STEP 7 — Print summary
# ─────────────────────────────────────────────

def print_summary(version: str, stack: str, product_line: str,
                  hooks_injected, hooks_skipped,
                  steering_injected, steering_skipped,
                  skills_injected, skills_skipped):

    total_injected = len(hooks_injected) + len(steering_injected) + len(skills_injected)
    total_skipped  = len(hooks_skipped)  + len(steering_skipped)  + len(skills_skipped)

    print("")
    print("  ┌─────────────────────────────────────────┐")
    print("  │         KSPA Injection Summary           │")
    print("  ├─────────────────────────────────────────┤")
    print(f"  │  Standards version : {version:<20} │")
    print(f"  │  Stack             : {stack:<20} │")
    print(f"  │  Product line      : {product_line:<20} │")
    print(f"  │  Hooks injected    : {len(hooks_injected):<20} │")
    print(f"  │  Steering injected : {len(steering_injected):<20} │")
    print(f"  │  Skills injected   : {len(skills_injected):<20} │")
    print(f"  │  Files skipped     : {total_skipped:<20} │")
    print("  └─────────────────────────────────────────┘")

    if total_injected > 0:
        print_success("Kiro standards provisioned! Open Kiro — you're ready to go.")
    else:
        print_step("ℹ️ ", "All standards already present — no changes made.")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="KSPA — Kiro Standards Provisioning Agent")
    parser.add_argument("--repo", required=True, help="Path to the checked-out repository")
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()

    if not repo_path.exists():
        print_error(f"Repo path not found: {repo_path}")
        sys.exit(1)

    # ── Step 1: Pull / validate cache ───────────────────────────────────────
    pull_latest_standards()

    # ── Step 2: Standards version ───────────────────────────────────────────
    version = get_standards_version()
    print_step("📦", f"Standards version: {version}")

    # ── Step 3: Detect stack ────────────────────────────────────────────────
    stack = detect_stack(repo_path)
    if stack == "unknown":
        print_warning("Could not detect stack (no pom.xml, package.json, or requirements.txt). Skipping injection.")
        sys.exit(0)

    lang_folder = LANGUAGE_SUBFOLDERS[stack]
    print_step("🔍", f"Detected stack: {stack} → using '{lang_folder}/' subfolder")

    # ── Step 4: Detect product line ─────────────────────────────────────────
    product_line = detect_product_line(repo_path)
    print_step("🏷️ ", f"Product line: {product_line}")

    # ── Step 5a: Inject common hooks (common/hooks/<stack>/) ─────────────────
    print_step("🔧", "Injecting common hooks...")
    h_inj, h_skip = inject_files(
        repo_path,
        COMMON_HOOKS_ROOT / lang_folder,
        KIRO_HOOKS_DEST,
        "common hook"
    )

    # ── Step 5b: Inject common steering — shared + stack-specific ─────────────
    print_step("🧭", "Injecting common steering...")
    # common/steering/common/ first …
    s_inj, s_skip = inject_files(
        repo_path,
        COMMON_STEERING_COMMON,
        KIRO_STEERING_DEST,
        "common steering"
    )
    # … then common/steering/<stack>/
    s_inj2, s_skip2 = inject_files(
        repo_path,
        COMMON_STEERING_STACK / lang_folder,
        KIRO_STEERING_DEST,
        f"{stack} steering"
    )
    s_inj  += s_inj2
    s_skip += s_skip2

    # ── Step 5c: Inject product-line hooks + steering + skills ───────────────
    sk_inj:  list[str] = []
    sk_skip: list[str] = []

    if product_line != "undetected":
        pl_root = PRODUCT_LINE_ROOT / product_line

        print_step("🏷️ ", f"Injecting product-line hooks from '{product_line}/hooks/'...")
        pl_h_inj, pl_h_skip = inject_files(
            repo_path,
            pl_root / "hooks",
            KIRO_HOOKS_DEST,
            f"{product_line} hook"
        )
        h_inj  += pl_h_inj
        h_skip += pl_h_skip

        print_step("🏷️ ", f"Injecting product-line steering from '{product_line}/steering/'...")
        pl_s_inj, pl_s_skip = inject_files(
            repo_path,
            pl_root / "steering",
            KIRO_STEERING_DEST,
            f"{product_line} steering"
        )
        s_inj  += pl_s_inj
        s_skip += pl_s_skip

        print_step("🧩", f"Injecting product-line skills from '{product_line}/skills/'...")
        sk_inj, sk_skip = inject_files(
            repo_path,
            pl_root / "skills",
            KIRO_AGENTS_DEST,
            f"{product_line} skill"
        )
    else:
        print_step("ℹ️ ", "No product line detected — skipping product-line injection.")

    # ── Step 6: Write log ───────────────────────────────────────────────────
    write_log(
        repo_path, version, stack, product_line,
        h_inj, h_skip,
        s_inj, s_skip,
        sk_inj, sk_skip,
    )

    # ── Step 7: Summary ─────────────────────────────────────────────────────
    print_summary(
        version, stack, product_line,
        h_inj, h_skip,
        s_inj, s_skip,
        sk_inj, sk_skip,
    )


if __name__ == "__main__":
    main()
