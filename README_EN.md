# First-Love.skill

> "If memory had a shape, it would be the first second you looked at them."

**Distill your first love into an AI Skill you can actually talk to.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-green)](https://agentskills.io)

Provide source materials (chat logs, photos, social posts) plus your own recollection,
and generate an **AI Skill that really sounds like them** —
with their rhythm, their way of replying, and your brightest shared moments.

⚠️ **For personal reflection only. Not for harassment, stalking, impersonation, or privacy invasion.**

[Installation](#installation) · [Usage](#usage) · [Examples](#examples) · [Features](#features) · [Project Structure](#project-structure) · [中文](README.md)

---

## Installation

### Claude Code

> **Important**: Claude Code loads skills from `.claude/skills/` at the git repository root.

```bash
# Install to current project (recommended)
mkdir -p .claude/skills
git clone https://github.com/<your-username>/first-love-skill .claude/skills/create-first-love

# Or install globally (available in all projects)
git clone https://github.com/<your-username>/first-love-skill ~/.claude/skills/create-first-love
```

### Dependencies (Optional)

```bash
pip3 install -r requirements.txt
```

---

## Usage

In Claude Code, type:

```text
/create-first-love
```

Then go through the flow:

1. Relationship anchors (how you met, stage, key locations)
2. Spark memories (first sight, first deep conversation, first clear heartbeat)
3. Interaction profile (speech style, emotional reactions, boundaries)
4. Source import (WeChat / QQ / social media / photos / narrated memory)

After generation, use `/first-love-{slug}` to start chatting.

### Management Commands

| Command | Description |
|---------|-------------|
| `/list-first-loves` | List all generated first-love Skills |
| `/first-love-{slug}` | Full mode |
| `/first-love-{slug}-memory` | Memory mode |
| `/first-love-{slug}-persona` | Persona mode |
| `/first-love-rollback {slug} {version}` | Roll back to a previous version |
| `/delete-first-love {slug}` | Delete |
| `/seal-summer {slug}` | Gentle alias for delete |

---

## Examples

> Input: `College classmate, ENFP, Gemini, talks fast, sends midnight voice notes, acts tough after arguments but still checks in`

**Scenario 1: Casual chat**

```text
User             ❯ what are you doing
First-Love.skill ❯ just got home, grabbed some fruit downstairs
                  you though? what made you text me all of a sudden
```

**Scenario 2: Memory flashback**

```text
User             ❯ remember our first meal together?
First-Love.skill ❯ yeah, you were so nervous you held chopsticks backwards
                  then pretended it was “your special technique”
```

**Scenario 3: Late-night emotion**

```text
User             ❯ i kinda want to go back to those days
First-Love.skill ❯ mm
                  don't rush into sadness
                  did you skip sleep again tonight
```

---

## Features

### Data Sources

| Source | Format | Notes |
|--------|--------|-------|
| WeChat chats | txt / html / csv / json / sqlite | Recommended, rich behavioral detail |
| QQ chats | txt / mht / mhtml | Great for school-era timelines |
| Social media | screenshots / text exports | Helps capture public persona |
| Photos | JPEG / PNG (with EXIF) | Timeline and location clues |
| Narrated memory | plain text | Full flow still works without attachments |

### Output Files (per `{slug}`)

- `first_loves/{slug}/memory.md`
- `first_loves/{slug}/persona.md`
- `first_loves/{slug}/meta.json`
- `first_loves/{slug}/response_profile.json`
- `first_loves/{slug}/SKILL.md`

### Response Variability Layer (not random chaos)

- `response_router.md`: classifies input type, relationship phase, and response intensity
- `response_modules.md`: defines primary/secondary expression modules
- `response_profile.json`: stores weighted module preferences + cooldown windows

This keeps the persona stable while making replies feel naturally variable.

---

## Safety Boundaries

1. Personal reflection and memory organization only
2. No real-world contact initiation, no replacement for real relationships
3. No reinforcement of obsessive attachment
4. Data is handled/stored locally by default
5. Key expressions should be evidence-backed, not idealized fabrication

---

## Project Structure

```text
first-love-skill/
├── SKILL.md
├── README.md
├── README_EN.md
├── INSTALL.md
├── prompts/
│   ├── intake.md
│   ├── intake_structurer.md
│   ├── memory_analyzer.md
│   ├── memory_builder.md
│   ├── persona_analyzer.md
│   ├── persona_builder.md
│   ├── response_router.md
│   ├── response_modules.md
│   ├── response_profile_builder.md
│   ├── merger.md
│   └── correction_handler.md
├── tools/
│   ├── wechat_parser.py
│   ├── qq_parser.py
│   ├── social_parser.py
│   ├── photo_analyzer.py
│   ├── chat_analysis.py
│   ├── variability_engine.py
│   ├── skill_writer.py
│   └── version_manager.py
├── docs/
└── first_loves/
```

---

## Credits & Upstream Attribution

- This project is a modified derivative of **[therealXiaomanChu/ex-skill](https://github.com/therealXiaomanChu/ex-skill)**.
- Following common open-source practice on GitHub, this README explicitly acknowledges upstream inspiration/derivation and keeps the license context transparent (this repo is MIT-licensed).
- Thanks also to **[titanwings/colleague-skill](https://github.com/titanwings/colleague-skill)**, the earlier conceptual inspiration cited by ex-skill.

If you fork or remix this project, keeping this attribution chain is strongly recommended.
