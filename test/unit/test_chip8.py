import random

import pytest

from CHIP8 import CHIP8


@pytest.fixture
def cpu_with_memory(instructions):
    cpu = CHIP8()
    assert all(b == 0 for b in cpu.MEMORY[cpu.PC_START_OFFSET :])
    cpu.MEMORY = cpu.MEMORY[:0x200] + [int(b) for b in instructions]
    yield cpu
    cpu.reset()
    cpu.MEMORY = [0] * 4096


@pytest.mark.parametrize(
    "instructions",
    [
        b"some_bytes",
        [0x0, 0x12, 0x11, 0x1E],
    ],
)
def test_load_instruction(instructions, cpu_with_memory):
    i = 0
    while i < len(instructions):
        instruction = cpu_with_memory.load_instruction()
        assert instruction == instructions[i] << 8 | instructions[i + 1]
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize("instructions", [[96, 10], [101, 170]])
def test_LD(instructions, cpu_with_memory):
    i = 0
    while i < len(instructions):
        cpu_with_memory.execute()
        register_index = ((instructions[0] << 8 | instructions[1]) & 0x0F00) >> 8
        assert cpu_with_memory.REGISTERS["GPR"][register_index] == instructions[1]
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize("instructions", [[0x10, 0xFD], [31, 74]])
def test_JP(instructions, cpu_with_memory):
    i = 0
    while i < len(instructions):
        cpu_with_memory.execute()
        assert (instructions[0]) >> 4 == 0x1
        assert (
            cpu_with_memory.REGISTERS["pc"]
            == (instructions[0] << 8 | instructions[1]) & 0x0FFF
        )
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize(
    "instructions",
    [
        [0xB0, 0xFD],
    ],
)
def test_JP_V0(instructions, cpu_with_memory):
    """
    Bnnn - JP V0, addr
    Jump to location nnn + V0.
    The program counter is set to nnn plus the value of V0.
    """
    V0_value = random.randint(0, 255)
    cpu_with_memory.REGISTERS["GPR"][0] = V0_value
    i = 0
    while i < len(instructions):
        cpu_with_memory.execute()
        expected_instruction = instructions[0] << 8 | instructions[1]
        assert cpu_with_memory.current_instruction == expected_instruction
        assert (
            cpu_with_memory.REGISTERS["pc"]
            == (expected_instruction & 0x0FFF) + V0_value
        )
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize(
    "instructions",
    [
        [0xA0, 0xFD],
    ],
)
def test_LD_I(instructions, cpu_with_memory):
    """
    Annn - LD I, addr
    Set I = nnn.
    The value of register I is set to nnn.
    """
    i = 0
    while i < len(instructions):
        cpu_with_memory.execute()
        expected_instruction = instructions[0] << 8 | instructions[1]
        assert cpu_with_memory.current_instruction == expected_instruction

        assert cpu_with_memory.REGISTERS["I"] == (expected_instruction & 0x0FFF)
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize("instructions", [[0x90, 0x10], [0x94, 0x30]])
def test_SNE_REG_REG(instructions, cpu_with_memory):
    """
    9xy0 - SNE Vx, Vy
    Skip next instruction if Vx != Vy.
    The values of Vx and Vy are compared, and if they are not equal, the program counter is increased by 2.
    :return: None
    """
    i = 0
    while i < len(instructions):
        curr_pc_val = cpu_with_memory.REGISTERS["pc"]
        expected_instruction = instructions[0] << 8 | instructions[1]
        x = (expected_instruction & 0x0F00) >> 8
        y = (expected_instruction & 0x00F0) >> 4
        cpu_with_memory.REGISTERS["GPR"][x] = 1
        cpu_with_memory.REGISTERS["GPR"][y] = 1

        cpu_with_memory.execute()
        curr_pc_val += len(instructions)  # ps = ps + 2
        assert cpu_with_memory.current_instruction == expected_instruction

        # should not increment because pc vx == vy
        assert cpu_with_memory.REGISTERS["pc"] == curr_pc_val

        cpu_with_memory.REGISTERS["GPR"][x] = 123
        cpu_with_memory.REGISTERS["GPR"][y] = 10
        cpu_with_memory.SNE_REG_REG()
        assert cpu_with_memory.REGISTERS["pc"] == curr_pc_val + 2
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize("instructions", [[0x40, 30], [0x44, 11]])
def test_SNE_REG_VAL(instructions, cpu_with_memory):
    """
    4xkk - SNE Vx, byte
    Skip next instruction if Vx != kk.
    The interpreter compares register Vx to kk, and if they are not equal, increments the program counter by 2.

    :return:
    """
    i = 0
    while i < len(instructions):
        curr_pc_val = cpu_with_memory.REGISTERS["pc"]
        expected_instruction = instructions[0] << 8 | instructions[1]
        x = (expected_instruction & 0x0F00) >> 8
        cpu_with_memory.REGISTERS["GPR"][x] = instructions[1]
        cpu_with_memory.execute()
        curr_pc_val += 2  # pc = pc + 2 after loading 2 bytes of instruction
        assert cpu_with_memory.current_instruction == expected_instruction
        assert cpu_with_memory.REGISTERS["pc"] == curr_pc_val

        cpu_with_memory.REGISTERS["GPR"][x] = 123
        cpu_with_memory.SNE_REG_VAL()
        assert cpu_with_memory.REGISTERS["pc"] == curr_pc_val + 2
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize("instructions", [[0x30, 30], [0x34, 11]])
def test_SE_REG_VAL(instructions, cpu_with_memory):
    """
    3xkk - SE Vx, byte
    Skip next instruction if Vx = kk.
    The interpreter compares register Vx to kk, and if they are equal, increments the program counter by 2.
    """
    i = 0
    while i < len(instructions):
        curr_pc_val = cpu_with_memory.REGISTERS["pc"]
        expected_instruction = instructions[0] << 8 | instructions[1]
        x = (expected_instruction & 0x0F00) >> 8
        cpu_with_memory.REGISTERS["GPR"][x] = instructions[1]
        cpu_with_memory.execute()
        curr_pc_val += 2  # pc = pc + 2 after loading 2 bytes of instruction
        assert cpu_with_memory.current_instruction == expected_instruction
        # should increment because cpu_with_memory.REGISTERS['GPR'][x] = instructions[1]
        assert cpu_with_memory.REGISTERS["pc"] == curr_pc_val + 2
        curr_pc_val += 2

        cpu_with_memory.REGISTERS["GPR"][x] = 123
        # should not increment because cpu_with_memory.REGISTERS['GPR'][x] != instructions[1]
        cpu_with_memory.SE_REG_VAL()
        assert cpu_with_memory.REGISTERS["pc"] == curr_pc_val
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize("instructions", [[0x50, 30], [0x54, 10]])
def test_SE_REG_REG(instructions, cpu_with_memory):
    """
    5xy0 - SE Vx, Vy
    Skip next instruction if Vx = Vy.
    The interpreter compares register Vx to register Vy, and if they are equal, increments the program counter by 2.

    :return: None
    """
    i = 0
    while i < len(instructions):
        curr_pc_val = cpu_with_memory.REGISTERS["pc"]
        expected_instruction = instructions[0] << 8 | instructions[1]
        x = (expected_instruction & 0x0F00) >> 8
        y = (expected_instruction & 0x00F0) >> 4
        cpu_with_memory.REGISTERS["GPR"][x] = 1
        cpu_with_memory.REGISTERS["GPR"][y] = 1

        cpu_with_memory.execute()
        curr_pc_val += len(instructions)  # ps = ps + 2
        assert cpu_with_memory.current_instruction == expected_instruction

        # should not increment because pc vx == vy
        assert cpu_with_memory.REGISTERS["pc"] == curr_pc_val + 2
        curr_pc_val += 2

        cpu_with_memory.REGISTERS["GPR"][x] = 123
        cpu_with_memory.REGISTERS["GPR"][y] = 10
        cpu_with_memory.SE_REG_REG()
        assert cpu_with_memory.REGISTERS["pc"] == curr_pc_val
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize("instructions", [[0x21, 23], [0x20, 11]])
def test_CALL(instructions, cpu_with_memory):
    """
    2nnn
    Call subroutine at nnn. The interpreter increments the stack pointer, then puts the current PC on the top of
    the stack. The PC is then set to nnn.

    :return: None
    """
    i = 0
    while i < len(instructions):
        expected_instruction = instructions[0] << 8 | instructions[1]
        pc_value_to_push = cpu_with_memory.REGISTERS["pc"]

        cpu_with_memory.execute()
        assert cpu_with_memory.current_instruction == expected_instruction
        stack_pointer = len(cpu_with_memory.REGISTERS["stack"].items) - 1
        assert cpu_with_memory.REGISTERS["stack"].items[
            stack_pointer
        ] == pc_value_to_push + len(instructions)
        assert cpu_with_memory.REGISTERS["pc"] == expected_instruction & 0x0FFF
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize("instructions", [[0x00, 0xEE], [0x00, 0xEE]])
def test_RET(instructions, cpu_with_memory):
    """
    00EE - RET Return from a subroutine. The interpreter sets the program counter to the address at the top of
    the stack, then subtracts 1 from the stack pointer.
    """
    i = 0
    while i < len(instructions):
        expected_instruction = instructions[0] << 8 | instructions[1]
        cpu_with_memory.REGISTERS["stack"].push(0x0231)
        stack_top_value = cpu_with_memory.REGISTERS["stack"].items[-1]
        cpu_with_memory.execute()

        assert cpu_with_memory.current_instruction == expected_instruction
        assert cpu_with_memory.REGISTERS["pc"] == stack_top_value
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize("instructions", [[0x61, 0xEE], [0x63, 0xAA]])
def test_LD_REG_VAL(instructions, cpu_with_memory):
    """
    6xkk - LD Vx, byte
    Set Vx = kk.
    The interpreter puts the value kk into register Vx.
    """
    i = 0
    while i < len(instructions):
        expected_instruction = instructions[0] << 8 | instructions[1]
        x = (expected_instruction & 0x0F00) >> 8
        cpu_with_memory.execute()

        assert cpu_with_memory.current_instruction == expected_instruction
        assert cpu_with_memory.REGISTERS["GPR"][x] == instructions[1]
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize(
    "instructions",
    [
        [0x81, 0x20],  # LD REG REG
        [0x81, 0x21],  # OR
        [0x81, 0x22],  # AND
        [0x81, 0x23],  # XOR
        [0x81, 0x24],  # ADD
        [0x81, 0x25],  # SUB
        [0x81, 0x26],  # SHR
        [0x81, 0x27],  # SUBN
        [0x81, 0x2E],  # SHL
    ],
)
def test_ld_or_logic_instructions(instructions, cpu_with_memory):
    """
    8xy0 - LD Vx, Vy
    Set Vx = Vy.
    Stores the value of register Vy in register Vx.

    8xy1 - OR Vx, Vy
    Set Vx = Vx OR Vy.
    Performs a bitwise OR on the values of Vx and Vy, then stores the result in Vx. A bitwise OR compares the corrseponding bits from two values, and if either bit is 1, then the same bit in the result is also 1. Otherwise, it is 0.

    8xy2 - AND Vx, Vy
    Set Vx = Vx AND Vy.
    Performs a bitwise AND on the values of Vx and Vy, then stores the result in Vx. A bitwise AND compares the corrseponding bits from two values, and if both bits are 1, then the same bit in the result is also 1. Otherwise, it is 0.


    8xy3 - XOR Vx, Vy
    Set Vx = Vx XOR Vy.
    Performs a bitwise exclusive OR on the values of Vx and Vy, then stores the result in Vx. An exclusive OR compares the corrseponding bits from two values, and if the bits are not both the same, then the corresponding bit in the result is set to 1. Otherwise, it is 0.

    8xy4 - ADD Vx, Vy
    Set Vx = Vx + Vy, set VF = carry.
    The values of Vx and Vy are added together. If the result is greater than 8 bits (i.e., > 255,) VF is set to 1, otherwise 0. Only the lowest 8 bits of the result are kept, and stored in Vx.

    8xy5 - SUB Vx, Vy
    Set Vx = Vx - Vy, set VF = NOT borrow.
    If Vx > Vy, then VF is set to 1, otherwise 0. Then Vy is subtracted from Vx, and the results stored in Vx.

    8xy6 - SHR Vx {, Vy}
    Set Vx = Vx SHR 1.
    If the least-significant bit of Vx is 1, then VF is set to 1, otherwise 0. Then Vx is divided by 2.

    8xy7 - SUBN Vx, Vy
    Set Vx = Vy - Vx, set VF = NOT borrow.
    If Vy > Vx, then VF is set to 1, otherwise 0. Then Vx is subtracted from Vy, and the results stored in Vx.

    8xyE - SHL Vx {, Vy}
    Set Vx = Vx SHL 1.
    If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0. Then Vx is multiplied by 2.
    """
    func = None
    last = instructions[1] & 0x0F
    if last == 0:

        def func(x_val, y_val):
            return y_val, 0

    elif last == 0x01:

        def func(x_val, y_val):
            return x_val | y_val, 0

    elif last == 0x02:

        def func(x_val, y_val):
            return x_val & y_val, 0

    elif last == 0x03:

        def func(x_val, y_val):
            return x_val ^ y_val, 0

    elif last == 0x04:

        def func(x_val, y_val):
            return (x_val + y_val) % 256, (x_val + y_val) >= 256

    elif last == 0x05:

        def func(x_val, y_val):
            if x_val > y_val:
                res = x_val - y_val
            else:
                res = 256 + x_val - y_val
            return res, x_val > y_val

    elif last == 0x06:

        def func(x_val, y_val):
            return x_val >> 1, x_val & 0x1

    elif last == 0x07:

        def func(x_val, y_val):
            if y_val < x_val:
                res = 256 + (y_val - x_val)
            else:
                res = y_val - x_val
            return res, y_val > x_val

    elif last == 0x0E:

        def func(x_val, y_val):
            return x_val << 1, (x_val & 0x80) >> 8

    i = 0
    while i < len(instructions):
        expected_instruction = instructions[0] << 8 | instructions[1]
        x = (expected_instruction & 0x0F00) >> 8
        y = (expected_instruction & 0x00F0) >> 4
        val_x = random.randint(0, 255)
        val_y = random.randint(0, 255)
        cpu_with_memory.REGISTERS["GPR"][x] = val_x
        cpu_with_memory.REGISTERS["GPR"][y] = val_y

        cpu_with_memory.execute()
        assert cpu_with_memory.current_instruction == expected_instruction

        val, flag = func(val_x, val_y)
        assert cpu_with_memory.REGISTERS["GPR"][x] == val
        assert cpu_with_memory.REGISTERS["GPR"][-1] == flag
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize("instructions", [[0x71, 0xEE], [0x75, 0xFF]])
def test_ADD_REG_VAL(instructions, cpu_with_memory):
    """
    7xkk - ADD Vx, byte
    Set Vx = Vx + kk.
    Adds the value kk to the value of register Vx, then stores the result in Vx.
    """
    i = 0
    while i < len(instructions):
        expected_instruction = instructions[0] << 8 | instructions[1]
        x = (expected_instruction & 0x0F00) >> 8
        value_to_add = expected_instruction & 0x00FF
        cpu_with_memory.execute()

        assert cpu_with_memory.current_instruction == expected_instruction
        assert cpu_with_memory.REGISTERS["GPR"][x] == value_to_add
        # check each 2 bytes
        i += 2
