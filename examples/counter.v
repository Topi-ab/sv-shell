// SPDX-FileCopyrightText: 2026 sv-shell contributors
// SPDX-License-Identifier: LGPL-3.0-or-later

module counter(clk, rst_n, en, count);
  input clk;
  input rst_n;
  input en;
  output reg [3:0] count;

  wire tick;
  reg [3:0] acc;
endmodule
