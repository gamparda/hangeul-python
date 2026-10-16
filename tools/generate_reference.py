"""Generate reference, editor completion data, and honest stdlib inventories."""

import argparse
import json
import sys
from pathlib import Path

from hangeul_python import Catalog

ROOT = Path(__file__).resolve().parents[1]


def artifacts():
    catalog = Catalog()
    lines = ["# 번역 사전", "", "core.json과 api.json에서 자동 생성합니다.",
             "번역어 변경은 원본 JSON을 수정한 뒤 tools/generate_reference.py를 실행하세요.", ""]
    for section, title in [("keywords", "문법"), ("soft_keywords", "문맥 키워드"),
                           ("builtins", "내장 이름"), ("exceptions", "예외"),
                           ("special_names", "특수 이름")]:
        lines += [f"## {title}", "", "| 파이썬 | 한글 |", "|---|---|"]
        lines += [f"| {a} | {b} |" for a, b in catalog.core[section].items()]
        lines.append("")
    lines += ["## 내장 함수 인자", ""]
    for function, mapping in catalog.api["builtin_keywords"].items():
        lines += [f"- {function}: " + ", ".join(f"{a} → {b}" for a, b in mapping.items())]
    lines += ["", "## 자료형별 멤버", ""]
    for name in catalog.api["types"]:
        profile = catalog.type_profile(name)
        lines += [f"### {name}", "", "| 파이썬 | 한글 |", "|---|---|"]
        lines += [f"| {a} | {b} |" for a, b in profile["members"].items()]
        lines.append("")
        for fn, mapping in profile["keywords"].items():
            lines += [f"- {fn} 인자: " + ", ".join(f"{a} → {b}" for a, b in mapping.items())]
        lines.append("")
    lines += ["## 모듈", "", "API 수는 등록된 이름의 수입니다. 모듈 전체 번역 완료를 뜻하지 않습니다.",
              "", "| 원본 모듈 | 한글 모듈 | API 이름 수 |", "|---|---|---:|"]
    for name, data in sorted(catalog.api["modules"].items()):
        lines += [f"| {name} | {data['alias']} | {len(data.get('members', {}))} |"]
    lines += ["", "## 모듈별 API", ""]
    for name, data in sorted(catalog.api["modules"].items()):
        if not data.get("members"):
            continue
        lines += [f"### {data['alias']} ({name})", "", "| 파이썬 | 한글 |", "|---|---|"]
        lines += [f"| {a} | {b} |" for a, b in data["members"].items()]
        for fn, mapping in data.get("keywords", {}).items():
            lines += ["", f"- {fn} 인자: " + ", ".join(f"{a} → {b}" for a, b in mapping.items())]
        lines.append("")
    completions = {}
    for section in ("keywords", "soft_keywords", "builtins", "exceptions", "special_names"):
        for english, korean in catalog.core[section].items():
            completions.setdefault(korean, []).append(english)
    for group in ("modules", "types"):
        for name, data in catalog.api[group].items():
            if "alias" in data:
                completions.setdefault(data["alias"], []).append(name)
            for english, korean in data.get("members", {}).items():
                completions.setdefault(korean, []).append(f"{name}.{english}")
    completion_data = [{"korean": name, "originals": sorted(set(originals))}
                       for name, originals in sorted(completions.items())]
    return {
        ROOT / "docs/translation-reference.md": "\n".join(lines).rstrip() + "\n",
        ROOT / "editors/vscode/translations.json": json.dumps(
            completion_data, ensure_ascii=False, indent=2) + "\n",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--inventory", action="store_true")
    args = parser.parse_args()
    if args.inventory:
        catalog = Catalog()
        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        inventory = {
            "python_version": version,
            "scope": "sys.stdlib_module_names; 모듈 단위, 하위모듈 제외",
            "modules": [
                {"python": name,
                 "korean": catalog.api["modules"].get(name, {}).get("alias"),
                 "registered_members": len(catalog.api["modules"].get(name, {}).get("members", {})),
                 "status": ("internal" if name.startswith("_") and name != "__future__"
                            else "partial_api" if catalog.api["modules"].get(name, {}).get("members")
                            else "module_alias" if name in catalog.api["modules"] else "planned")}
                for name in sorted(sys.stdlib_module_names)
            ],
        }
        path = ROOT / f"docs/stdlib-inventory-{version}.json"
        path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
        return
    for path, content in artifacts().items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"생성 문서 갱신 필요: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
