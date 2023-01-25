class Stack:
    capacity = 16

    def __init__(self):
        self.items = []

    def push(self, value):
        if len(self.items) < 16:
            self.items.append(value)
        else:
            raise Exception("Stack overflow")

    def pop(self, value):
        if len(self.items) > 0:
            return self.items.pop(value)
        else:
            raise Exception("Stack underflow")


class CHIP8:
    # sprites representing the hexadecimal digits 0 through F
    FONT_SPRITES = [
        0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
        0x20, 0x60, 0x20, 0x20, 0x70,  # 1
        0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
        0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
        0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
        0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
        0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
        0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
        0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
        0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
        0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
        0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
        0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
        0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
        0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
        0xF0, 0x80, 0xF0, 0x80, 0x80  # F
    ]

    def __init__(self):
        self.PC_START_OFFSET = 200
        self.MEMORY = [0] * 4096
        # The fonts data should be stored in the interpreter area of Chip-8 memory (0x000 to 0x1FF)
        for i in range(len(self.FONT_SPRITES)):
            self.MEMORY[i] = self.FONT_SPRITES[i]

        self.REGISTERS = {
            # 16 general purpose 8-bit registers [V0-VF] VF is used as a flag by some instructions
            'GPR': [0] * 16,
            # I register is generally used to store memory addresses, so only the lowest(rightmost) 12 bits are
            # usually used.
            'I': 0,
            'delay': 0,
            'sound': 0,
            # Program counter 16 bit
            'pc': 0,
            # Stack pointer 8 bit
            'sp': 0,
            # Separate stack memory
            # The stack is an array of 16 16-bit values, used to store the address that the interpreter should return
            # to when finished with a subroutine. Chip-8 allows for up to 16 levels of nested subroutines
            'stack': Stack()
        }
        self.INSTRUCTION_SET = {
            # TODO: implement other instructions
            0x6: self.LD
        }
        self.current_instruction = 0

    def LD(self) -> None:
        """
        put the value kk into register Vx. (6xkk)
        :return: None
        """
        register = (self.current_instruction & 0xF00) >> 8  # register index to put value in
        value = (self.current_instruction & 0x0FF)  # value to store
        self.REGISTERS["GPR"][register] = value

    def execute(self):
        """
        load and execute instruction
        """
        self.current_instruction = self.load_instruction()
        opcode = self.current_instruction >> 12  # first 4 bits
        self.INSTRUCTION_SET[opcode]()

    def load_instruction(self) -> int:
        """
        Get 2 bytes from memory where address == pc and address == pc + 1 and execute
        :return: int
        """
        offset = self.PC_START_OFFSET + self.REGISTERS['pc']
        self.REGISTERS['pc'] += 2
        return int(self.MEMORY[offset]) << 8 | int(self.MEMORY[offset + 1])

    def load_program(self, filename: str) -> None:
        """
        Load bytes from file into ROM
        :param filename: string
        :return: None
        """
        data = open(filename, 'rb').read()
        offset = self.PC_START_OFFSET
        for index in range(len(data)):
            self.MEMORY[offset] = data[index]
            offset += 1

    def decrement_timers(self):
        """
        When these registers are non-zero, they are automatically decremented at a rate of 60Hz
        """
        if self.REGISTERS['delay'] != 0:
            self.REGISTERS['delay'] -= 1
        if self.REGISTERS['sound'] != 0:
            self.REGISTERS['sound'] -= 1
