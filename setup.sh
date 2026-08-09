#!/bin/bash

# ─────────────────────────────────────────────
# KSPA — One-Time Setup Script
# Run this ONCE per developer machine
# Works on Mac and Windows (Git Bash)
# ─────────────────────────────────────────────

echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║   KSPA Setup — Kiro Standards Agent       ║"
echo "║   Southwest Airlines AI Engineering       ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# ── Step 1: Create KSPA home directory
echo "  📁  Creating KSPA directory..."
mkdir -p "$HOME/.kspa"

# ── Step 2: Copy agent script
echo "  📋  Installing KSPA agent..."
cp "$(dirname "$0")/kspa.py" "$HOME/.kspa/kspa.py"
chmod +x "$HOME/.kspa/kspa.py"

# ── Step 3: Set up Git template directory
echo "  🔧  Configuring Git template..."
mkdir -p "$HOME/.git-templates/hooks"
cp "$(dirname "$0")/post-checkout" "$HOME/.git-templates/hooks/post-checkout"
chmod +x "$HOME/.git-templates/hooks/post-checkout"

# ── Step 4: Configure Git to use template globally
git config --global init.templateDir "$HOME/.git-templates"

# ── Step 5: Verify Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo ""
    echo "  ⚠️   Python 3 not found. Please install Python 3 and re-run this script."
    echo "      Download: https://www.python.org/downloads/"
    exit 1
fi

echo "  ✅  Python 3 found: $(python3 --version)"

# ── Step 6: Test SSH access to GitHub
echo "  🔐  Testing GitHub SSH access..."
ssh -T git@github.com -o ConnectTimeout=5 2>&1 | grep -q "Hi"
if [ $? -eq 0 ]; then
    echo "  ✅  GitHub SSH access confirmed."
else
    echo "  ⚠️   Could not verify GitHub SSH — make sure your SSH key is configured."
    echo "      Run: ssh -T git@github.com"
fi

echo ""
echo "  ┌─────────────────────────────────────────┐"
echo "  │         KSPA Setup Complete ✅           │"
echo "  ├─────────────────────────────────────────┤"
echo "  │  From now on, every Java repo you        │"
echo "  │  check out will automatically get        │"
echo "  │  Kiro hooks and steering files.          │"
echo "  │                                          │"
echo "  │  You don't need to do anything else.     │"
echo "  └─────────────────────────────────────────┘"
echo ""
