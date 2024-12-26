import os
from collections import defaultdict, deque

class PipelinedMIPSSimulator:
    def __init__(self):
        # 初始化 32 個暫存器，預設值為 1
        self.registers = [1] * 32
        self.registers[0] = 0  # MIPS 規範中 $0 暫存器的值固定為 0

        # 初始化記憶體，共 32 個字，每個預設值為 1
        self.memory = [1] * 32

        # 設置 5 階段的管線：IF, ID, EX, MEM, WB
        self.pipeline = deque(maxlen=5)

        # 週期計數器，用於記錄時鐘周期數
        self.cycles = 0

        # 預留的信號值（未來擴展使用）
        self.signals = []

    def load_instructions(self, filepath):
        # 從檔案中載入指令到指令清單
        with open(filepath, 'r') as f:
            self.instructions = [line.strip() for line in f.readlines() if line.strip()]

    def parse_instruction(self, instruction):
        # 解析 MIPS 指令，提取操作碼與操作數
        parts = instruction.split()
        op = parts[0]
        if op in ('add', 'sub'):
            # 處理算術指令：add/sub
            return op, int(parts[1][1:]), int(parts[2][1:]), int(parts[3][1:])
        elif op in ('lw', 'sw'):
            # 處理記憶體讀寫指令：lw/sw
            reg = int(parts[1][1:])
            offset, base = parts[2].split('(')
            return op, reg, int(offset), int(base[1:-1])
        elif op == 'beq':
            # 處理分支指令：beq
            return op, int(parts[1][1:]), int(parts[2][1:]), int(parts[3])
        return None

    def execute_pipeline(self):
        # 模擬管線階段的主迴圈
        while self.pipeline or self.instructions:
            self.cycles += 1  # 時鐘週期數加一

            # 依序執行管線中的每個階段（從後往前）
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

            # 每個週期後顯示管線狀態
            self.display_pipeline_state()

    def fetch(self):
        # 取指階段：從指令記憶體中取出下一條指令並加入管線
        if self.instructions:
            instruction = self.instructions.pop(0)
            self.pipeline.appendleft((instruction, 'IF'))

    def decode(self):
        # 解碼階段：分析指令的操作碼與操作數
        instruction, stage = self.pipeline[-2]
        self.pipeline[-2] = (instruction, 'ID')

    def execute(self):
        # 執行階段：執行算術運算或計算記憶體地址
        instruction, stage = self.pipeline[-3]
        op, *args = self.parse_instruction(instruction)
        if op in ('add', 'sub'):
            # 執行加法或減法運算
            dest, src1, src2 = args
            result = (self.registers[src1] + self.registers[src2]) if op == 'add' else (self.registers[src1] - self.registers[src2])
            self.pipeline[-3] = (instruction, 'EX', result)
        elif op == 'lw':
            # 計算記憶體地址（load 指令）
            dest, offset, base = args
            self.pipeline[-3] = (instruction, 'EX', self.memory[self.registers[base] + offset])
        elif op == 'sw':
            # 準備數據與地址（store 指令）
            src, offset, base = args
            self.pipeline[-3] = (instruction, 'EX', self.registers[src], self.registers[base] + offset)

    def memory_access(self):
        # 記憶體訪問階段：處理記憶體讀取或寫入操作
        instruction, stage, *data = self.pipeline[-4]
        if instruction.startswith('lw'):
            # load 指令：從記憶體讀取數據
            self.pipeline[-4] = (instruction, 'MEM', data[0])
        elif instruction.startswith('sw'):
            # store 指令：將數據寫入記憶體
            value, addr = data
            self.memory[addr] = value
            self.pipeline[-4] = (instruction, 'MEM')

    def write_back(self):
        # 寫回階段：將結果寫回暫存器
        instruction, stage, *data = self.pipeline.pop()
        if instruction.startswith('add') or instruction.startswith('sub') or instruction.startswith('lw'):
            dest = int(instruction.split()[1][1:])
            self.registers[dest] = data[0]

    def display_pipeline_state(self):
        # 顯示當前管線的狀態以及暫存器與記憶體的內容
        print(f"Cycle {self.cycles}:")
        for i, (instr, stage, *_) in enumerate(self.pipeline):
            print(f"  Stage {5 - i}: {stage} - {instr}")
        print("Registers:", self.registers)
        print("Memory:", self.memory)

if __name__ == "__main__":
    simulator = PipelinedMIPSSimulator()
    # 指令檔案路徑
    input_file = "inputs/test1.txt"  # 範例輸入檔案
    simulator.load_instructions(input_file)

    # 執行管線模擬
    simulator.execute_pipeline()

    # 將最終狀態輸出到檔案
    output_file = "outputs/test1.txt"
    with open(output_file, 'w') as f:
        f.write(f"Total Cycles: {simulator.cycles}\n")
        f.write(f"Registers: {self.registers}\n")
        f.write(f"Memory: {self.memory}\n")
