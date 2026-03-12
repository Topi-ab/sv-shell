# SPDX-FileCopyrightText: 2026 sv-shell contributors
# SPDX-License-Identifier: LGPL-3.0-or-later

from pathlib import Path

from sv_shell import shell_from_sv


def write_sv(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content)
    return path


def test_generates_shell_for_ansi_ports(tmp_path: Path) -> None:
    source = write_sv(
        tmp_path,
        "ansi.sv",
        """\
    (* mod_attr = 1 *) module foo #(parameter int W = 8) (
  (* keep = "true" *) input wire clk,
  input [W-1:0] a,
  output reg [W-1:0] y
);
  localparam int L = 2;
  typedef logic [W-1:0] word_t;
  wire z;
  reg [W-1:0] r;
  logic [W-1:0] l;
  assign y = a;
endmodule
""",
    )

    rendered = shell_from_sv(source)

    assert not rendered.startswith("//")
    assert "SPDX-License-Identifier" not in rendered
    assert "SPDX-FileCopyrightText" not in rendered
    assert "module foo #(parameter int W = 8) (" in rendered
    assert "input logic clk" in rendered
    assert "input logic [W-1:0] a" in rendered
    assert "output logic [W-1:0] y" in rendered
    assert "#(" in rendered
    assert "(*" not in rendered
    assert "localparam" not in rendered
    assert "typedef" not in rendered
    assert "logic z;" not in rendered
    assert "logic [W-1:0] r;" not in rendered
    assert "logic [W-1:0] l;" not in rendered
    assert "assign y = a;" not in rendered


def test_generates_shell_for_non_ansi_ports(tmp_path: Path) -> None:
    source = write_sv(
        tmp_path,
        "non_ansi.sv",
        """\
module bar(a, b, y);
  (* my_attr = 1 *) input wire [3:0] a, b;
  output reg y;
  wire z;
endmodule
""",
    )

    rendered = shell_from_sv(source)

    assert "module bar (" in rendered
    assert "input logic [3:0] a" in rendered
    assert "input logic [3:0] b" in rendered
    assert "output logic y" in rendered
    assert "logic z;" not in rendered
    assert "(*" not in rendered
    assert "input wire" not in rendered
    assert "output reg" not in rendered


def test_generates_shell_for_module_without_ports(tmp_path: Path) -> None:
    source = write_sv(
        tmp_path,
        "no_ports.sv",
        """\
module n;
  reg [1:0] r;
endmodule
""",
    )

    rendered = shell_from_sv(source)

    assert "module n (" in rendered
    assert ");" in rendered
    assert "logic [1:0] r;" not in rendered
