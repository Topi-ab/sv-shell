<!-- SPDX-FileCopyrightText: 2026 sv-shell contributors -->
<!-- SPDX-License-Identifier: LGPL-3.0-or-later -->

# sv-shell

`sv-shell` is a Python library and Linux CLI that reads a single Verilog/SystemVerilog file and generates an empty SystemVerilog shell that contains only the module declaration and port list (plus parameter port list, if present). Port types are forced to `logic`.

It uses `pyslang` (py-slang) AST parsing.

## Install (PyPI)

```bash
python3 -m pip install ab-sv-shell
```

## Install (Local Development)

```bash
python3 -m pip install -e .
```

## CLI

```bash
sv-shell path/to/design.sv
sv-shell path/to/design.sv -o shell.sv
sv-shell path/to/design.sv --module my_module
```

## Library

```python
from sv_shell import shell_from_sv

shell = shell_from_sv("path/to/design.sv")
print(shell)
```

## Example

Example files are included in `examples/`:

- Input Verilog: `examples/counter.v`
- Generated SystemVerilog shell: `examples/counter_shell.sv`

Run the example (`counter.v`) from this repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
sv-shell examples/counter.v -o examples/counter_shell.sv
cat examples/counter_shell.sv
```

## Maintainer Notes

Release and PyPI publishing steps are documented in `RELEASING.md`.

## License

Project source code is licensed under `LGPL-3.0-or-later`.
Generated output files do not include injected SPDX/copyright lines, so existing
copyright / licensing on your original source is applied to the generated file.
