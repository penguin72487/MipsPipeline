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

            if len(self.pipeline) >= 5:
                self.write_back()
            if len(self.pipeline) >= 4:
                self.memory_access()
            if len(self.pipeline) >= 3:
                self.execute()
            if len(self.pipeline) >= 2:
                self.decode()
            if self.instructions:
                self.fetch()

            for i in range(len(self.pipeline) - 1, 0, -1):
                entry = self.pipeline[i - 1]
                if len(entry) == 2:
                    instruction, stage = entry
                    next_stage = self.get_next_stage(stage)
                    self.pipeline[i] = (instruction, next_stage)
                else:
                    instruction, stage, *data = entry
                    next_stage = self.get_next_stage(stage)
                    self.pipeline[i] = (instruction, next_stage, *data)

            self.display_pipeline_state()

            if not self.pipeline and not self.instructions:
                break

    def get_next_stage(self, current_stage):
        stages = ['IF', 'ID', 'EX', 'MEM', 'WB']
        if current_stage in stages:
            idx = stages.index(current_stage)
            if idx + 1 < len(stages):
                return stages[idx + 1]
        return current_stage

    def fetch(self):
        if self.instructions:
            instruction = self.instructions.pop(0)
            self.pipeline.appendleft((instruction, 'IF'))

    def decode(self):
        if len(self.pipeline) >= 2:
            instruction, stage = self.pipeline[-2]
            self.pipeline[-2] = (instruction, 'ID')

    def execute(self):
        if len(self.pipeline) >= 3:
            instruction, stage = self.pipeline[-3]
            op, *args = self.parse_instruction(instruction)
            if op in ('add', 'sub'):
                dest, src1, src2 = args
                result = self.registers[src1] + self.registers[src2] if op == 'add' else self.registers[src1] - self.registers[src2]
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
        if len(self.pipeline) >= 4:
            instruction, stage, *data = self.pipeline[-4]
            if not data:
                return

            if instruction.startswith('lw'):
                addr = data[0]
                if addr < len(self.memory):
                    value = self.memory[addr]
                    self.pipeline[-4] = (instruction, 'MEM', value)
            elif instruction.startswith('sw'):
                if len(data) < 2:
                    return
                value, addr = data
                if addr < len(self.memory):
                    self.memory[addr] = value
                    self.pipeline[-4] = (instruction, 'MEM')

    def write_back(self):
        if len(self.pipeline) >= 1:
            entry = self.pipeline.pop()
            if len(entry) > 2:
                instruction, stage, *data = entry
                if instruction.startswith(('add', 'sub', 'lw')) and data:
                    dest = int(instruction.split()[1][1:].replace(',', ''))
                    self.registers[dest] = data[0]

    def display_pipeline_state(self):
        print(f"Cycle {self.cycles}:")
        for i, entry in enumerate(self.pipeline):
            if len(entry) == 2:
                instr, stage = entry
                print(f"  Stage {5 - i}: {stage} - {instr}")
            elif len(entry) > 2:
                instr, stage, *data = entry
                print(f"  Stage {5 - i}: {stage} - {instr} - Data: {data}")
        print("Registers:", self.registers)
        print("Memory:", self.memory)
        print("-" * 50)

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
