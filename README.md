# KSPA — Kiro Standards Provisioning Agent
### Southwest Airlines AI Engineering

---

## What Is KSPA?

KSPA automatically provisions Kiro hooks and steering files into every Java repository the moment a developer checks out a branch — with zero manual setup required.

---

## How It Works

```
Developer runs: git checkout branch
        ↓
post-checkout Git hook fires
        ↓
Detects Java project (pom.xml / build.gradle)
        ↓
Pulls latest standards from central GitLab repo
        ↓
Injects hooks + steering files into .kiro/
        ↓
Developer opens Kiro — standards already there
```

---

## Central Repo Structure

```
Kiro-Spec-Provisioning-Agent/
├── hooks/
│   ├── unit-test-gen.md
│   ├── changelog.md
│   ├── impact-analysis.md
│   ├── readme-update.md
│   └── sonarqube-healing.md
├── steering/
│   ├── coding-standards.md
│   └── spec-integrity.md
└── version.json
```

---

## Developer Setup (One Time Only)

```bash
# Clone this repo
git clone git@github.com:MahimaMohana/Kiro-Spec-Provisioning-Agent.git

# Run setup script
cd Kiro-Spec-Provisioning-Agent
chmod +x setup.sh
./setup.sh
```

That's it. Every Java repo you check out from now on will automatically get Kiro standards.

---

## Merge Logic

KSPA never overwrites existing files:

| Scenario | What KSPA Does |
|---|---|
| No `.kiro/` folder exists | Clean inject — copies everything |
| `.kiro/` exists, no conflicts | Adds new files, leaves existing untouched |
| File already exists in repo | Skips it — never overwrites custom work |

---

## Injection Log

Every run writes a log to `.kiro/.kspa-log.json`:

```json
{
  "agent": "KSPA — Kiro Standards Provisioning Agent",
  "repo": "/path/to/repo",
  "history": [
    {
      "timestamp": "2026-05-10T09:30:00",
      "standards_version": "1.0.0",
      "hooks_injected": ["unit-test-gen.md", "changelog.md"],
      "hooks_skipped": [],
      "steering_injected": ["coding-standards.md"],
      "steering_skipped": []
    }
  ]
}
```

---

## Updating Standards

When you update hooks or steering files in this repo:
- Push changes + update `version.json`
- KSPA pulls latest automatically on next checkout
- All developers stay current with zero manual action

---

## Designed By
**Mahima — Senior Software Engineer, Southwest Airlines AI Engineering**

*Part of the Southwest Airlines Developer Intelligence Initiative*
