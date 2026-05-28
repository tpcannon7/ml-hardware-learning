SIM ?= verilator
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES += $(PWD)/pe.sv $(PWD)/systolic.sv
COCOTB_TOPLEVEL = systolic
COCOTB_TEST_MODULES = systolic_tb

COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps

COMPILE_ARGS += -GDATA_WIDTH=8 -GN=8 --timescale 1ns/1ps
EXTRA_ARGS += --trace --trace-structs

WAVES=1

include $(shell cocotb-config --makefiles)/Makefile.sim