#!/usr/bin/env python3
"""Shared provider facts; runtime access, effort and billing stay separate.

This module never starts a model, refreshes credentials or authorizes spending.
`--check` validates the packaged catalog; `--runtime FILE` constrains observations
for orchestrate.py. Public API prices are reference data, not subscription bills.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "references" / "model-registry.json"
MAX_FACT_AGE_SECONDS = 7 * 24 * 60 * 60
RUNTIME_TTL_SECONDS = 900
VENDORS = {"codex": "openai", "claude": "anthropic", "antigravity": "google", "grok": "xai"}
DOMAINS = {
    "openai": {"developers.openai.com", "platform.openai.com", "learn.chatgpt.com"},
    "anthropic": {"platform.claude.com", "code.claude.com", "www.anthropic.com"},
    "google": {"ai.google.dev", "cloud.google.com", "antigravity.google"},
    "xai": {"docs.x.ai", "x.ai"},
}
HARNESS_MODES = {"ultra", "ultracode"}  # Dynamic delegation, not ordinary API effort.
PRICE_SCOPE = "direct-api-standard-usd-per-million-tokens"


def timestamp(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Registry timestamps need a timezone")
    return stamp


def runtime_fresh(value, now):
    try:
        age = (timestamp(now) - timestamp(value)).total_seconds()
        return 0 <= age <= RUNTIME_TTL_SECONDS
    except (TypeError, ValueError, AttributeError):
        return False


def evidence_expiry(observations):
    """Derive a bound; missing timestamps never inherit a caller's assertion."""
    try:
        return min(timestamp(value) + timedelta(seconds=ttl)
                   for value, ttl in observations).isoformat()
    except (TypeError, ValueError, AttributeError, OverflowError):
        return None


def digest(data):
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate registry key: " + key)
        result[key] = value
    return result


def _rate(value):
    if isinstance(value, bool):
        raise ValueError("Invalid API price")
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("Invalid API price") from None
    if not number.is_finite() or number < 0:
        raise ValueError("Invalid API price")


def validate_registry(data):
    if data.get("schema_version") != 1 or not data.get("version"):
        raise ValueError("Unsupported model registry version")
    timestamp(data["checked_at"])
    if not isinstance(data.get("sources"), dict) or not isinstance(data.get("models"), list) or not data["models"]:
        raise ValueError("Registry requires sources and models")
    keys = set()
    for model in data["models"]:
        surface, vendor = model.get("surface"), model.get("vendor")
        if VENDORS.get(surface) != vendor or vendor not in DOMAINS:
            raise ValueError("Invalid model surface/vendor")
        if model.get("id_namespace") not in ("provider-api", "provider-api-alias"):
            raise ValueError("Model ID needs an explicit supported namespace")
        for key in [model.get("id"), *model.get("aliases", [])]:
            if not isinstance(key, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}", key):
                raise ValueError("Invalid model ID or alias")
            if key in keys:
                raise ValueError("Duplicate model ID or alias: " + key)
            keys.add(key)
        if model.get("lifecycle") not in ("active", "preview", "deprecated", "retired"):
            raise ValueError("Invalid lifecycle")
        efforts = model.get("api_efforts")
        alias = model["id_namespace"] == "provider-api-alias"
        if alias and not model.get("documented_target"):
            raise ValueError("Rolling alias needs its documented target")
        if not (alias and efforts is None) and (not isinstance(efforts, list) or not efforts or len(efforts) != len(set(efforts))
                or any(not isinstance(e, str) or not e or e in HARNESS_MODES for e in efforts)):
            raise ValueError("API efforts must be explicit, non-harness values")
        if not model.get("sources"):
            raise ValueError("Model needs official sources")
        for name in model["sources"]:
            url = urlsplit(data["sources"].get(name, ""))
            if url.scheme != "https" or url.hostname not in DOMAINS[vendor] or url.username or url.password:
                raise ValueError("Missing or non-official source for " + model["id"])
        pricing = model.get("pricing")
        if pricing is not None:
            if pricing.get("scope") != PRICE_SCOPE:
                raise ValueError("API price scope must not imply a subscription bill")
            for field in ("input", "cached_input", "output", "cache_write"):
                if pricing.get(field) is not None:
                    _rate(pricing[field])
            for tier in pricing.get("tiers", []):
                if type(tier.get("above_input_tokens")) is not int or tier["above_input_tokens"] < 0:
                    raise ValueError("Invalid context price threshold")
                for field in ("input", "cached_input", "output", "cache_write"):
                    if tier.get(field) is not None:
                        _rate(tier[field])
    index = {m["id"]: m for m in data["models"]}
    for model in data["models"]:
        if model["id_namespace"] == "provider-api-alias":
            target = index.get(model["documented_target"])
            if not target or target["id_namespace"] != "provider-api" or target["vendor"] != model["vendor"]:
                raise ValueError("Rolling alias target must be an exact same-vendor model")
    for old_id, migration in data.get("legacy_lane_migration", {}).items():
        if old_id not in index or migration.get("candidate") not in index or not migration.get("status"):
            raise ValueError("Invalid legacy migration disposition")
    return data


def load_registry(path=None):
    data = json.loads(Path(path or DEFAULT_PATH).read_text(encoding="utf-8-sig"), object_pairs_hook=_object)
    return validate_registry(data)


def constrain_runtime(runtime, registry, now=None):
    """Intersect observations with public facts; never infer account access.

    Exact model IDs remain exact. An alias needs matching observed resolution.
    API and transport capabilities both constrain ordinary worker effort. Harness
    delegation modes are excluded, so a worker cannot silently become another
    unbudgeted orchestrator. Bot controls remain provider-managed.
    """
    validate_registry(registry)
    now = now or datetime.now(timezone.utc).isoformat()
    age = (timestamp(now) - timestamp(registry["checked_at"])).total_seconds()
    fresh = 0 <= age <= MAX_FACT_AGE_SECONDS
    index = {key: m for m in registry["models"] for key in [m["id"], *m.get("aliases", [])]}
    result = copy.deepcopy(runtime)
    result["model_registry"] = {"version": registry["version"], "sha256": digest(registry),
                                "checked_at": registry["checked_at"]}
    for c in result.get("candidates", []):
        errors = []
        observations = [(c.get("observed_at"), RUNTIME_TTL_SECONDS),
                        (c.get("quota", {}).get("observed_at"), RUNTIME_TTL_SECONDS)]
        requested = c.get("requested_model", c.get("model"))
        if c.get("surface") == "grok-bot":
            if c.get("model") is not None or c.get("resolved_model") is not None:
                errors.append("BOT_MODEL_CONTROL_UNVERIFIED")
            c.update(provider_efforts=[], transport_efforts=[], requested_model=None,
                     resolved_model=None, model=None)
        else:
            observations.append((registry["checked_at"], MAX_FACT_AGE_SECONDS))
            model = index.get(requested)
            if not model:
                errors.append("MODEL_NOT_REGISTERED")
            else:
                if not fresh:
                    errors.append("REGISTRY_STALE")
                if model["surface"] != c.get("surface"):
                    errors.append("MODEL_SURFACE_MISMATCH")
                rolling = model["id_namespace"] == "provider-api-alias"
                target_id = model["documented_target"] if rolling else model["id"]
                target = index[target_id]
                alias = requested != model["id"] or rolling
                if alias and c.get("resolved_model") != target_id:
                    errors.append("ALIAS_RESOLUTION_UNVERIFIED")
                if alias:
                    observations.append((c.get("resolution_observed_at"), RUNTIME_TTL_SECONDS))
                    if not runtime_fresh(c.get("resolution_observed_at"), now) or not c.get("resolution_evidence"):
                        errors.append("ALIAS_RESOLUTION_STALE")
                if model.get("requires_access_program"):
                    access = c.get("access_proof", {})
                    observations.append((access.get("observed_at"), RUNTIME_TTL_SECONDS))
                    account_ref = c.get("billing", {}).get("account_ref")
                    if (access.get("verified") is not True or not access.get("evidence")
                            or access.get("program") != model["requires_access_program"]
                            or not account_ref or access.get("account_ref") != account_ref
                            or not runtime_fresh(access.get("observed_at"), now)):
                        errors.append("MODEL_ACCESS_UNVERIFIED")
                if c.get("resolved_model") is not None and c["resolved_model"] != target_id:
                    errors.append("MODEL_RESOLUTION_MISMATCH")
                if model["lifecycle"] != "active" or target["lifecycle"] != "active" or c.get("lifecycle") != "active":
                    errors.append("MODEL_NOT_ACTIVE")
                allowed = set(target["api_efforts"]) - HARNESS_MODES
                c["provider_efforts"] = [e for e in c.get("provider_efforts", []) if e in allowed]
                c["transport_efforts"] = [e for e in c.get("transport_efforts", []) if e in allowed]
                c["requested_model"] = requested
                c["model"] = model["id"]
                c["model_id_namespace"] = model["id_namespace"]
                # Exact requested IDs do not prove which model actually ran.
                c.setdefault("resolved_model", None)
                c["registry_sources"] = [registry["sources"][name] for name in model["sources"]]
        # Preserve the earliest gate expiry through plan -> dispatch. A fresh
        # runtime snapshot must not extend an older alias/access/catalog proof.
        c["valid_until"] = evidence_expiry(observations)
        c["registry_errors"] = sorted(set(errors))
        if errors:
            c["available"] = False
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--now")
    args = parser.parse_args(argv)
    try:
        registry = load_registry(args.registry)
        if args.runtime:
            runtime = json.loads(args.runtime.read_text(encoding="utf-8-sig"), object_pairs_hook=_object)
            result = constrain_runtime(runtime, registry, args.now)
        elif args.check:
            result = {"valid": True, "version": registry["version"], "models": len(registry["models"]),
                      "sha256": digest(registry)}
        else:
            result = registry
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (KeyError, TypeError, ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
