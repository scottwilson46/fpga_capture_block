module dual_port_ram #(parameter DATA_WIDTH      = 64,
                       parameter MEM_DEPTH       = 128,
                       parameter OUTPUT_REG      = 0) (
  input                              port_a_clk,
  input                              port_a_wr,
  input      [$clog2(MEM_DEPTH)-1:0] port_a_addr,
  input      [DATA_WIDTH-1:0]        port_a_din,
  output     [DATA_WIDTH-1:0]        port_a_dout,

  input                              port_b_clk,
  input                              port_b_wr,
  input      [$clog2(MEM_DEPTH)-1:0] port_b_addr,
  input      [DATA_WIDTH-1:0]        port_b_din,
  output     [DATA_WIDTH-1:0]        port_b_dout
);
reg [DATA_WIDTH-1:0] mem [MEM_DEPTH-1:0];

reg [DATA_WIDTH-1:0] port_a_dout_reg, port_a_dout_reg2;
reg [DATA_WIDTH-1:0] port_b_dout_reg, port_b_dout_reg2;

always @(posedge port_a_clk) begin
  port_a_dout_reg <= mem[port_a_addr];
  if (port_a_wr) begin
    mem[port_a_addr] <= port_a_din;
  end
end

generate
  if (OUTPUT_REG != 0) begin
    always @(posedge port_a_clk) 
      port_a_dout_reg2 <= port_a_dout_reg;

    assign port_a_dout = port_a_dout_reg2;
  end else begin
    assign port_a_dout = port_a_dout_reg;
  end
endgenerate

always @(posedge port_b_clk) begin
  port_b_dout_reg    <= mem[port_b_addr];
  if (port_b_wr) begin
    mem[port_b_addr] <= port_b_din;
  end
end

generate
  if (OUTPUT_REG != 0) begin
    always @(posedge port_b_clk) 
      port_b_dout_reg2 <= port_b_dout_reg;

    assign port_b_dout = port_b_dout_reg2;
  end else begin
    assign port_b_dout = port_b_dout_reg;
  end
endgenerate

endmodule


