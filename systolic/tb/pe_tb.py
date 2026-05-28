import cocotb
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from cocotb.clock import Clock
import random

async def reset(dut):
    dut.rst.value = 0
    dut.loading.value = 0
    dut.top_in.value = 0
    dut.left_side_in.value = 0
    dut.weight_in.value = 0

    dut.rst.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk_in)
    dut.rst.value = 0

@cocotb.test()
async def test_weights(dut):
    prev_weight_in = 0

    clk = Clock(dut.clk_in, 10, "ns")
    clk.start()
    await reset(dut)

    for _ in range(100):
        weight_in = random.randint(0,(2**8)-1)
        cocotb.log.info(f"----------------------------------")
        cocotb.log.info(f"prev_weight_in={prev_weight_in}")
        cocotb.log.info(f"weight_in={weight_in}")
        

        dut.loading.value = 1
        dut.weight_in.value = weight_in
        await RisingEdge(dut.clk_in)
        await Timer(1, "ns")
        
        assert dut.weight_out.value == prev_weight_in

        await RisingEdge(dut.clk_in)
        await Timer(1, "ns")
        cocotb.log.info(f"weigh_out={int(dut.weight_out.value)}")
        assert dut.weight_out.value == weight_in

        prev_weight_in = weight_in



@cocotb.test()
async def test_pe(dut):
    clk = Clock(dut.clk_in, 10, "ns")
    clk.start()
    await reset(dut)

    for _ in range (100):
        left_in = random.randint(0,(2**8)-1)
        top_in = random.randint(0,(2**16)-1)
        weight_in = random.randint(0,(2**8)-1)

        cocotb.log.info(f"left={left_in},top_in={top_in},weight_in={weight_in}")

        dut.loading.value = 1
        dut.weight_in.value = weight_in
        await RisingEdge(dut.clk_in)
        await Timer(1, "ns")

        dut.loading.value = 0
        dut.top_in.value = top_in
        dut.left_side_in.value = left_in
        await RisingEdge(dut.clk_in)
        await Timer(1, "ns")
        cocotb.log.info(f"down_out=%d",dut.down_out.value)
        await RisingEdge(dut.clk_in)
        await Timer(1, "ns")
        cocotb.log.info(f"down_out=%d",dut.down_out.value)

        assert dut.down_out.value == ((left_in*weight_in) + top_in) & 0xffff
        


