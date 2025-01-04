class MIPSPipeline:
    def __init__(self):
        self.registers = [0] * 32
        self.memory = [0] * 1024  # 模擬的記憶體
        self.pc = 0
        self.pipeline = []  # 用於模擬 pipeline 的每個階段
        self.cycles = 0
        self.stage_log = []  # 用於記錄每個週期的 pipeline 狀態
        self.stalled = False  # 用於表示是否有 stall

    def load_memory(self, values):
        for address, value in values.items():
            self.memory[address] = value

    def execute_pipeline(self, instructions):
        while self.pc < len(instructions) or len(self.pipeline) > 0:
            self.cycles += 1

            # 記錄當前 pipeline 狀態
            self.log_pipeline_state()

            # 處理 pipeline 的執行階段
            if self.pipeline:
                self.process_pipeline()

            # 加入新的指令到 pipeline
            if not self.stalled and self.pc < len(instructions):
                instruction = instructions[self.pc].strip()
                self.pipeline.append((instruction, "IF"))
                self.pc += 1

        return self.cycles

    def process_pipeline(self):
        data_hazard = False  # 用於判斷是否遇到數據冒險

        for i in range(len(self.pipeline)):
            instruction, stage = self.pipeline[i]

            if stage == "IF":
                self.pipeline[i] = (instruction, "ID")
            elif stage == "ID":
                if self.check_hazard(instruction):
                    data_hazard = True  # 發現數據冒險，標記暫停
                    continue
                else:
                    self.pipeline[i] = (instruction, "EX")
            elif stage == "EX":
                if self.execute_instruction(instruction):
                    self.pipeline[i] = (instruction, "MEM")
            elif stage == "MEM":
                self.pipeline[i] = (instruction, "WB")
            elif stage == "WB":
                self.pipeline[i] = (instruction, "DONE")

        # 移除已經完成的指令
        self.pipeline = [(inst, stage) for inst, stage in self.pipeline if stage != "DONE"]
            
        # 如果遇到數據冒險，則暫停當前週期
        
        if data_hazard:
            self.stalled = True  # 發現數據冒險，僅暫停當前
        else:
            self.stalled = False

    def check_hazard(self, instruction):
        parts = instruction.replace(",", "").split()
        op = parts[0]
        sources = []

        # 根據指令類型提取源寄存器
        if op in ["add", "sub", "beq"]:
            sources = [
                int(part[1:]) for part in parts[2:] if part.startswith("$")
            ]  # 確保只處理寄存器
        elif op == "lw":
            if "(" in parts[2]:
                sources = [int(parts[2].split("(")[1][1:].strip(")"))]
        elif op == "sw":
            if "(" in parts[2]:
                sources = [int(parts[1][1:])]

        # 檢查流水線中其他指令是否正在使用相關寄存器
        for inst, stage in self.pipeline:
            if stage in ["EX", "MEM", "WB"]:  # 只檢查這些階段
                inst_parts = inst.replace(",", "").split()
                if inst_parts[0] in ["add", "sub", "lw"]:  # 目標寄存器相關的指令
                    inst_dest = int(inst_parts[1][1:])
                    if inst_dest in sources:  # 如果目標寄存器與源寄存器有衝突
                        return True
        return False



    def execute_instruction(self, instruction):
        parts = instruction.replace(",", "").strip().split()
        op = parts[0]
        if op == "lw":
            rt = int(parts[1][1:])
            offset, base = map(int, parts[2].strip("()").split("($"))
            self.registers[rt] = self.memory[self.registers[base] + offset]
        elif op == "sw":
            rt = int(parts[1][1:])
            offset, base = map(int, parts[2].strip("()").split("($"))
            self.memory[self.registers[base] + offset] = self.registers[rt]
        elif op == "add":
            rd = int(parts[1][1:])
            rs = int(parts[2][1:])
            rt = int(parts[3][1:])
            self.registers[rd] = self.registers[rs] + self.registers[rt]
        elif op == "sub":
            rd = int(parts[1][1:])
            rs = int(parts[2][1:])
            rt = int(parts[3][1:])
            self.registers[rd] = self.registers[rs] - self.registers[rt]
        elif op == "beq":
            rs = int(parts[1][1:])
            rt = int(parts[2][1:])
            offset = int(parts[3])
            if self.registers[rs] == self.registers[rt]:
                self.pc += offset
                self.pipeline.clear()
        else:
            raise ValueError(f"Unknown instruction: {instruction}")
        return True

    def log_pipeline_state(self):
        state = f"Cycle {self.cycles}: " + ", ".join([f"{inst} ({stage})" for inst, stage in self.pipeline])
        if self.stalled:
            state += " [STALL]"
        self.stage_log.append(state)
        print(state)

# 讀取 inputs/test3.txt
with open("inputs/test4.txt", "r") as f:
    instructions = f.readlines()

# 初始化模擬器與記憶體
pipeline = MIPSPipeline()
pipeline.load_memory({8: 5, 16: 10})

# 執行指令並模擬 pipeline
cycles = pipeline.execute_pipeline(instructions)

# 寫入 outputs/test3.txt
with open("outputs/test3.txt", "w") as f:
    f.write(f"Total Cycles: {cycles}\n")
    f.write("Pipeline Stages per Cycle:\n")
    f.write("\n".join(pipeline.stage_log) + "\n")
    f.write(f"Registers: {pipeline.registers}\n")
    f.write(f"Memory: {pipeline.memory[:32]}\n")
