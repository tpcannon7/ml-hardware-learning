`timescale 1ns/1ps


/*
                    top_in   weight_in
                        |       |
                        V       V
                    ------------------      
                    |               |
left_side_in --->   |      PE       | ---> right_side_out
                    |               |
                    ------------------
                        |           |
                        |           |
                        V           V
                    weight_out    down_out
*/


module pe #(
    parameter int DATA_WIDTH = 8
) (
    input logic clk_in,
    input logic rst,
    input logic loading,

    input logic [(DATA_WIDTH*2)-1:0] top_in,
    input logic [DATA_WIDTH-1:0] left_side_in,
    input logic [DATA_WIDTH-1:0] weight_in,
    
    output logic [DATA_WIDTH-1:0] right_side_out,
    output logic [(DATA_WIDTH*2)-1:0] down_out,
    output logic [DATA_WIDTH-1:0] weight_out
);

logic [DATA_WIDTH-1:0] right_out_reg, inside_reg, weight_out_reg;
logic [(DATA_WIDTH*2)-1:0] down_out_reg, down_out_next;

always_ff @(posedge clk_in or posedge rst) begin
    if (rst) begin
        right_out_reg <= '0;
        down_out_reg <= '0;
        inside_reg <= '0;
        weight_out_reg <= '0;
    end else begin
        right_out_reg <= left_side_in;
        down_out_reg <= down_out_next;
        if (loading) begin
            inside_reg <= weight_in;
            weight_out_reg <= inside_reg;
        end
    end
end

always_comb begin
    if (~loading) begin
        down_out_next = (left_side_in * inside_reg) + top_in;
    end else begin
        down_out_next = '0;
    end
end

assign right_side_out = right_out_reg;
assign down_out = down_out_reg;
assign weight_out = weight_out_reg;

endmodule