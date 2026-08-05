#!/usr/bin/env python3
"""Generate the per-domain namespace classes from ``sdk-manifest.json``.

The manifest is the public description of the SuperBooks tool surface:
one entry per tool with its name, description, JSON Schema for inputs, and
whether it is destructive. This script turns each entry into a typed method on
a domain namespace, for both the sync and async clients.

Usage::

    python scripts/codegen.py           # write src/superbooks/_generated/
    python scripts/codegen.py --check   # fail if the output is out of date

Output is deterministic: nothing time-varying is embedded, so ``--check`` is a
reliable CI gate against hand-editing the generated files or forgetting to
regenerate after a manifest update.
"""

from __future__ import annotations

import argparse
import json
import keyword
import sys
import textwrap
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "sdk-manifest.json"
OUTPUT_DIR = REPO_ROOT / "src" / "superbooks" / "_generated"


def dq(value: str) -> str:
    """Render a Python string literal with double quotes.

    ``repr`` would emit single quotes and fail ``ruff format --check``;
    ``json.dumps`` escapes identically to Python for plain strings.
    """
    return json.dumps(value)


HEADER = '''"""Generated from sdk-manifest.json by scripts/codegen.py. Do not edit.

Run ``python scripts/codegen.py`` to regenerate.
"""

from __future__ import annotations

import builtins
from typing import Any, Literal

from .._namespace import {base_class}

'''


def safe_identifier(name: str) -> str:
    """Make a Python-legal identifier out of an API name.

    Python keywords get a trailing underscore (``from`` -> ``from_``). The
    original name is what goes on the wire; the mangling is presentation only.
    """
    if keyword.iskeyword(name) or keyword.issoftkeyword(name):
        return f"{name}_"
    return name


def class_name_for(domain: str) -> str:
    parts = [p for p in domain.split("_") if p]
    return "".join(p.capitalize() for p in parts)


def method_name_for(domain: str, tool_name: str) -> str:
    """Strip the domain prefix off a tool id to get the method name."""
    prefix = f"{domain}_"
    base = tool_name[len(prefix) :] if tool_name.startswith(prefix) else tool_name
    if not base:
        base = tool_name
    return safe_identifier(base)


def python_type(schema: dict[str, Any]) -> str:
    """Map a JSON Schema node onto a Python type annotation."""
    enum = schema.get("enum")
    if isinstance(enum, list) and enum and all(isinstance(v, str) for v in enum):
        return "Literal[" + ", ".join(dq(v) for v in enum) + "]"

    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        # e.g. ["string", "null"] — the nullability is expressed by the
        # parameter default, so pick the first concrete type.
        non_null = [t for t in schema_type if t != "null"]
        schema_type = non_null[0] if non_null else None

    if schema_type == "string":
        return "str"
    if schema_type == "integer":
        return "int"
    if schema_type == "number":
        return "float"
    if schema_type == "boolean":
        return "bool"
    if schema_type == "array":
        items = schema.get("items")
        inner = python_type(items) if isinstance(items, dict) else "Any"
        # `builtins.` qualified on purpose: namespaces take their method names
        # from the API, and `list` is one of them. A bare `list[...]` inside
        # such a class body resolves to that method, not the type.
        return f"builtins.list[{inner}]"
    if schema_type == "object":
        return "builtins.dict[str, Any]"
    return "Any"


def describe_param(name: str, schema: dict[str, Any]) -> str:
    """One docstring line for a parameter."""
    bits: list[str] = []
    description = schema.get("description")
    if description:
        bits.append(str(description).strip().rstrip("."))
    if "default" in schema:
        bits.append(f"Defaults to {schema['default']!r} server-side")
    enum = schema.get("enum")
    if isinstance(enum, list) and enum and not description:
        bits.append("one of " + ", ".join(dq(v) for v in enum))
    return ". ".join(bits) if bits else ""


def build_docstring(tool: dict[str, Any], params: list[tuple[str, str, dict]]) -> str:
    lines: list[str] = []
    description = str(tool.get("description") or "").strip()
    if description:
        lines.extend(textwrap.wrap(description, width=76))
    else:
        lines.append(f"Call the {tool['name']} tool.")

    if tool.get("destructive"):
        lines.append("")
        lines.extend(
            textwrap.wrap(
                "Destructive. Two gates must both be open: the credential "
                "needs the full-access `apis.all` scope, and the team must "
                "have destructive AI tools enabled. Otherwise this raises "
                "AuthorizationError.",
                width=76,
            )
        )

    documented = [
        (py_name, describe_param(wire_name, schema))
        for py_name, wire_name, schema in params
    ]
    documented = [(n, d) for n, d in documented if d]
    if documented:
        lines.append("")
        lines.append("Args:")
        for py_name, doc in documented:
            wrapped = textwrap.wrap(f"{py_name}: {doc}.", width=72)
            lines.append(f"    {wrapped[0]}")
            for continued in wrapped[1:]:
                lines.append(f"        {continued}")

    if len(lines) == 1:
        return f'        """{lines[0]}"""'
    body = "\n".join(f"        {line}".rstrip() for line in lines)
    return f'        """\n{body}\n        """'


def render_method(domain: str, tool: dict[str, Any], is_async: bool) -> str:
    schema = tool.get("inputSchema") or {}
    properties: dict[str, Any] = schema.get("properties") or {}
    required: list[str] = list(schema.get("required") or [])

    # Required parameters first so they can also be passed positionally.
    ordered = [n for n in properties if n in required] + [
        n for n in properties if n not in required
    ]

    params: list[tuple[str, str, dict[str, Any]]] = []
    required_sig: list[str] = []
    optional_sig: list[str] = []
    arg_entries: list[str] = []

    for wire_name in ordered:
        prop = properties[wire_name] or {}
        py_name = safe_identifier(wire_name)
        annotation = python_type(prop)
        params.append((py_name, wire_name, prop))
        if wire_name in required:
            required_sig.append(f"{py_name}: {annotation}")
        else:
            optional_sig.append(f"{py_name}: {annotation} | None = None")
        arg_entries.append(f"                {dq(wire_name)}: {py_name},")

    signature_parts = ["self", *required_sig]
    if optional_sig:
        signature_parts.append("*")
        signature_parts.extend(optional_sig)

    method = method_name_for(domain, tool["name"])
    prefix = "async def" if is_async else "def"
    await_kw = "await " if is_async else ""

    joined = ",\n        ".join(signature_parts)
    lines = [
        f"    {prefix} {method}(",
        f"        {joined},",
        "    ) -> Any:",
        build_docstring(tool, params),
    ]

    if arg_entries:
        lines.append(f"        return {await_kw}self._call(")
        lines.append(f"            {dq(tool['name'])},")
        lines.append("            {")
        lines.extend(arg_entries)
        lines.append("            },")
        lines.append("        )")
    else:
        lines.append(f"        return {await_kw}self._call({dq(tool['name'])}, {{}})")

    return "\n".join(lines)


def render_namespace(domain: str, tools: list[dict[str, Any]], is_async: bool) -> str:
    suffix = "Async" if is_async else ""
    base = "AsyncNamespace" if is_async else "SyncNamespace"
    cls = f"{suffix}{class_name_for(domain)}"
    header = [
        f"class {cls}({base}):",
        f'    """`{domain}` tools ({len(tools)} available)."""',
        "",
    ]
    methods = [render_method(domain, tool, is_async) for tool in tools]
    return "\n".join(header) + "\n" + "\n\n".join(methods) + "\n"


def render_module(manifest: dict[str, Any], is_async: bool) -> str:
    base_class = "AsyncNamespace" if is_async else "SyncNamespace"
    parts = [HEADER.format(base_class=base_class)]

    domains = manifest["domains"]
    names = [("Async" if is_async else "") + class_name_for(d) for d in domains]
    all_line = "__all__ = [\n" + "".join(f"    {n!r},\n" for n in sorted(names)) + "]\n"
    parts.append(all_line)

    for domain, tools in domains.items():
        parts.append("\n")
        parts.append(render_namespace(domain, tools, is_async))

    return "".join(parts)


def render_init(manifest: dict[str, Any]) -> str:
    domains = list(manifest["domains"])
    lines = [
        '"""Generated from sdk-manifest.json by scripts/codegen.py. Do not edit.',
        "",
        "Run ``python scripts/codegen.py`` to regenerate.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
    ]

    sync_names = [class_name_for(d) for d in domains]
    async_names = [f"Async{class_name_for(d)}" for d in domains]

    lines.append("from ._async import (")
    for name in sorted(async_names):
        lines.append(f"    {name},")
    lines.append(")")
    lines.append("from ._sync import (")
    for name in sorted(sync_names):
        lines.append(f"    {name},")
    lines.append(")")
    lines.append("")

    lines.append("#: Domain name -> (sync namespace class, async namespace class).")
    lines.append("DOMAINS: dict[str, tuple[type, type]] = {")
    for domain in domains:
        cls = class_name_for(domain)
        lines.append(f"    {dq(domain)}: ({cls}, Async{cls}),")
    lines.append("}")
    lines.append("")
    lines.append(f"TOOL_COUNT = {manifest['toolCount']}")
    lines.append("")
    lines.append("__all__ = [")
    lines.append('    "DOMAINS",')
    lines.append('    "TOOL_COUNT",')
    for name in sorted(sync_names + async_names):
        lines.append(f"    {dq(name)},")
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def render_bind(manifest: dict[str, Any]) -> str:
    """Emit the typed namespace-holder mixins the clients inherit from.

    Generated rather than hand-written so that adding a domain to the manifest
    surfaces it on the client with full type information, without editing
    ``_client.py``.
    """
    domains = list(manifest["domains"])
    lines = [
        '"""Generated from sdk-manifest.json by scripts/codegen.py. Do not edit.',
        "",
        "Run ``python scripts/codegen.py`` to regenerate.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from .._transport import AsyncTransport, SyncTransport",
    ]

    lines.append("from ._async import (")
    for domain in sorted(domains):
        lines.append(f"    Async{class_name_for(domain)},")
    lines.append(")")
    lines.append("from ._sync import (")
    for domain in sorted(domains):
        lines.append(f"    {class_name_for(domain)},")
    lines.append(")")
    lines.append("")
    lines.append('__all__ = ["AsyncNamespaces", "SyncNamespaces"]')
    lines.append("")
    lines.append("")

    for is_async in (False, True):
        cls = "AsyncNamespaces" if is_async else "SyncNamespaces"
        transport = "AsyncTransport" if is_async else "SyncTransport"
        prefix = "Async" if is_async else ""
        flavour = "async" if is_async else "sync"
        lines.append(f"class {cls}:")
        lines.append(
            f'    """Typed tool namespaces attached to the {flavour} client."""'
        )
        lines.append("")
        for domain in domains:
            lines.append(f"    {domain}: {prefix}{class_name_for(domain)}")
        lines.append("")
        lines.append(f"    def _bind_namespaces(self, transport: {transport}) -> None:")
        for domain in domains:
            lines.append(
                f"        self.{domain} = {prefix}{class_name_for(domain)}(transport)"
            )
        lines.append("")
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


def generate(manifest: dict[str, Any]) -> dict[Path, str]:
    return {
        OUTPUT_DIR / "__init__.py": render_init(manifest),
        OUTPUT_DIR / "_sync.py": render_module(manifest, is_async=False),
        OUTPUT_DIR / "_async.py": render_module(manifest, is_async=True),
        OUTPUT_DIR / "_bind.py": render_bind(manifest),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the generated files differ from the manifest",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    files = generate(manifest)

    if args.check:
        stale = [
            path
            for path, content in files.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            for path in stale:
                print(f"out of date: {path.relative_to(REPO_ROOT)}", file=sys.stderr)
            print(
                "Run `python scripts/codegen.py` and commit the result.",
                file=sys.stderr,
            )
            return 1
        print(f"generated files are up to date ({manifest['toolCount']} tools)")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(REPO_ROOT)}")
    print(f"{manifest['toolCount']} tools across {len(manifest['domains'])} domains")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
