# KSPA — Kiro Standards Provisioning Agent

---

## What Is KSPA?

KSPA automatically provisions Kiro hooks, steering files, and skills into any repository the moment a developer checks out a branch — with zero manual setup required.

It injects two layers of standards:

| Layer | Source | Destination |
|---|---|---|
| **Common** | `common/hooks/<stack>/` | `.kiro/hooks/` |
| **Common** | `common/steering/common/` + `common/steering/<stack>/` | `.kiro/steering/` |
| **Product line** | `<product-line>/hooks/` | `.kiro/hooks/` |
| **Product line** | `<product-line>/steering/` | `.kiro/steering/` |
| **Product line** | `<product-line>/skills/` | `.kiro/agents/` |

---

## How It Works

```
Developer runs: git checkout branch
        ↓
post-checkout Git hook fires
        ↓
Detects stack (pom.xml → java, package.json → node, requirements.txt → python)
        ↓
Pulls / validates latest standards from central repo
        ↓
Injects common hooks + steering (stack-scoped)
        ↓
Detects product line from repo's origin URL
        ↓
Injects product-line hooks + steering + skills
        ↓
Developer opens Kiro — standards already there
```

---

## Central Repo Structure

```
Kiro-Spec-Provisioning-Agent/
│
├── common/                        # Coding-standard assets for all product lines
│   ├── hooks/
│   │   ├── java/
│   │   ├── node/
│   │   └── python/
│   └── steering/
│       ├── common/                # Shared across all stacks
│       ├── java/
│       ├── node/
│       └── python/
│
├── store-operations/              # Product-line assets
│   ├── hooks/
│   ├── steering/
│   └── skills/
│
├── data-and-platform/
│   ├── hooks/
│   ├── steering/
│   └── skills/
│
├── digital-commerce/
│   ├── hooks/
│   ├── steering/
│   └── skills/
│
├── merchandising-and-assortment/
│   ├── hooks/
│   ├── steering/
│   └── skills/
│
├── order-management/
│   ├── hooks/
│   ├── steering/
│   └── skills/
│
├── supply-chain-and-inventory/
│   ├── hooks/
│   ├── steering/
│   └── skills/
│
├── provisioning/
│   ├── hooks/
│   ├── steering/
│   └── skills/
│
├── kspa.py                        # Agent entry point
├── setup.sh                       # One-time developer setup
├── post-checkout                  # Git hook script
└── version.json
```

---

## Product Line Detection

KSPA reads the target repo's `origin` remote URL and matches it against
`PRODUCT_LINE_URL_MAP` in `kspa.py` using a longest-prefix check.

### Configuring a product line URL

Open `kspa.py` and find `PRODUCT_LINE_URL_MAP`. Each entry maps a normalised
host/group prefix to a product-line folder name:

```python
PRODUCT_LINE_URL_MAP: dict[str, str] = {
    # Replace the placeholder with the real GitLab/GitHub group prefix,
    # e.g. "gitlab.example.com/retail/store-ops/"
    "STORE_OPS_URL_PREFIX_PLACEHOLDER/": "store-operations",

    # Add the real prefix for each line when the URL is known:
    "__NO_MATCH__/data-and-platform":            "data-and-platform",
    ...
}
```

**Normalisation rules** — KSPA converts any remote URL format to
`host/group/` before matching:

| Raw URL | Normalised |
|---|---|
| `https://github.com/my-org/store-ops/my-repo.git` | `github.com/my-org/store-ops/` |
| `git@github.com:my-org/store-ops/my-repo.git` | `github.com/my-org/store-ops/` |
| `ssh://git@github.com/my-org/store-ops/my-repo` | `github.com/my-org/store-ops/` |

If no entry matches, KSPA sets the product line to `undetected`, injects only
common standards, and exits with code 0.

---

## Developer Setup (One Time Only)

```bash
git clone git@github.com:MahimaMohana/Kiro-Spec-Provisioning-Agent.git
cd Kiro-Spec-Provisioning-Agent
chmod +x setup.sh
./setup.sh
```

---

## Merge / Safety Rules

- KSPA writes only to `.kiro/hooks`, `.kiro/steering`, and `.kiro/agents`.
- It never overwrites an existing file (skips and logs instead).
- `.kiro/specs` and `.kiro/settings` are never touched.

---

## Injection Log

Every run appends an entry to `.kiro/.kspa-log.json`:

```json
{
  "agent": "KSPA — Kiro Standards Provisioning Agent",
  "repo": "/path/to/repo",
  "history": [
    {
      "timestamp": "2026-11-17T09:30:00",
      "standards_version": "1.0.0",
      "stack": "java",
      "product_line": "store-operations",
      "hooks_injected": ["fix-sonar-issues-post-task-hook.json"],
      "hooks_skipped": [],
      "steering_injected": ["java-coding-standards.md"],
      "steering_skipped": [],
      "skills_injected": [],
      "skills_skipped": []
    }
  ]
}
```

---

## Updating Standards

Push changes to this repo and update `version.json`. KSPA pulls the latest
automatically on every checkout — all developers stay current with no manual
action required.

---

## Designed By
**Mahima — Senior Software Engineer, AI Engineering**
