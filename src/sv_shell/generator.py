# SPDX-FileCopyrightText: 2026 sv-shell contributors
# SPDX-License-Identifier: LGPL-3.0-or-later

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

import pyslang


@dataclass(frozen=True)
class PortDecl:
    direction: str
    signing: str
    packed_dims: tuple[str, ...]
    name: str
    unpacked_dims: tuple[str, ...]


class ShellGenerationError(RuntimeError):
    pass


def generate_shell_from_file(path: str | Path, module_name: str | None = None) -> str:
    source_path = Path(path)
    source_text = source_path.read_text()
    tree = pyslang.SyntaxTree.fromFile(str(source_path))

    errors = [d for d in tree.diagnostics if d.isError()]
    if errors:
        raise ShellGenerationError(
            f"Parse failed for {source_path}: {len(errors)} error diagnostic(s)."
        )

    modules = [
        member
        for member in tree.root.members
        if _is_syntax_node(member) and member.kind.name == "ModuleDeclaration"
    ]

    if not modules:
        raise ShellGenerationError(f"No module declarations found in {source_path}")

    if module_name is not None:
        modules = [m for m in modules if m.header.name.valueText == module_name]
        if not modules:
            raise ShellGenerationError(
                f"Module '{module_name}' not found in {source_path}"
            )

    rendered = [_render_module(module, source_text) for module in modules]
    return "\n\n".join(rendered) + "\n"


def _render_module(module, source_text: str) -> str:
    header = module.header
    name = header.name.valueText

    param_text = ""
    if header.parameters is not None:
        raw_param_text = _strip_attributes(_node_text(header.parameters, source_text))
        if raw_param_text:
            param_text = f" {raw_param_text.lstrip()}"

    ports = _extract_ports(module, source_text)

    lines: list[str] = [f"module {name}{param_text} ("]

    if ports:
        port_lines = [f"    {_render_port_decl(port)}" for port in ports]
        for idx, port_line in enumerate(port_lines):
            suffix = "," if idx < len(port_lines) - 1 else ""
            lines.append(f"{port_line}{suffix}")
    lines.append(");")
    lines.append("endmodule")
    return "\n".join(lines)


def _extract_ports(module, source_text: str) -> list[PortDecl]:
    port_list = module.header.ports
    if port_list is None:
        return []
    if port_list.kind.name == "AnsiPortList":
        return _extract_ansi_ports(module, source_text)
    if port_list.kind.name == "NonAnsiPortList":
        return _extract_non_ansi_ports(module, source_text)
    raise ShellGenerationError(f"Unsupported port list kind: {port_list.kind.name}")


def _extract_ansi_ports(module, source_text: str) -> list[PortDecl]:
    ports: list[PortDecl] = []
    for entry in module.header.ports.ports:
        if not _is_syntax_node(entry):
            continue
        if entry.kind.name not in {"ImplicitAnsiPort", "ExplicitAnsiPort"}:
            continue

        if not hasattr(entry, "header") or not hasattr(entry, "declarator"):
            raise ShellGenerationError(
                f"Unsupported ANSI port node kind: {entry.kind.name}"
            )

        header = entry.header
        if not hasattr(header, "direction") or not hasattr(header, "dataType"):
            raise ShellGenerationError(
                f"Unsupported ANSI port header kind: {header.kind.name}"
            )

        direction = header.direction.valueText
        if not direction:
            raise ShellGenerationError("Port direction must be explicit")

        data_type = header.dataType
        signing = _extract_signing(data_type)
        packed_dims = _extract_dimensions(data_type.dimensions, source_text)

        declarator = entry.declarator
        name = declarator.name.valueText
        unpacked_dims = _extract_dimensions(declarator.dimensions, source_text)

        ports.append(
            PortDecl(
                direction=direction,
                signing=signing,
                packed_dims=packed_dims,
                name=name,
                unpacked_dims=unpacked_dims,
            )
        )
    return ports


def _extract_non_ansi_ports(module, source_text: str) -> list[PortDecl]:
    ordered_names: list[str] = []
    for entry in module.header.ports.ports:
        if not _is_syntax_node(entry):
            continue
        if entry.kind.name not in {"ImplicitNonAnsiPort", "ExplicitNonAnsiPort"}:
            continue
        if not hasattr(entry, "expr"):
            raise ShellGenerationError(
                f"Unsupported non-ANSI port node kind: {entry.kind.name}"
            )
        name = _node_text(entry.expr, source_text).strip()
        ordered_names.append(name)

    declaration_map: dict[str, PortDecl] = {}
    for member in module.members:
        if not _is_syntax_node(member) or member.kind.name != "PortDeclaration":
            continue

        header = member.header
        if not hasattr(header, "direction") or not hasattr(header, "dataType"):
            raise ShellGenerationError(
                f"Unsupported port declaration header kind: {header.kind.name}"
            )

        direction = header.direction.valueText
        if not direction:
            raise ShellGenerationError("Port direction must be explicit")

        data_type = header.dataType
        signing = _extract_signing(data_type)
        packed_dims = _extract_dimensions(data_type.dimensions, source_text)

        for declarator in _iter_declarators(member.declarators):
            declaration_map[declarator.name.valueText] = PortDecl(
                direction=direction,
                signing=signing,
                packed_dims=packed_dims,
                name=declarator.name.valueText,
                unpacked_dims=_extract_dimensions(declarator.dimensions, source_text),
            )

    missing = [name for name in ordered_names if name not in declaration_map]
    if missing:
        raise ShellGenerationError(
            "Missing declarations for non-ANSI ports: " + ", ".join(missing)
        )

    return [declaration_map[name] for name in ordered_names]


def _extract_signing(data_type) -> str:
    signing = getattr(data_type, "signing", None)
    if signing is None or getattr(signing, "isMissing", False):
        return ""
    return signing.valueText


def _extract_dimensions(dimensions, source_text: str) -> tuple[str, ...]:
    return tuple(
        _node_text(node, source_text).strip()
        for node in dimensions
        if _is_syntax_node(node)
    )


def _iter_declarators(nodes) -> Iterable:
    for node in nodes:
        if _is_syntax_node(node) and node.kind.name == "Declarator":
            yield node


def _render_port_decl(port: PortDecl) -> str:
    type_text = _render_logic_type(port.signing, port.packed_dims)
    unpacked = "".join(f" {dim}" for dim in port.unpacked_dims)
    return f"{port.direction} {type_text} {port.name}{unpacked}"


def _render_logic_type(signing: str, packed_dims: tuple[str, ...]) -> str:
    parts = ["logic"]
    if signing:
        parts.append(signing)
    parts.extend(packed_dims)
    return " ".join(parts)


def _node_text(node, source_text: str) -> str:
    source_range = node.sourceRange
    return source_text[source_range.start.offset : source_range.end.offset]


def _is_syntax_node(value) -> bool:
    return hasattr(value, "sourceRange")


_ATTRIBUTE_RE = re.compile(r"\(\*.*?\*\)\s*", flags=re.DOTALL)


def _strip_attributes(text: str) -> str:
    return _ATTRIBUTE_RE.sub("", text)
