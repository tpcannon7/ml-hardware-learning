`timescale 1ns/1ps

module systolic #(
    parameter int DATA_WIDTH = 8,
    parameter int N = 8 // NxN array
) (
    input logic clk_in,
    input logic rst,
    input logic loading,

    input logic valid_in,
    input logic [N-1:0][DATA_WIDTH-1:0] left_side_in,
    input logic [N-1:0][DATA_WIDTH-1:0] weights_in,

    output logic [N-1:0][(DATA_WIDTH*2)-1:0] accumulate_out,
    output logic [N-1:0][(DATA_WIDTH*2)-1:0] res,
    output logic load_done,
    output logic valid_out
);

localparam DELAY_CYCLES = 2*N;

typedef enum logic[2:0] {  
    IDLE,
    LOADING
} state_t;

state_t next_state, curr_state;

logic [$clog2(N*2):0] cnt;

always_ff @(posedge clk_in or posedge rst) begin
    if (rst) begin
        curr_state <= IDLE;
        cnt <= '0;
    end else begin
        curr_state <= next_state;
        if (curr_state != next_state) begin
            cnt <= '0;
        end else if (curr_state == LOADING) begin
            cnt <= cnt + 1;
        end
    end
end

always_comb begin
    next_state = curr_state;
    case(curr_state)
        IDLE: if (loading) next_state = LOADING;
        LOADING: if (cnt == $bits(cnt)'(DELAY_CYCLES-1)) next_state = IDLE;
        default: next_state = curr_state;
    endcase
end

assign load_done = curr_state == LOADING && cnt == $bits(cnt)'(DELAY_CYCLES-1);

logic [(2*N)-2:0] valid_out_pipe;
always_ff @(posedge clk_in or posedge rst) begin
    if (rst) begin
        valid_out_pipe <= '0;
    end else begin
        valid_out_pipe <= {valid_out_pipe[(2*N)-3:0], valid_in};
    end
end

assign valid_out = valid_out_pipe[(2*N)-2];

logic [N-1:0][N-1:0][(DATA_WIDTH*2)-1:0] prop_down_out;
logic [N-1:0][N-1:0][DATA_WIDTH-1:0] prop_right_out, prop_weights_out;
logic [N-1:0][N-1:0][DATA_WIDTH-1:0] skew_regs;
logic [N-1:0][N-1:0][(DATA_WIDTH*2)-1:0] deskew_regs;

genvar i,j;
generate
    for (i = 0; i < N; i++) begin : skew_gen
        always_ff @(posedge clk_in or posedge rst) begin
            if (rst) begin
                skew_regs[i] <= {N{{DATA_WIDTH{1'b0}}}};
            end else begin
                if (i > 0) begin
                    skew_regs[i][i-1] <= left_side_in[i];
                    for (int s = i-1; s > 0; s--) begin
                        skew_regs[i][s-1] <= skew_regs[i][s];
                    end
                end
            end
        end
        for (j = 0; j < N; j++) begin : pe_gen
            pe #(.DATA_WIDTH(DATA_WIDTH)) array (
                .clk_in(clk_in),
                .rst(rst),
                .loading(loading),
                .top_in(i == 0 ? {(DATA_WIDTH*2){1'b0}} : prop_down_out[i-1][j]),
                .left_side_in(j == 0 ? (i == 0 ? left_side_in[0] : skew_regs[i][0]) : prop_right_out[i][j-1]),
                .weight_in(i == 0 ? weights_in[j] : prop_weights_out[i-1][j]),
                .right_side_out(prop_right_out[i][j]),
                .down_out(prop_down_out[i][j]),
                .weight_out(prop_weights_out[i][j])
            );
        end
    end
endgenerate

generate
    for (j = 0; j < N-1; j++) begin : deskew_gen
        always_ff @(posedge clk_in or posedge rst) begin
            if (rst) begin
                for (int s = 0; s < N-1-j; s++)
                    deskew_regs[s][j] <= '0;
            end else begin
                deskew_regs[0][j] <= prop_down_out[N-1][j];
                for (int s = 1; s < N-1-j; s++)
                    deskew_regs[s][j] <= deskew_regs[s-1][j];
            end
        end
    end
endgenerate

generate
    for (j = 0; j < N; j++) begin : out_assign
        if (j == N-1)
            assign accumulate_out[j] = prop_down_out[N-1][j];
        else
            assign accumulate_out[j] = deskew_regs[N-2-j][j];
    end
endgenerate

endmodule
