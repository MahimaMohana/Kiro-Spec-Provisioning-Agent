#!/usr/bin/env python3

# ─────────────────────────────────────────────
# KSPA — Kiro Standards Provisioning Agent
# Core Python Agent
# ─────────────────────────────────────────────

import os
import sys
import json
import shutil
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIGURATION — Update these for Southwest
# ─────────────────────────────────────────────

CENTRAL_REPO_SSH   = "git@github.com:MahimaMohana/Kiro-Spec-Provisioning-Agent.git"
CENTRAL_REPO_LOCAL = Path.home() / ".kspa" / "standards-cache"
LOG_FILE_NAME      = ".kspa-log.json"

HOOKS_SOURCE       = CENTRAL_REPO_LOCAL / "hooks"
STEERING_SOURCE    = CENTRAL_REPO_LOCAL / "steering"

KIRO_HOOKS_DEST    = ".kiro/hooks"
KIRO_STEERING_DEST = ".kiro/steering"

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
# STEP 1 — Pull latest standards from GitLab
# ─────────────────────────────────────────────

def pull_latest_standards():
    print_step("📡", "Pulling latest standards from central repo...")

    if CENTRAL_REPO_LOCAL.exists():
        # Already cloned — just pull latest
        result = subprocess.run(
            ["git", "-C", str(CENTRAL_REPO_LOCAL), "pull", "--quiet"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print_warning("Could not pull latest — using cached version.")
    else:
        # First time — clone the repo
        CENTRAL_REPO_LOCAL.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", "--quiet", CENTRAL_REPO_SSH, str(CENTRAL_REPO_LOCAL)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print_error(f"Could not clone central repo: {result.stderr}")
            print_error("Check your GitLab SSH access and try again.")
            sys.exit(1)

    print_step("✓", "Standards cache is up to date.")

# ─────────────────────────────────────────────
# STEP 2 — Read version from central repo
# ─────────────────────────────────────────────

def get_standards_version():
    version_file = CENTRAL_REPO_LOCAL / "version.json"
    if version_file.exists():
        with open(version_file) as f:
            data = json.load(f)
            return data.get("version", "unknown")
    return "unknown"

# ─────────────────────────────────────────────
# STEP 3 — Check what already exists in repo
# ─────────────────────────────────────────────

def get_existing_files(repo_path, relative_dir):
    target = Path(repo_path) / relative_dir
    if not target.exists():
        return set()
    return {f.name for f in target.iterdir() if f.is_file()}

# ─────────────────────────────────────────────
# STEP 4 — Inject files (smart merge)
# ─────────────────────────────────────────────

def inject_files(repo_path, source_dir, dest_relative, label):
    injected = []
    skipped  = []

    dest_path = Path(repo_path) / dest_relative
    dest_path.mkdir(parents=True, exist_ok=True)

    if not source_dir.exists():
        print_warning(f"No {label} found in central repo — skipping.")
        return injected, skipped

    existing = get_existing_files(repo_path, dest_relative)

    for source_file in sorted(source_dir.iterdir()):
        if not source_file.is_file():
            continue

        if source_file.name in existing:
            # File already exists — do NOT overwrite
            skipped.append(source_file.name)
            print_step("⏭️ ", f"Skipped {label}: {source_file.name} (already exists)")
        else:
            # File doesn't exist — inject it
            shutil.copy2(source_file, dest_path / source_file.name)
            injected.append(source_file.name)
            print_step("💉", f"Injected {label}: {source_file.name}")

    return injected, skipped

# ─────────────────────────────────────────────
# STEP 5 — Write injection log
# ─────────────────────────────────────────────

def write_log(repo_path, version, hooks_injected, hooks_skipped,
              steering_injected, steering_skipped):

    log_path = Path(repo_path) / ".kiro" / LOG_FILE_NAME
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing log if present
    history = []
    if log_path.exists():
        with open(log_path) as f:
            try:
                existing = json.load(f)
                history = existing.get("history", [])
            except Exception:
                history = []

    # Add new entry
    entry = {
        "timestamp":         datetime.now().isoformat(),
        "standards_version": version,
        "hooks_injected":    hooks_injected,
        "hooks_skipped":     hooks_skipped,
        "steering_injected": steering_injected,
        "steering_skipped":  steering_skipped,
    }
    history.insert(0, entry)

    log_data = {
        "agent":   "KSPA — Kiro Standards Provisioning Agent",
        "repo":    str(repo_path),
        "history": history
    }

    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)

    print_step("📝", f"Injection log written to .kiro/{LOG_FILE_NAME}")

# ─────────────────────────────────────────────
# STEP 6 — Print summary
# ─────────────────────────────────────────────

def print_summary(version, hooks_injected, hooks_skipped,
                  steering_injected, steering_skipped):

    total_injected = len(hooks_injected) + len(steering_injected)
    total_skipped  = len(hooks_skipped)  + len(steering_skipped)

    print("")
    print("  ┌─────────────────────────────────────────┐")
    print("  │         KSPA Injection Summary           │")
    print("  ├─────────────────────────────────────────┤")
    print(f"  │  Standards version : {version:<20} │")
    print(f"  │  Hooks injected    : {len(hooks_injected):<20} │")
    print(f"  │  Steering injected : {len(steering_injected):<20} │")
    print(f"  │  Files skipped     : {total_skipped:<20} │")
    print("  └─────────────────────────────────────────┘")

    if total_injected > 0:
        print_success(f"Kiro standards provisioned! Open Kiro — you're ready to go.")
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

    # Step 1 — Pull latest standards
    pull_latest_standards()

    # Step 2 — Get version
    version = get_standards_version()
    print_step("📦", f"Standards version: {version}")

    # Step 3 — Inject hooks
    print_step("🔧", "Checking hooks...")
    hooks_injected, hooks_skipped = inject_files(
        repo_path, HOOKS_SOURCE, KIRO_HOOKS_DEST, "hook"
    )

    # Step 4 — Inject steering files
    print_step("🧭", "Checking steering files...")
    steering_injected, steering_skipped = inject_files(
        repo_path, STEERING_SOURCE, KIRO_STEERING_DEST, "steering"
    )

    # Step 5 — Write log
    write_log(
        repo_path, version,
        hooks_injected, hooks_skipped,
        steering_injected, steering_skipped
    )

    # Step 6 — Print summary
    print_summary(
        version,
        hooks_injected, hooks_skipped,
        steering_injected, steering_skipped
    )

if __name__ == "__main__":
    main()
