module my_capture #(parameter CAPTURE_WIDTH = 32,
                    parameter CAPTURE_SIZE  = 128) (
  input                           clk,
  input                           reset,

  input       [CAPTURE_WIDTH-1:0] capture_data,
  input                           capture_data_valid, 
  input                           capture_start,

  input                           capture_circular,
  input                           capture_stop,

  input       [31:0]              capture_rd_addr,
  input                           capture_reset,
  output      [CAPTURE_WIDTH-1:0] capture_rd_data,
  output      [31:0]              capture_size,
  output reg  [31:0]              capture_amount,
  output      [31:0]              capture_pos);

parameter IDLE          = 'd0;
parameter IN_CAPTURE    = 'd1;
parameter FINISH        = 'd2;


reg [31:0] next_capture_addr, capture_addr;
reg [31:0] next_capture_amount;
reg [1:0]  next_cap_state, cap_state;
reg        capture_wr;

assign capture_size = CAPTURE_SIZE;
assign capture_pos  = capture_addr;

always @(*)
begin
  next_cap_state    = cap_state;
  next_capture_addr = capture_addr;
  next_capture_amount = capture_amount;
  capture_wr        = 1'b0;
  case(cap_state)
    IDLE:
      if (capture_start) begin
        if (capture_data_valid)
        begin
          capture_wr        = 1'b1;
          next_capture_addr = capture_addr + 'd1;
          next_capture_amount = capture_amount + 'd1;
        end
        next_cap_state    = IN_CAPTURE;
      end
    IN_CAPTURE:
      if (capture_reset) begin
        next_cap_state    = IDLE;
        next_capture_addr = 'd0;
      end else if (capture_stop) begin
        next_cap_state    = FINISH;
      end else if (capture_data_valid && (capture_addr == (CAPTURE_SIZE-1)) && !capture_circular) begin
        next_cap_state    = FINISH;
        capture_wr        = 1'b1;
        next_capture_addr = capture_addr + 'd1;
        next_capture_amount = capture_amount + 'd1;
      end else if (capture_data_valid) begin
        capture_wr        = 1'b1;
        if (capture_addr == (CAPTURE_SIZE-1))
          next_capture_addr = 'd0;
        else
          next_capture_addr = capture_addr + 'd1;

        if (capture_amount == CAPTURE_SIZE)
          next_capture_amount = capture_amount;
        else
          next_capture_amount = capture_amount + 'd1;
      end
   FINISH:
     if (capture_reset) begin
        next_cap_state    = IDLE;
        next_capture_addr = 'd0;
        next_capture_amount = 'd0;
     end
  endcase
end

always @(posedge clk or posedge reset)
  if (reset) begin
    cap_state     <= IDLE;
    capture_addr  <= 'd0;
    capture_amount <= 'd0;
  end else begin
    cap_state     <= next_cap_state;
    capture_addr  <= next_capture_addr;
    capture_amount <= next_capture_amount;
  end

dual_port_ram #(.DATA_WIDTH   (CAPTURE_WIDTH),
                .MEM_DEPTH    (CAPTURE_SIZE)) capture_ram (
  .port_a_clk      (clk),
  .port_a_wr       (capture_wr),
  .port_a_addr     (capture_addr[$clog2(CAPTURE_SIZE)-1:0]),
  .port_a_din      (capture_data),
  .port_a_dout     (),
  .port_b_clk      (clk),
  .port_b_wr       (1'b0),
  .port_b_addr     (capture_rd_addr[$clog2(CAPTURE_SIZE)-1:0]),
  .port_b_din      ({(CAPTURE_WIDTH){1'b0}}),
  .port_b_dout     (capture_rd_data));

endmodule
