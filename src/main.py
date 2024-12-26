import os
from collections import deque

class MIPSPipelineSimulator:
    def __init__(self):
        self.registers = [1] * 32  # 初始化32個暫存器
        self.registers[0] = 0  # $0寄存器固定為0
        self.memory = [1] * 32  # 初始化記憶體
        self.pipeline = deque(maxlen=5)  # 五階段管線
        self.cycles = 0  # 週期計數器
        self.instructions = []

    def load_instructions(self, filepath):
        with open(filepath, 'r') as f:
            self.instructions = [line.strip() for line in f.readlines() if line.strip()]

    def parse_instruction(self, instruction):
        parts = instruction.replace(',', '').split()
        op = parts[0]
        if op in ('add', 'sub'):
            return op, int(parts[1][1:]), int(parts[2][1:]), int(parts[3][1:])
        elif op in ('lw', 'sw'):
            reg = int(parts[1][1:])
            offset, base = parts[2].split('(')
            return op, reg, int(offset), int(base[1:-1])
        elif op == 'beq':
            return op, int(parts[1][1:]), int(parts[2][1:]), int(parts[3])
        return None

    def execute_pipeline(self):
        while self.pipeline or self.instructions:
            self.cycles += 1
            if self.pipeline:
                self.write_back()
            if len(self.pipeline) >= 4:
                self.memory_access()
            if len(self.pipeline) >= 3:
                self.execute()
            if len(self.pipeline) >= 2:
                self.decode()
            if self.instructions:
                self.fetch()
            self.display_pipeline_state()

    def fetch(self):
        if self.instructions:
            instruction = self.instructions.pop(0)
            self.pipeline.appendleft((instruction, 'IF'))

    def decode(self):
        instruction, stage = self.pipeline[-2]
        self.pipeline[-2] = (instruction, 'ID')

    def execute(self):
        instruction, stage = self.pipeline[-3]
        op, *args = self.parse_instruction(instruction)
        if op in ('add', 'sub'):
            dest, src1, src2 = args
            result = (self.registers[src1] + self.registers[src2]) if op == 'add' else (self.registers[src1] - self.registers[src2])
            self.pipeline[-3] = (instruction, 'EX', result)
        elif op == 'lw':
            dest, offset, base = args
            addr = self.registers[base] + offset
            self.pipeline[-3] = (instruction, 'EX', addr)
        elif op == 'sw':
            src, offset, base = args
            addr = self.registers[base] + offset
            self.pipeline[-3] = (instruction, 'EX', self.registers[src], addr)

    def memory_access(self):
        instruction, stage, *data = self.pipeline[-4]
        if instruction.startswith('lw'):
            addr = data[0]
            value = self.memory[addr]
            self.pipeline[-4] = (instruction, 'MEM', value)
        elif instruction.startswith('sw'):
            value, addr = data
            self.memory[addr] = value
            self.pipeline[-4] = (instruction, 'MEM')

    def write_back(self):
        if not self.pipeline:
            return
        instruction, stage, *data = self.pipeline.pop()
        if instruction.startswith(('add', 'sub', 'lw')) and data:
            dest = int(instruction.split()[1][1:])
            self.registers[dest] = data[0]

    def display_pipeline_state(self):
        print(f"Cycle {self.cycles}:")
        for i, (instr, stage, *_) in enumerate(self.pipeline):
            print(f"  Stage {5 - i}: {stage} - {instr}")
        print("Registers:", self.registers)
        print("Memory:", self.memory)

if __name__ == "__main__":
    simulator = MIPSPipelineSimulator()
    input_file = "inputs/test3.txt"
    simulator.load_instructions(input_file)
    simulator.execute_pipeline()
    output_file = "outputs/test3.txt"
    with open(output_file, 'w') as f:
        f.write(f"Total Cycles: {simulator.cycles}\n")
        f.write(f"Registers: {simulator.registers}\n")
        f.write(f"Memory: {simulator.memory}\n")
