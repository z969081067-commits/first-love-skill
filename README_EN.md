# First-Love.skill

**Turn the remembered version of your first love into an AI Skill.**

The goal is not to replay the ending. The goal is to bring the user back to the first sight, the first real conversation, the first rush of feeling, and the brightest stretch of that relationship.

⚠️ For personal reflection only. Not for harassment, stalking, or replacing real contact.

## Suggested GitHub Repo Name

`first-love-skill`

## Usage

Type in Claude Code:

```text
/create-first-love
```

Then provide:

1. Relationship anchor: codename, life stage, how long you were closest, what state the memory stays in now
2. Falling-in-love memories: first sight, first real conversation, first spark, and the brightest scenes
3. Interaction profile: how they spoke, how they moved closer, how they reacted when sad or upset, and what topics they avoided
4. Source material: chat logs, photos, social posts, narrated memories

Each category can include follow-up prompts. The goal is to collect scenes, actions, exact wording, emotions, and relationship rhythm, not just labels.
The flow can also lightly ask for a few downstream fields such as how you met, the main city/place, MBTI, or zodiac if you know them.
Before generation, the intake answers should be normalized into a structured result that feeds `meta.json`, `memory.md`, `persona.md`, and the response-variation layer.

Use `/first-love-{slug}` after generation.

Each generated first-love skill now also carries a `response_profile.json` file:

- It does not make replies randomly chaotic
- It gives the skill weighted variation inside the same persona
- It adds cooldown so the same reply style does not repeat every turn
- If the file is missing, the skill should still fall back to `memory.md` + `persona.md` without breaking

## Commands

| Command | Description |
|---------|-------------|
| `/list-first-loves` | List all first-love Skills |
| `/first-love-{slug}` | Full mode |
| `/first-love-{slug}-memory` | Memory mode |
| `/first-love-{slug}-persona` | Persona mode |
| `/first-love-rollback {slug} {version}` | Roll back |
| `/delete-first-love {slug}` | Delete |
| `/seal-summer {slug}` | Gentle delete alias |

## Core Logic

1. The default identity is the remembered version of them.
2. First sight, growing closer, and falling for them matter more than the ending.
3. The tone leans toward youth, seasonality, and first-love intensity.
4. A white-moonlight atmosphere is allowed, but unsupported idealization is not.
5. The system keeps asking: “Why did you fall for them in the first place?”

## Response Variability

The skill now uses a three-part response-variation layer:

1. `response_router.md`
   Chooses the likely input type, relationship phase, and reply intensity before responding.
2. `response_modules.md`
   Defines primary and secondary expression modules such as gentle catching, youthful pause, counter-probing, low-pressure care, and memory flash.
3. `response_profile.json`
   Stores weighted module preferences, route biases, cooldown windows, and evidence-backed variation settings for that specific first love.

This is designed to make the AI feel more like one real person with natural fluctuations, not a rigid template and not a random-text generator.

## Output Files

Each generated first-love skill should create:

- `first_loves/{slug}/memory.md`
- `first_loves/{slug}/persona.md`
- `first_loves/{slug}/meta.json`
- `first_loves/{slug}/response_profile.json`
- `first_loves/{slug}/SKILL.md`

## Project Layout

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
  │   └── response_profile_builder.md
  ├── tools/
  │   ├── wechat_parser.py
  │   ├── qq_parser.py
  │   ├── social_parser.py
  │   ├── photo_analyzer.py
  │   ├── skill_writer.py
  │   ├── version_manager.py
  │   ├── chat_analysis.py
  │   └── variability_engine.py
  ├── docs/
  └── first_loves/
```

## Notes

- White-moonlight feeling should come from evidence and remembered detail, not fabrication.
- Weighted variation should change wording and approach, not core personality facts.
- If later corrections say “they would not reply like that,” update both `persona.md` and `response_profile.json`.
- If you find yourself becoming too emotionally absorbed, pause and step away from the skill.
