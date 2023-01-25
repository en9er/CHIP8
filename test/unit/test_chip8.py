import pytest

from CHIP8 import CHIP8


@pytest.mark.parametrize(
    "test_memory",
    [
        b"some_bytes",
        [0x0, 0x12, 0x11, 0x1e],
    ]
)
def test_load_instruction(test_memory):
    cpu = CHIP8()
    assert all(b == 0 for b in cpu.MEMORY[cpu.PC_START_OFFSET:])
    cpu.MEMORY = cpu.MEMORY[:200] + [int(b) for b in test_memory]
    i = 0
    while i < len(test_memory):
        instruction = cpu.load_instruction()
        assert instruction == test_memory[i] << 8 | test_memory[i + 1]
        # check each 2 bytes
        i += 2


@pytest.mark.parametrize(
    "load_instruction",
    [
        [96, 10],
        [101, 170]
    ]
)
def test_LD(load_instruction):
    cpu = CHIP8()
    assert all(b == 0 for b in cpu.MEMORY[cpu.PC_START_OFFSET:])
    cpu.MEMORY = cpu.MEMORY[:200] + [int(b) for b in load_instruction]
    i = 0
    while i < len(load_instruction):
        cpu.execute()
        register_index = ((load_instruction[0] << 8 | load_instruction[1]) & 0x0F00) >> 8
        assert cpu.REGISTERS['GPR'][register_index] == load_instruction[1]
        # check each 2 bytes
        i += 2
