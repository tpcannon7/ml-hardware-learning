`timescale 1ns/1ps

module pe_tb #()();

localparam DATA_WIDTH = 8;

logic clk_in, rst_ni, loading;

logic [(DATA_WIDTH*2)-1:0] top_in, down_out;
logic [DATA_WIDTH-1:0] left_side_in, weight_in, right_side_out;

initial clk_in = 0;
always #5 clk_in = ~clk_in;

pe #(.DATA_WIDTH(DATA_WIDTH)) dut (.*);

initial begin
    loading = 0;
    weight_in = 8'h00;
    top_in = 16'h0000;
    left_side_in = 8'h00;

    rst_ni = 0;
    @(posedge clk_in);
    @(posedge clk_in); // reset
    @(posedge clk_in); // reset

    rst_ni = 1;

    $display("after reset: down_out=%0d", down_out);
    
    loading = 1;
    weight_in = 8'hff;
    @(posedge clk_in);
    $display("after weight load: down_out=%0d, inside_reg should be 1", down_out);
    
    loading = 0;
    top_in = 16'h0000;
    left_side_in = 8'hff;
    @(posedge clk_in);
    $display("after compute cycle 1: down_out=%0d", down_out);
    @(posedge clk_in);
    $display("after compute cycle 2: down_out=%0d", down_out);
    $finish;
end


endmodule