# fpga_capture_block
## Poor mans signaltap/chipscope

So you put your design into the FPGA and it doesn't do what you expect it to do, what do you do next.  One option is to look at your design, find some
signals that you think will help you to get to the bottom of the issue, mark them for debug, resynthesize and use Vivado to insert an ILA core for the
issue.  I got fed up fo using this as occasionally it messes with the signal names and I find it a bit fiddly to use.  It also requires that you can connect
to your FPGA via JTAG which is not always possible.  I developed a simple debug block that can be used in a variety of ways to get some visibility of whats going
on:

Usually FPGA debug requires a bit of inventiveness to try and catch the issue.  I tend to use it in a few different modes:

### 1. capture the data on a bus (say for example capture a few metwork packets on the avalon bus):

just wire the capture_valid signal to the bus valid signal.

### 2. capture until we have a trigger fired (this will give us some extra cycles after the trigger too):

```
    parameter CYCLES_AFTER_TRIGGER = 100;
    
    assign capture_valid     = cap_count == CYCLES_AFTER_TRIGGER ? 'd0 :
                               cap_count;
    assign next_cap_count    = cap_trigger                       ? 'd1 :
                               cap_count == CYCLES_AFTER_TRIGGER ? 'd0 :
                               cap_count == 'd0                  ? 'd0 :
                               cap_count + 'd1;
```    

### 3. capture multiple times for n-cycles:

create a signal for starting capture and define a time for the capture:

This code snippit will generate a capture of n-cycles everytime the trigger fires until the buffer fills:

    parameter CAP_CYCLES = 100;  //
    wire cap_start;              // capture_start_trigger
    
    assign capture_valid    = cap_start              ? 1'b1 :
                              cap_count = CAP_CYCLES ? 1'b0 :
                              capture_valid_reg;
    
    assign next_cap_count   = cap_start               ? 'd1  :
                              cap_count == CAP_CYCLES ? 'd0  :
                              cap_count == 'd0        ? 'd0  :
                              cap_count + 'd1;
    

The script capture.py can be used to create a wrapper for your design and also can be used to generate the vcd file from the captured data.   First you need to create a signals file.  This contains a list of signal names you want to capture and the sizes of these signals:

for example:

    signal1 1
    signal2 2
    signal3 16

Then you can generate a wrapper file using:

    python capture.py --signals_file=signals --gen_wrapper

this will generate a wrapper file called capture_wrapper with a module prototype:

    module capture_wrapper (
      input                           clk,
      input                           reset,
    
      input                           capture_circular,
      input                           capture_stop,
    
      input       [31:0]              capture_rd_addr,
      input                           capture_reset,
      output      [CAPTURE_WIDTH-1:0] capture_rd_data,
      output      [31:0]              capture_size,
      output      [31:0]              capture_amount,
      output      [31:0]              capture_pos,
    
      input                           capture_start,
      input                           capture_valid,
    
      input       [  1:0]             signal1,
      input       [  2:0]             signal2,
      input       [ 16:0]             signal3);


You need to connect capture_rd_addr, capture_reset, capture_rd_data, capture_size, capture_amount and capture_pos to the memory mapped register interface for your FPGA (I'm guessing most FPGA designs have some mechanism for reading and writing registers) and then read the data out of the buffer by doing something like this:

    void read_out_buffer() {
    
      int i;
    
      int pos  = IORD(CAPTURE_POS);
      int size = IORD(CAPTURE_SIZE);
      int amount = IORD(CAPTURE_AMOUNT);
      uint32_t data_0, data_1, data_2;
    
      int start_pos = (amount < size) ? 0 : pos+1;
      for (i=0; i<amount; i+=1) {
        IOWR(0, CAPTURE_RD_ADDR, (start_pos+i)%size);
        data_0 = IORD(CAPTURE_RD_DATA_0);
        data_1 = IORD(CAPTURE_RD_DATA_1);
    
        printf("%8.8x%8.8x\n", data_1, data_0);
      }
    
      IOWR(0, CAPTURE_RESET, 1);
      IOWR(0, CAPTURE_RESET, 0);
    
    }

once you have the captured data, you can create the vcd by doing:

    python capture.py --signals_file=signals --captured_data=capture_data.txt --vcd_name=op.vcd --process_data
