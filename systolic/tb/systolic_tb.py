import cocotb
from cocotb.triggers import RisingEdge, Timer, ReadOnly
from cocotb.clock import Clock

import numpy as np

# params
data_width = 8
N = 8

async def reset(dut):
    dut.rst.value = 0
    dut.loading.value = 0
    dut.left_side_in.value = 0
    dut.weights_in.value = 0
    dut.valid_in.value = 0

    dut.rst.value = 1
    for _ in range(3): await RisingEdge(dut.clk_in)
    dut.rst.value = 0

def pack(vector):
    temp = 0
    for i,val in enumerate(vector):
        val = val << data_width * i
        temp = temp | val
    return temp

def unpack(scalar):
    temp = np.zeros(N, dtype=np.int32)
    for i in range(N):
         temp[i] = (scalar & 0xffff)
         scalar = scalar >> data_width * 2

    return temp

#@cocotb.test
async def test_matmul(dut):
    clk = Clock(dut.clk_in, 10, "ns")
    clk.start()

    rng = np.random.default_rng()

    await reset(dut)

    for _ in range(100):
        weights = rng.integers(low=0, high=(2**data_width - 1), size=(N,N))
        cocotb.log.info(f"weights={weights}")
        left_in = rng.integers(low=0, high=(2**data_width - 1), size=N)
        cocotb.log.info(f"left_in={left_in}")

        dut.loading.value = 1
        for i in range(N-1,-1,-1):
            cocotb.log.info(f"weight {i}={weights[i,:]}")
            dut.weights_in.value = int(pack(weights[i,:]))
            await RisingEdge(dut.clk_in)
            await Timer(1, "ns")
            await RisingEdge(dut.clk_in)
            await Timer(1, "ns")

        assert dut.load_done.value == 1

        dut.loading.value = 0
        dut.left_side_in.value = int(pack(left_in))
        dut.valid_in.value = 1
        await RisingEdge(dut.clk_in)
        await Timer(1,"ns")
        dut.valid_in.value = 0

        for _ in range(3*N):
            await RisingEdge(dut.clk_in)
            await Timer(1, "ns")
            if dut.valid_out.value == 1:
                break
        assert dut.valid_out.value == 1

        await RisingEdge(dut.clk_in)
        await Timer(1,"ns")

        cocotb.log.info(f"raw={hex(int(dut.res.value))}")
        out = unpack(int(dut.accumulate_out.value))
        expected = (left_in @ weights) & 0xffff
        cocotb.log.info(f"out={out}")
        cocotb.log.info(f"expected={expected}")
        assert np.array_equal(out, expected)

#@cocotb.test
async def b2b_matmul_test(dut):
    clk = Clock(dut.clk_in, 10, "ns")
    clk.start()
    rng = np.random.default_rng()

    await reset(dut)

    for _ in range (100):
        in1 = rng.integers(low=0, high=(2**data_width - 1), size=N)
        cocotb.log.info(f"in1={in1}")
        in2 = rng.integers(low=0, high=(2**data_width - 1), size=N)
        cocotb.log.info(f"in2={in2}")
        weights = rng.integers(low=0, high=(2**data_width - 1), size=(N,N))
        cocotb.log.info(f"weights={weights}")

        expected1 = (in1 @ weights) & 0xffff
        expected2 = (in2 @ weights) & 0xffff

        dut.loading.value = 1
        for i in range(N-1,-1,-1):
            dut.weights_in.value = int(pack(weights[i,:]))
            await RisingEdge(dut.clk_in)
            await Timer(1, "ns")
            await RisingEdge(dut.clk_in)
            await Timer(1, "ns")
        assert dut.load_done.value == 1

        dut.loading.value = 0

        dut.left_side_in.value = int(pack(in1))
        dut.valid_in.value = 1
        await RisingEdge(dut.clk_in)
        await Timer(1,"ns")
        dut.valid_in.value = 0

        for _ in range(3*N):
            await RisingEdge(dut.clk_in)
            await Timer(1, "ns")
            if dut.valid_out.value == 1:
                break
        assert dut.valid_out.value == 1

        await RisingEdge(dut.clk_in)
        await Timer(1,"ns")

        out1 = unpack(int(dut.accumulate_out.value))
        cocotb.log.info(f"out={out1}")
        cocotb.log.info(f"exp={expected1}")
        assert np.array_equal(out1,expected1)

        dut.left_side_in.value = int(pack(in2))
        dut.valid_in.value = 1
        await RisingEdge(dut.clk_in)
        await Timer(1,"ns")
        dut.valid_in.value = 0

        for _ in range(3*N):
            await RisingEdge(dut.clk_in)
            await Timer(1, "ns")
            if dut.valid_out.value == 1:
                break
        assert dut.valid_out.value == 1

        await RisingEdge(dut.clk_in)
        await Timer(1,"ns")

        out2 = unpack(int(dut.accumulate_out.value))
        cocotb.log.info(f"out={out2}")
        cocotb.log.info(f"exp={expected2}")
        assert np.array_equal(out2,expected2)

@cocotb.test
async def pipeline_test(dut):
    clk = Clock(dut.clk_in, 10, "ns")
    clk.start()
    rng = np.random.default_rng()
    num_inputs = 16

    await reset(dut)

    inputs = rng.integers(low=0, high=(2**data_width)-1, size=(num_inputs,N))
    weights = rng.integers(low=0, high=(2**data_width)-1, size=(N,N))
    expected = (inputs @ weights) & 0xffff

    cocotb.log.info(f"weights={weights}")
    cocotb.log.info(f"expected(big)={expected}")

    
    dut.loading.value = 1
    for i in range(N-1,-1,-1):
            dut.weights_in.value = int(pack(weights[i,:]))
            await RisingEdge(dut.clk_in)
            await RisingEdge(dut.clk_in)
            await Timer(1, "ns")
    assert dut.load_done.value == 1
    dut.loading.value = 0

    count = 0
    while(True):
        slice = inputs[count:count+N, :]
        for i,v in enumerate(slice):
            cocotb.log.info(f"input: {count+i}, {v}")
            dut.left_side_in.value = int(pack(v))
            dut.valid_in.value = 1
            await RisingEdge(dut.clk_in)
            await Timer(1, "ns")

        dut.valid_in.value = 0

        for _ in range(N-1):
            await RisingEdge(dut.clk_in)
            await Timer(1,"ns") 
        
        for i in range(N):
            assert dut.valid_out.value == 1
            out = unpack(int(dut.accumulate_out.value))
            exp = expected[count:count+N,:]
            cocotb.log.info(f"out {count+i}={out}")
            cocotb.log.info(f"expected {count+i}={exp[i]}")
            #assert np.array_equal(out,exp)
            await RisingEdge(dut.clk_in)
            await Timer(1,"ns")

        count = count + N
        if (count >= num_inputs):
            break
