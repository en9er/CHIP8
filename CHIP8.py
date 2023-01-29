import random
import sys

import pygame

KEYS = {
    0x0: pygame.K_1,
    0x1: pygame.K_2,
    0x2: pygame.K_3,
    0x3: pygame.K_4,
    0x4: pygame.K_q,
    0x5: pygame.K_w,
    0x6: pygame.K_e,
    0x7: pygame.K_r,
    0x8: pygame.K_a,
    0x9: pygame.K_s,
    0xA: pygame.K_d,
    0xB: pygame.K_f,
    0xC: pygame.K_z,
    0xD: pygame.K_x,
    0xE: pygame.K_c,
    0xF: pygame.K_v,
}


class Stack:
    capacity = 16

    def __init__(self):
        self.items = []

    def push(self, value):
        if len(self.items) < 16:
            self.items.append(value)
        else:
            raise Exception("Stack overflow")

    def pop(self):
        if len(self.items) > 0:
            return self.items.pop()
        else:
            raise Exception("Stack underflow")


class CHIP8:
    # sprites representing the hexadecimal digits 0 through F
    FONT_SPRITES = [
        0xF0,
        0x90,
        0x90,
        0x90,
        0xF0,  # 0
        0x20,
        0x60,
        0x20,
        0x20,
        0x70,  # 1
        0xF0,
        0x10,
        0xF0,
        0x80,
        0xF0,  # 2
        0xF0,
        0x10,
        0xF0,
        0x10,
        0xF0,  # 3
        0x90,
        0x90,
        0xF0,
        0x10,
        0x10,  # 4
        0xF0,
        0x80,
        0xF0,
        0x10,
        0xF0,  # 5
        0xF0,
        0x80,
        0xF0,
        0x90,
        0xF0,  # 6
        0xF0,
        0x10,
        0x20,
        0x40,
        0x40,  # 7
        0xF0,
        0x90,
        0xF0,
        0x90,
        0xF0,  # 8
        0xF0,
        0x90,
        0xF0,
        0x10,
        0xF0,  # 9
        0xF0,
        0x90,
        0xF0,
        0x90,
        0x90,  # A
        0xE0,
        0x90,
        0xE0,
        0x90,
        0xE0,  # B
        0xF0,
        0x80,
        0x80,
        0x80,
        0xF0,  # C
        0xE0,
        0x90,
        0x90,
        0x90,
        0xE0,  # D
        0xF0,
        0x80,
        0xF0,
        0x80,
        0xF0,  # E
        0xF0,
        0x80,
        0xF0,
        0x80,
        0x80,  # F
    ]

    def __init__(self):
        self.PC_START_OFFSET = 0x200
        self.MEMORY = [0] * 4096
        # The fonts data should be stored in the interpreter area of Chip-8 memory (0x000 to 0x1FF)
        for i in range(len(self.FONT_SPRITES)):
            self.MEMORY[i] = self.FONT_SPRITES[i]

        self.REGISTERS = {
            # 16 general purpose 8-bit registers [V0-VF] VF is used as a flag by some instructions
            "GPR": [0] * 16,
            # I register is generally used to store memory addresses, so only the lowest(rightmost) 12 bits are
            # usually used.
            "I": 0,
            "delay": 0,
            "sound": 0,
            # Program counter 16 bit
            "pc": 0,
            # Stack pointer 8 bit (useless)
            # Separate stack memory
            # The stack is an array of 16 16-bit values, used to store the address that the interpreter should return
            # to when finished with a subroutine. Chip-8 allows for up to 16 levels of nested subroutines
            "stack": Stack(),
        }
        self.INSTRUCTION_SET = {
            0x0: self.clear_or_return,  # clear or ret instruction
            0x1: self.JP,  # jump
            0x2: self.CALL,  # CALL
            0x3: self.SE_REG_VAL,  # SE Vx, byte, skip next instruction if Vx == kk
            0x4: self.SNE_REG_VAL,  # SNE vx, byte, skip next instruction if Vx != kk.
            0x5: self.SE_REG_REG,  # SE Vx, Vy, skip next instruction if Vx = Vy.
            0x6: self.LD_REG_VAL,  # Set Vx = kk.
            0x7: self.ADD_REG_VAL,  # Set Vx = Vx + kk.
            0x8: self.LD_OR_LOGIC_INSTRUCTIONS,
            0x9: self.SNE_REG_REG,  # Skip next instruction if Vx != Vy.
            0xA: self.LD_I,  # Set I = nnn.
            0xB: self.JP_V0,  # Jump to location nnn + V0.
            0xC: self.RND,  # Set Vx = random byte AND kk.
            0xD: self.DRW,  # Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.
            0xE: self.SKIP_IF_KEY,
            # TODO: rename function below
            0xF: self.some_really_useful_functions,
        }
        self.current_instruction = 0
        self.screen_matrix = []
        self.screen_width = 64
        self.screen_height = 32
        self.init_empty_screen_matrix()
        self.reset()
        self.keys_pressed = []

    def clear_or_return(self) -> None:
        """
        0nnn - SYS addr
        Jump to a machine code routine at nnn.
        This instruction is only used on the old computers on which Chip-8 was originally implemented. It is ignored by
            modern interpreters.
        00E0 - CLS
        Clear the display.
        00EE - RET
        Return from a subroutine.
        The interpreter sets the program counter to the address at the top of the stack, then subtracts 1
            from the stack pointer.

        :return: None
        """
        operand = self.current_instruction & 0x00FF
        if operand == 0xE0:
            self.clear_screen_matrix()
        elif operand == 0xEE:
            self.RET()
        else:
            raise Exception("Extended operations are not implemented")

    def RET(self) -> None:
        """
        00EE - RET Return from a subroutine. The interpreter sets the program counter to the address at the top of
        the stack, then subtracts 1 from the stack pointer.

        :return: None
        """
        self.REGISTERS["pc"] = self.REGISTERS["stack"].pop()

    def JP(self) -> None:
        """
        1nnn
        The interpreter sets the program counter to nnn. (1nnn)
        :return: None
        """
        self.REGISTERS["pc"] = self.current_instruction & 0x0FFF

    def CALL(self) -> None:
        """
        2nnn
        Call subroutine at nnn. The interpreter increments the stack pointer, then puts the current PC on the top of
        the stack. The PC is then set to nnn.

        :return: None
        """
        self.REGISTERS["stack"].push(self.REGISTERS["pc"])
        self.REGISTERS["pc"] = self.current_instruction & 0x0FFF

    def SE_REG_VAL(self) -> None:
        """
        3xkk - SE Vx, byte
        Skip next instruction if Vx = kk.
        The interpreter compares register Vx to kk, and if they are equal, increments the program counter by 2.

        :return: None
        """
        register_to_compare = (self.current_instruction & 0x0F00) >> 8
        compare_value = self.current_instruction & 0x00FF
        if self.REGISTERS["GPR"][register_to_compare] == compare_value:
            self.REGISTERS["pc"] += 2

    def SNE_REG_VAL(self) -> None:
        """
        4xkk - SNE Vx, byte
        Skip next instruction if Vx != kk.
        The interpreter compares register Vx to kk, and if they are not equal, increments the program counter by 2.

        :return:
        """
        register_to_compare = (self.current_instruction & 0x0F00) >> 8
        compare_value = self.current_instruction & 0x00FF
        if self.REGISTERS["GPR"][register_to_compare] != compare_value:
            self.REGISTERS["pc"] += 2

    def SE_REG_REG(self) -> None:
        """
        5xy0 - SE Vx, Vy
        Skip next instruction if Vx = Vy.
        The interpreter compares register Vx to register Vy, and if they are equal, increments the program counter by 2.

        :return: None
        """
        x = (self.current_instruction & 0x0F00) >> 8
        y = (self.current_instruction & 0x00F0) >> 4
        if self.REGISTERS["GPR"][x] == self.REGISTERS["GPR"][y]:
            self.REGISTERS["pc"] += 2

    def LD_REG_VAL(self) -> None:
        """
        6xkk - LD Vx, byte
        Set Vx = kk.
        The interpreter puts the value kk into register Vx.

        :return: None
        """
        register = (
            self.current_instruction & 0x0F00
        ) >> 8  # register index to put value in
        value = self.current_instruction & 0x00FF  # value to store
        self.REGISTERS["GPR"][register] = value

    def ADD_REG_VAL(self) -> None:
        """
        7xkk - ADD Vx, byte
        Set Vx = Vx + kk.
        Adds the value kk to the value of register Vx, then stores the result in Vx.
        :return:
        """
        register = (
            self.current_instruction & 0x0F00
        ) >> 8  # register index to put value in
        reg_value = self.REGISTERS["GPR"][register]
        value = self.current_instruction & 0x00FF  # value to store
        tmp = reg_value + value
        self.REGISTERS["GPR"][register] = tmp if tmp < 256 else tmp - 256

    def LD_OR_LOGIC_INSTRUCTIONS(self) -> None:
        """
        8xy0 - LD Vx, Vy
        Set Vx = Vy.
        Stores the value of register Vy in register Vx.
        :return: None
        """
        if self.current_instruction & 0x000F == 0:
            # LOAD_REG_REG
            x = (self.current_instruction & 0x0F00) >> 8
            y = (self.current_instruction & 0x00F0) >> 4
            self.REGISTERS["GPR"][x] = self.REGISTERS["GPR"][y]
        else:
            self.LOGIC_INSTRUCTIONS()

    def LOGIC_INSTRUCTIONS(self) -> None:
        """
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

        :return:
        """
        x = (self.current_instruction & 0x0F00) >> 8
        x_reg_value = self.REGISTERS["GPR"][x]
        y = (self.current_instruction & 0x00F0) >> 4
        y_reg_value = self.REGISTERS["GPR"][y]
        last_4_bits = self.current_instruction & 0x000F
        if last_4_bits == 1:
            # Set Vx = Vx OR Vy.
            self.REGISTERS["GPR"][x] = x_reg_value | y_reg_value
        elif last_4_bits == 2:
            # Set Vx = Vx AND Vy.
            self.REGISTERS["GPR"][x] = x_reg_value & y_reg_value
        elif last_4_bits == 3:
            # Set Vx = Vx XOR Vy.
            self.REGISTERS["GPR"][x] = x_reg_value ^ y_reg_value
        elif last_4_bits == 4:
            # Set Vx = Vx + Vy, set VF = carry.
            add_result = x_reg_value + y_reg_value
            self.REGISTERS["GPR"][x] = add_result % 256
            # Set carry(last GPR register)
            self.REGISTERS["GPR"][-1] = add_result > 256
        elif last_4_bits == 5:
            # Set Vx = Vx - Vy, set VF = NOT borrow.
            if x_reg_value >= y_reg_value:
                self.REGISTERS["GPR"][x] = x_reg_value - y_reg_value
                self.REGISTERS["GPR"][-1] = 1
            else:
                self.REGISTERS["GPR"][x] = 256 + x_reg_value - y_reg_value
                self.REGISTERS["GPR"][-1] = 0

        elif last_4_bits == 6:
            # Set Vx = Vx SHR 1.
            # If the least-significant bit of Vx is 1, then VF is set to 1, otherwise 0. Then Vx is divided by 2.
            self.REGISTERS["GPR"][-1] = x_reg_value & 0x1
            self.REGISTERS["GPR"][x] >>= 1

        elif last_4_bits == 7:
            # Set Vx = Vy - Vx, set VF = NOT borrow.
            # If Vy > Vx, then VF is set to 1, otherwise 0. Then Vx is subtracted from Vy, and the results stored in Vx.
            if y_reg_value >= x_reg_value:
                self.REGISTERS["GPR"][-1] = 1
                self.REGISTERS["GPR"][x] = y_reg_value - x_reg_value
            else:
                self.REGISTERS["GPR"][-1] = 0
                self.REGISTERS["GPR"][x] = 256 + y_reg_value - x_reg_value

        elif last_4_bits == 0xE:
            # Set Vx = Vx SHL 1.
            # If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0. Then Vx is multiplied by 2.
            most_significant_bit = (x_reg_value & 0x80) >> 7
            self.REGISTERS["GPR"][-1] = most_significant_bit
            self.REGISTERS["GPR"][x] = x_reg_value << 1

    def SNE_REG_REG(self) -> None:
        """
        9xy0 - SNE Vx, Vy
        Skip next instruction if Vx != Vy.
        The values of Vx and Vy are compared, and if they are not equal, the program counter is increased by 2.
        :return: None
        """
        x = (self.current_instruction & 0x0F00) >> 8
        x_reg_value = self.REGISTERS["GPR"][x]
        y = (self.current_instruction & 0x00F0) >> 4
        y_reg_value = self.REGISTERS["GPR"][y]
        if x_reg_value != y_reg_value:
            self.REGISTERS["pc"] += 2

    def LD_I(self) -> None:
        """
        Annn - LD I, addr
        Set I = nnn.
        The value of register I is set to nnn.
        :return: None
        """
        self.REGISTERS["I"] = self.current_instruction & 0x0FFF

    def JP_V0(self) -> None:
        """
        Bnnn - JP V0, addr
        Jump to location nnn + V0.
        The program counter is set to nnn plus the value of V0.
        :return: None
        """
        self.REGISTERS["pc"] = (self.current_instruction & 0x0FFF) + self.REGISTERS[
            "GPR"
        ][0]

    def RND(self) -> None:
        """
        Cxkk - RND Vx, byte
        Set Vx = random byte AND kk.
        The interpreter generates a random number from 0 to 255, which is then ANDed with the value kk.
        The results are stored in Vx. See instruction 8xy2 for more information on AND.

        :return: None
        """
        x = (self.current_instruction & 0x0F00) >> 8
        kk = self.current_instruction & 0x00FF
        rand_byte = random.randint(0, 255)
        self.REGISTERS["GPR"][x] = kk & rand_byte

    def DRW(self) -> None:
        """
        Dxyn - DRW Vx, Vy, nibble
        Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.
        The interpreter reads n bytes from memory, starting at the address stored in I.
        These bytes are then displayed as sprites on screen at coordinates (Vx, Vy).
        Sprites are XORed onto the existing screen.
        If this causes any pixels to be erased, VF is set to 1, otherwise it is set to 0.
        If the sprite is positioned so part of it is outside the coordinates of the display,
        it wraps around to the opposite side of the screen.

        :return: None
        """
        x = (self.current_instruction & 0x0F00) >> 8
        y = (self.current_instruction & 0x00F0) >> 4
        n = self.current_instruction & 0x000F
        # collision initial 0
        self.REGISTERS["GPR"][-1] = 0
        x_position = self.REGISTERS["GPR"][x]
        y_position = self.REGISTERS["GPR"][y]
        sprite_data = self.MEMORY[self.REGISTERS["I"]:self.REGISTERS["I"] + n]
        if self.draw_sprite(x_position, y_position, sprite_data):
            self.REGISTERS["GPR"][-1] = 1
        else:
            self.REGISTERS["GPR"][-1] = 0

    def draw_sprite(self, x_position, y_position, sprite_data) -> bool:
        """
        :param x_position: int
        :param y_position: int
        :param sprite_data: list(int)
        :return: boot
        """
        collision = False

        sprite_binary = []
        for i in sprite_data:
            binary_data = bin(i)[2:]
            sprite_binary.append(["0"] * (8 - len(binary_data)) + list(binary_data))

        for i in range(len(sprite_binary)):
            for j in range(8):
                try:
                    if (
                        self.screen_matrix[y_position + i][x_position + j] == 1
                        and int(sprite_binary[i][j]) == 1
                    ):
                        collision = True
                    self.screen_matrix[y_position + i][x_position + j] = int(
                        self.screen_matrix[y_position + i][x_position + j]
                    ) ^ int(sprite_binary[i][j])
                except IndexError:
                    continue

        return collision

    def SKIP_IF_KEY(self) -> None:
        """
        Ex9E - SKP Vx
        Skip next instruction if key with the value of Vx is pressed.
        Checks the keyboard, and if the key corresponding to the value of Vx is currently in the down position, PC is increased by 2.

        ExA1 - SKNP Vx
        Skip next instruction if key with the value of Vx is not pressed.
        Checks the keyboard, and if the key corresponding to the value of Vx is currently in the up position, PC is increased by 2.
        :return: None
        """
        arg = self.current_instruction & 0x00FF
        x = (self.current_instruction & 0x0F00) >> 8
        if arg == 0x9E:
            # Skip next instruction if key with the value of Vx is pressed.
            pressed_key = pygame.key.get_pressed()
            if pressed_key[KEYS[self.REGISTERS["GPR"][x]]]:
                self.REGISTERS["pc"] += 2
        elif arg == 0xA1:
            # Skip next instruction if key with the value of Vx is not pressed.
            pressed_key = pygame.key.get_pressed()
            if not pressed_key[KEYS[self.REGISTERS["GPR"][x]]]:
                self.REGISTERS["pc"] += 2

        else:
            raise Exception("Unknown instruction")

    def some_really_useful_functions(self) -> None:
        """
        Fx07 - LD Vx, DT
        Set Vx = delay timer value.

        The value of DT is placed into Vx.


        Fx0A - LD Vx, K
        Wait for a key press, store the value of the key in Vx.

        All execution stops until a key is pressed, then the value of that key is stored in Vx.


        Fx15 - LD DT, Vx
        Set delay timer = Vx.

        DT is set equal to the value of Vx.


        Fx18 - LD ST, Vx
        Set sound timer = Vx.

        ST is set equal to the value of Vx.


        Fx1E - ADD I, Vx
        Set I = I + Vx.

        The values of I and Vx are added, and the results are stored in I.


        Fx29 - LD F, Vx
        Set I = location of sprite for digit Vx.

        The value of I is set to the location for the hexadecimal sprite corresponding to the value of Vx. See section 2.4, Display, for more information on the Chip-8 hexadecimal font.


        Fx33 - LD B, Vx
        Store BCD representation of Vx in memory locations I, I+1, and I+2.

        The interpreter takes the decimal value of Vx, and places the hundreds digit in memory at location in I, the tens digit at location I+1, and the ones digit at location I+2.


        Fx55 - LD [I], Vx
        Store registers V0 through Vx in memory starting at location I.

        The interpreter copies the values of registers V0 through Vx into memory, starting at the address in I.


        Fx65 - LD Vx, [I]
        Read registers V0 through Vx from memory starting at location I.

        The interpreter reads values from memory starting at location I into registers V0 through Vx.
        :return:
        """
        arg = self.current_instruction & 0x00FF
        x = (self.current_instruction & 0x0F00) >> 8
        x_reg_value = self.REGISTERS["GPR"][x]
        if arg == 0x07:
            # Set Vx = delay timer value.
            self.REGISTERS["GPR"][x] = self.REGISTERS["delay"]
        elif arg == 0x0A:
            # Wait for a key press, store the value of the key in Vx.
            pause = True
            while pause:
                event = pygame.event.wait()
                if event.type == pygame.KEYDOWN:
                    pressed_key = pygame.key.get_pressed()
                    for key in KEYS.values():
                        if pressed_key[key]:
                            self.REGISTERS["GPR"][x] = key
                            pause = False
                            break
        elif arg == 0x15:
            # Set delay timer = Vx.
            self.REGISTERS["delay"] = x_reg_value
        elif arg == 0x18:
            # Set sound timer = Vx.
            self.REGISTERS["sound"] = x_reg_value
        elif arg == 0x1E:
            # Set I = I + Vx.
            self.REGISTERS["I"] += x_reg_value
        elif arg == 0x29:
            # Set I = location of sprite for digit Vx.
            self.REGISTERS["I"] = self.REGISTERS["GPR"][x] * 5  # Font width
        elif arg == 0x33:
            # Store BCD representation of Vx in memory locations I, I+1, and I+2.
            hundreds = x_reg_value // 100
            tens = (x_reg_value - hundreds * 100) // 10
            ones = x_reg_value - hundreds * 100 - tens * 10
            self.MEMORY[self.REGISTERS["I"]] = hundreds
            self.MEMORY[self.REGISTERS["I"] + 1] = tens
            self.MEMORY[self.REGISTERS["I"] + 2] = ones
        elif arg == 0x55:
            # Store registers V0 through Vx in memory starting at location I.
            for reg_num in range(x + 1):
                self.MEMORY[self.REGISTERS["I"] + reg_num] = self.REGISTERS["GPR"][
                    reg_num
                ]
        elif arg == 0x65:
            # Read registers V0 through Vx from memory starting at location I.
            for reg_num in range(x + 1):
                self.REGISTERS["GPR"][reg_num] = self.MEMORY[
                    self.REGISTERS["I"] + reg_num
                ]

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
        offset = self.REGISTERS["pc"]
        self.REGISTERS["pc"] += 2
        return (int(self.MEMORY[offset]) << 8) | int(self.MEMORY[offset + 1])

    def load_program(self, filename: str) -> None:
        """
        Load bytes from file into ROM
        :param filename: string
        :return: None
        """
        data = open(filename, "rb").read()
        offset = self.PC_START_OFFSET
        for index in range(len(data)):
            self.MEMORY[offset + index] = data[index]

    def decrement_timers(self):
        """
        When these registers are non-zero, they are automatically decremented at a rate of 60Hz
        """
        if self.REGISTERS["delay"] > 0:
            self.REGISTERS["delay"] -= 1
        if self.REGISTERS["sound"] > 0:
            self.REGISTERS["sound"] -= 1

    def init_empty_screen_matrix(self) -> None:
        """
        The original implementation of the Chip-8 language used a 64x32-pixel monochrome display

        :return: None
        """
        for row in range(self.screen_height):
            a = [0] * self.screen_width
            self.screen_matrix.append(a)

    def reset(self):
        """
        Reset all registers
        """
        self.REGISTERS["GPR"] = [0] * 16
        self.REGISTERS["pc"] = self.PC_START_OFFSET
        self.REGISTERS["I"] = 0
        self.REGISTERS["delay"] = 0
        self.REGISTERS["sound"] = 0
        self.REGISTERS["stack"].items = []

    def key_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                try:
                    targetKey = KEYS[event.key]
                    self.keys_pressed[targetKey] = True
                except KeyError:
                    pass

            elif event.type == pygame.KEYUP:
                try:
                    targetKey = KEYS[event.key]
                    self.keys_pressed[targetKey] = False
                except KeyError:
                    pass

    def clear_screen_matrix(self):
        for i in range(self.screen_height):
            for j in range(self.screen_width):
                self.screen_matrix[i][j] = 0
