"""Versioned, inspectable translation catalogs. No module is monkey-patched."""

from __future__ import annotations

import builtins
import json
import keyword
from copy import deepcopy
from importlib.resources import files
from pathlib import Path


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"번역 사전에 중복 키가 있습니다: {key}")
        result[key] = value
    return result


def read_json(text: str) -> dict:
    return json.loads(text, object_pairs_hook=_unique_object)


class Catalog:
    def __init__(self):
        root = files("hangeul_python").joinpath("data")
        self.core = read_json(root.joinpath("core.json").read_text(encoding="utf-8"))
        self.api = read_json(root.joinpath("api.json").read_text(encoding="utf-8"))
        self.overrides = {"schema_version": 1}
        # Reflected and in-place binary operations follow the same naming rule.
        specials = self.core["special_names"]
        for op in ("add", "sub", "mul", "matmul", "truediv", "floordiv", "mod", "divmod",
                   "pow", "lshift", "rshift", "and", "xor", "or"):
            name = specials[f"__{op}__"][2:-2]
            specials.setdefault(f"__r{op}__", f"__역{name}__")
            if op != "divmod":
                specials.setdefault(f"__i{op}__", f"__제자리{name}__")
        self.refresh()

    def refresh(self):
        self.replacements = {}
        for section in ("keywords", "soft_keywords", "special_names"):
            for original, korean in self.core[section].items():
                if korean in self.replacements and self.replacements[korean] != original:
                    raise ValueError(f"번역어 충돌: {korean}")
                self.replacements[korean] = original
        self.module_aliases = {
            value["alias"]: name for name, value in self.api["modules"].items()
        }
        if len(self.module_aliases) != len(self.api["modules"]):
            raise ValueError("모듈 번역어가 중복되었습니다")
        self.attribute_aliases = set()
        for group in (self.api["types"], self.api["modules"]):
            for data in group.values():
                values = list(data.get("members", {}).values())
                if len(values) != len(set(values)):
                    raise ValueError("한 객체 안에서 멤버 번역어가 중복되었습니다")
                self.attribute_aliases.update(values)
        self.keyword_aliases = set()
        mappings = list(self.api["builtin_keywords"].values())
        for group in (self.api["types"], self.api["modules"]):
            for data in group.values():
                mappings.extend(data.get("keywords", {}).values())
        for mapping in mappings:
            if len(mapping.values()) != len(set(mapping.values())):
                raise ValueError("한 함수 안에서 인자 번역어가 중복되었습니다")
            self.keyword_aliases.update(mapping.values())

    def canonical_module(self, name: str) -> str:
        for alias in sorted(self.module_aliases, key=len, reverse=True):
            if name == alias or name.startswith(alias + "."):
                return self.module_aliases[alias] + name[len(alias):]
        return name

    def type_profile(self, name: str, seen: frozenset[str] = frozenset()) -> dict:
        if name in seen:
            raise ValueError("자료형 번역 사전 상속이 순환합니다")
        profile = self.api["types"].get(name, {})
        merged = {"members": {}, "keywords": {}}
        if parent := profile.get("inherit_members"):
            merged = self.type_profile(parent, seen | {name})
        for section in merged:
            merged[section] = {**merged[section], **profile.get(section, {})}
        if name.startswith("builtins."):
            owner = getattr(builtins, name.split(".", 1)[1], None)
            if owner is not None:
                merged["members"] = {key: value for key, value in merged["members"].items()
                                     if hasattr(owner, key)}
                merged["keywords"] = {key: value for key, value in merged["keywords"].items()
                                      if hasattr(owner, key)}
        return merged

    def load_profile(self, path: str | Path):
        extra = read_json(Path(path).read_text(encoding="utf-8"))
        self.apply_profile(extra)

    def apply_profile(self, extra: dict):
        if extra.get("schema_version") != 1:
            raise ValueError("지원하지 않는 번역 사전 버전입니다")
        previous = self.api
        candidate = deepcopy(previous)
        for section in ("modules", "types", "builtin_keywords"):
            for name, data in extra.get(section, {}).items():
                candidate[section][name] = data
        self.api = candidate
        try:
            self.refresh()
            if problems := self.validate():
                raise ValueError("; ".join(problems))
        except Exception:
            self.api = previous
            self.refresh()
            raise
        for section in ("modules", "types", "builtin_keywords"):
            self.overrides.setdefault(section, {}).update(extra.get(section, {}))

    def validate(self) -> list[str]:
        problems = []
        for key in keyword.kwlist:
            if key not in self.core["keywords"]:
                problems.append(f"문법 번역 누락: {key}")
        for key in keyword.softkwlist:
            if key != "_" and key not in self.core["soft_keywords"]:
                problems.append(f"문맥 키워드 번역 누락: {key}")
        for key in dir(builtins):
            if key.startswith("_") or key in keyword.kwlist:
                continue
            if key not in self.core["builtins"] and key not in self.core["exceptions"]:
                problems.append(f"내장 이름 번역 누락: {key}")
        all_aliases = []
        for section in ("builtins", "exceptions"):
            all_aliases.extend(self.core[section].values())
        if len(all_aliases) != len(set(all_aliases)):
            problems.append("내장 번역어 충돌")
        if set(all_aliases) & set(self.replacements):
            problems.append("내장 이름과 예약어 충돌")
        for name in self.api["types"]:
            self.type_profile(name)
        return problems
