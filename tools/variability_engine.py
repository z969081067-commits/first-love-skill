#!/usr/bin/env python3
"""Weighted response-module selector for first-love skill."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any


PRIMARY_FALLBACK = [
    "lightly_catch",
    "tsundere_care",
    "youthful_pause",
    "half_tease",
    "counter_probe",
    "act_casual",
    "brief_soften_then_pull_back",
    "guarded_retreat",
]

SECONDARY_FALLBACK = [
    "memory_flash",
    "old_habit_echo",
    "late_night_loosen",
    "tiny_jealousy",
    "low_pressure_care",
    "gentle_redirect",
]


def load_json(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误：response_profile.json 不存在 {path}", file=sys.stderr)
        sys.exit(1)


def safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def weighted_pick(
    candidates: list[str],
    base_weights: dict[str, float],
    preferred: list[str],
    boosted: list[str],
    suppressed: list[str],
    recent: list[str],
    repeat_penalty: float,
    rng: random.Random,
) -> str:
    scored: list[tuple[str, float]] = []
    for item in candidates:
        weight = safe_float(base_weights.get(item, 1.0), 1.0)
        if item in preferred:
            weight *= 1.35
        if item in boosted:
            weight *= 1.2
        if item in suppressed:
            weight *= 0.65
        if item in recent:
            weight *= repeat_penalty
        scored.append((item, max(weight, 0.01)))

    total = sum(weight for _, weight in scored)
    pivot = rng.uniform(0, total)
    cursor = 0.0
    for item, weight in scored:
        cursor += weight
        if pivot <= cursor:
            return item
    return scored[-1][0]


def main() -> None:
    parser = argparse.ArgumentParser(description="回复变化模块选择器")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="根据 response_profile.json 计算本轮模块选择")
    plan.add_argument("--profile", required=True, help="response_profile.json 路径")
    plan.add_argument("--input-type", required=True, help="输入类型")
    plan.add_argument("--phase", help="关系相位")
    plan.add_argument("--intensity", help="表达强度")
    plan.add_argument("--recent-primary", default="", help="最近主模块，逗号分隔")
    plan.add_argument("--recent-secondary", default="", help="最近副模块，逗号分隔")
    plan.add_argument("--seed", type=int, help="随机种子，用于复现")

    args = parser.parse_args()

    profile = load_json(args.profile)
    rng = random.Random(args.seed)

    default_state = profile.get("default_state", {})
    routes = profile.get("input_routes", {})
    route = routes.get(args.input_type, {})
    phase = args.phase or default_state.get("phase", "golden_period")
    intensity = args.intensity or route.get("intensity_bias") or default_state.get("intensity", "medium")
    phase_bias = profile.get("phase_bias", {}).get(phase, {})

    cooldown = profile.get("cooldown", {})
    repeat_penalty = safe_float(cooldown.get("repeat_penalty", 0.4), 0.4)
    recent_primary = [x.strip() for x in args.recent_primary.split(",") if x.strip()]
    recent_secondary = [x.strip() for x in args.recent_secondary.split(",") if x.strip()]

    primary_weights = profile.get("module_weights", {}).get("primary", {})
    secondary_weights = profile.get("module_weights", {}).get("secondary", {})
    preferred_primary = route.get("preferred_primary", [])
    preferred_secondary = route.get("preferred_secondary", [])
    boosted = phase_bias.get("boost", [])
    suppressed = phase_bias.get("suppress", [])

    primary = weighted_pick(
        PRIMARY_FALLBACK,
        primary_weights,
        preferred_primary,
        boosted,
        suppressed,
        recent_primary[: int(cooldown.get("recent_primary_window", 3))],
        repeat_penalty,
        rng,
    )

    secondary_probability = safe_float(default_state.get("secondary_module_probability", 0.35), 0.35)
    secondary = None
    if rng.random() <= secondary_probability:
        secondary = weighted_pick(
            SECONDARY_FALLBACK,
            secondary_weights,
            preferred_secondary,
            boosted,
            suppressed,
            recent_secondary[: int(cooldown.get("recent_secondary_window", 2))],
            repeat_penalty,
            rng,
        )

    memory_insert_probability = safe_float(default_state.get("memory_insert_probability", 0.25), 0.25)
    memory_insert = rng.random() <= memory_insert_probability

    result = {
        "input_type": args.input_type,
        "phase": phase,
        "intensity": intensity,
        "primary_module": primary,
        "secondary_module": secondary,
        "memory_insert": memory_insert,
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
