#!/usr/bin/env python3

# ─────────────────────────────────────────────
# KSPA — Kiro Standards Provisioning Agent
# Core Python Agent
# ─────────────────────────────────────────────

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

HOOKS_SOURCE       = CENTRAL_REPO_LOCAL / "hooks"
STEERING_SOURCE    = CENTRAL_REPO_LOCAL / "steering"

KIRO_HOOKS_DEST    = ".kiro/hooks"
KIRO_STEERING_DEST = ".kiro/steering"

# Maps project type to the subfolder name used in hooks/ and steering/
LANGUAGE_SUBFOLDERS = {
    "java":   "java",
    "python": "python",
    "node":   "node",
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
# STEP 1 — Pull latest standards from GitHub
# ─────────────────────────────────────────────

def pull_latest_standards():
    print_step("📡", "Pulling latest standards from central repo...")

    if CENTRAL_REPO_LOCAL.exists():
        result = subprocess.run(
            ["git", "-C", str(CENTRAL_REPO_LOCAL), "pull", "--quiet"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print_warning("Could not pull latest — using cached version.")
    else:
        CENTRAL_REPO_LOCAL.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", "--quiet", CENTRAL_REPO_SSH, str(CENTRAL_REPO_LOCAL)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print_error(f"Could not clone central repo: {result.stderr}")
            print_error("Check your GitHub SSH access and try again.")
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
# STEP 3 — Detect project type from repo root
# ─────────────────────────────────────────────

def detect_project_type(repo_path: Path) -> str:
    """Return 'java', 'python', 'node', or raise if unrecognised."""
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
# STEP 4 — Inject files (language-scoped, flat)
# ─────────────────────────────────────────────

def inject_files(repo_path: Path, source_dir: Path, dest_relative: str, label: str):
    """
    Copy files from source_dir directly into dest_relative (flat).
    source_dir should already be the language-specific subfolder,
    e.g. hooks/java/ or steering/java/ — no subdirectory structure
    is created inside the destination.
    """
    injected = []
    skipped  = []

    dest_path = repo_path / dest_relative

    if not source_dir.exists():
        print_warning(f"No {label} source folder found at {source_dir} — skipping.")
        return injected, skipped

    # Collect only files (skip .gitkeep and other dot-files)
    source_files = sorted(
        f for f in source_dir.iterdir()
        if f.is_file() and not f.name.startswith(".")
    )

    if not source_files:
        print_warning(f"No {label} files found in {source_dir} — skipping.")
        return injected, skipped

    # Only create the destination folder if there are real files to inject
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
# STEP 5 — Write injection log
# ─────────────────────────────────────────────

def write_log(repo_path, version, project_type, hooks_injected, hooks_skipped,
              steering_injected, steering_skipped):

    log_path = repo_path / ".kiro" / LOG_FILE_NAME
    log_path.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if log_path.exists():
        with open(log_path) as f:
            try:
                existing = json.load(f)
                history = existing.get("history", [])
            except Exception:
                history = []

    entry = {
        "timestamp":         datetime.now().isoformat(),
        "standards_version": version,
        "project_type":      project_type,
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

def print_summary(version, project_type, hooks_injected, hooks_skipped,
                  steering_injected, steering_skipped):

    total_injected = len(hooks_injected) + len(steering_injected)
    total_skipped  = len(hooks_skipped)  + len(steering_skipped)

    print("")
    print("  ┌─────────────────────────────────────────┐")
    print("  │         KSPA Injection Summary           │")
    print("  ├─────────────────────────────────────────┤")
    print(f"  │  Standards version : {version:<20} │")
    print(f"  │  Project type      : {project_type:<20} │")
    print(f"  │  Hooks injected    : {len(hooks_injected):<20} │")
    print(f"  │  Steering injected : {len(steering_injected):<20} │")
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

    # Step 1 — Pull latest standards
    pull_latest_standards()

    # Step 2 — Get version
    version = get_standards_version()
    print_step("📦", f"Standards version: {version}")

    # Step 3 — Detect project type
    project_type = detect_project_type(repo_path)
    if project_type == "unknown":
        print_warning("Could not detect project type — no pom.xml, package.json, or requirements.txt found. Skipping injection.")
        sys.exit(0)

    lang_folder = LANGUAGE_SUBFOLDERS[project_type]
    print_step("🔍", f"Detected project type: {project_type} → injecting from '{lang_folder}/' subfolder only")

    # Step 4 — Inject hooks from language subfolder only
    print_step("🔧", "Checking hooks...")
    hooks_injected, hooks_skipped = inject_files(
        repo_path, HOOKS_SOURCE / lang_folder, KIRO_HOOKS_DEST, "hook"
    )

    # Step 5 — Inject steering files from language subfolder only
    print_step("🧭", "Checking steering files...")
    steering_injected, steering_skipped = inject_files(
        repo_path, STEERING_SOURCE / lang_folder, KIRO_STEERING_DEST, "steering"
    )

    # Step 6 — Write log
    write_log(
        repo_path, version, project_type,
        hooks_injected, hooks_skipped,
        steering_injected, steering_skipped
    )

    # Step 7 — Print summary
    print_summary(
        version, project_type,
        hooks_injected, hooks_skipped,
        steering_injected, steering_skipped
    )

if __name__ == "__main__":
    main()
