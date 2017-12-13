import getopt
import sys
import os

def to_bin(data, len):
  op = ""
  for i in range(len):
    if (data>>i)&0x1:
      op = "1" + op
    else:
      op = "0" + op
  return(op)

def read_in_signals_file(filename, signals):
  fh = open(filename, "r")

  for line in fh:
    data = line.rstrip().split()
    signals.append((data[0], int(data[1])))

def expand_signals_file(signals):
  signals_exp = []
  offset = 0
  for item in signals:
    signals_exp.append((item[0], item[1], offset))
    offset += item[1]
  return signals_exp

def write_capture_wrapper(signals, capture_buffer_size):
  capture_data_size = signals[-1][2] + signals[-1][1]

  cap_fh = open("capture_wrapper.v", "w")
  cap_fh.write("""module capture_wrapper (
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
""")

  for index, item in enumerate(signals):
    if index>0:
      cap_fh.write(",")
    cap_fh.write("\n  input       [%s:0]             %s" % ("{:>3}".format("%d"%item[1]), item[0]))

  cap_fh.write(");\n\n")

  cap_fh.write("parameter CAPTURE_WIDTH = %d;\n" % (signals[-1][2]+signals[-1][1]))
  cap_fh.write("wire [CAPTURE_WIDTH-1:0]  capture_data;\n\n")

  data_cat = ""
  for index, item in enumerate(signals[::-1]):
    if index>0:
      data_cat += ","
    data_cat += item[0]

  cap_fh.write("assign capture_data = {%s};\n\n" % data_cat)

  cap_fh.write("""my_capture #(.CAPTURE_WIDTH    (%d),
             .CAPTURE_SIZE     (%d)) capture_block (
  .clk                 (clk),
  .reset               (reset),
  .capture_data        (capture_data),
  .capture_data_valid  (capture_valid),
  .capture_start       (capture_start),
  .capture_circular    (capture_circular),
  .capture_stop        (capture_stop),
  .capture_rd_addr     (capture_rd_addr),
  .capture_reset       (capture_reset),
  .capture_size        (capture_size),
  .capture_amount      (capture_amount),
  .capture_pos         (capture_pos));
""" % (capture_data_size,
       capture_buffer_size))

  cap_fh.write("\nendmodule\n")
  cap_fh.close()

def get_captured_data(filename, captured_data):
  cap_fh = open(filename, "r")
  for line in cap_fh:
    captured_data.append(int(line,16))

def create_vcd(vcd_file, captured_data, signals):
  vcd_fh = open(vcd_file, "w")  
  vcd_fh.write("""
  $date
     Date text. For example: November 11, 2009.
  $end
  $version
     VCD generator tool version info text.
  $end
  $comment
     Any comment text.
  $end
  $timescale 1ps $end
  $scope module logic $end
  """)
  
  items = []
  for index, item in enumerate(signals):
    items.append((item[0], item[1], item[2], chr((0x41+index)&0xff)))
    vcd_fh.write("$var wire %d %s %s $end\n" % (item[1], chr((0x41+index)&0xff), item[0]))
  
  vcd_fh.write("""
  $upscope $end
  $enddefinitions $end
  $dumpvars
  """)
 
  count = 1
  for data in captured_data:
    for item in items:
      data_tmp = (data>>item[2])&((1<<item[1])-1)
      vcd_fh.write("b%s %s\n"%(to_bin(data_tmp, item[1]), item[3]))
    vcd_fh.write("#%d\n" % count)
    count += 1

def print_usage():
  print """
capture.py --help --signals_file=fn --buffer_size=value --captured_data=fn --vcd_name=fn --gen_wrapper --process_data
   --help:           print this message
   --signals_file:   name of file containing signals to capture
   --buffer_size:    size of buffer (defaults to 1024), block ram usage is size of buffer * total signals size
   --captured_data:  name of file containing captured data
   --vcd_name:       name of vcd file to write
   --gen_wrapper:    generate the verilog wrapper for the capture block, requires signals_file to be defined
   --process_data:   generate the vcd file from the captured data, requires signals_file, captured_data, vcd_name 
"""

if __name__ == "__main__":
  opts, args = getopt.getopt(sys.argv[1:], "", ["help", "signals_file=", "buffer_size=", "captured_data=", "vcd_name=", "gen_wrapper", "process_data"])

  buffer_size            = 1024
  signals_file           = None
  captured_data_filename = None
  vcd_name               = None
  gen_wrapper            = False
  process_data           = False

  for o,a in opts:
    if   o == "--signals_file":
      signals_file = a
    elif o == "--buffer_size":
      buffer_size = int(a)
    elif o == "--captured_data":
      captured_data_filename = a
    elif o == "--vcd_name":
      vcd_name = a
    elif o == "--gen_wrapper":
      gen_wrapper = True
    elif o == "--process_data":
      process_data = True
    elif o == "--help":
      print_usage()
      sys.exit()

  signals = []
  if signals_file is None:
    print_usage()
    print "ERROR: signals_file is not defined"
    sys.exit()

  read_in_signals_file(signals_file, signals)
  signals_exp =  expand_signals_file(signals)

  if gen_wrapper:
    write_capture_wrapper(signals_exp, buffer_size)
  elif process_data:

    if vcd_name is None:
      print_usage()
      print "ERROR: vcd_name is not defined"
      sys.exit()

    if captured_data_filename is None:
      print_usage()
      print "ERROR: captured_data is not defined"
      sys.exit()

    captured_data = []
    get_captured_data(captured_data_filename, captured_data)
    create_vcd(vcd_name, captured_data, signals_exp)
  


