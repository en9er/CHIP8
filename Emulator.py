from CHIP8 import CHIP8


def main():
    cpu = CHIP8()
    cpu.load_program("./programs/demo/Zero_Demo.ch8")
    print(cpu.MEMORY[200:])
    cpu.execute()


if __name__ == "__main__":
    main()
