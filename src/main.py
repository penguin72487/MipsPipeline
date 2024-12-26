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
        for i, (instruction, stage) in enumerate(self.pipeline):
            if stage == "IF":
                self.pipeline[i] = (instruction, "ID")
            elif stage == "ID":
                if self.check_hazard(instruction):
                    self.stalled = True
                    return
                else:
                    self.stalled = False
                    self.pipeline[i] = (instruction, "EX")
            elif stage == "EX":
                if self.execute_instruction(instruction):
                    self.pipeline[i] = (instruction, "MEM")
            elif stage == "MEM":
                self.pipeline[i] = (instruction, "WB")  # 恢復 WB 階段
            elif stage == "WB":
                self.pipeline.pop(i)
                break

    def check_hazard(self, instruction):
        parts = instruction.replace(",", "").split()
        if parts[0] in ["lw", "sw", "add", "beq"]:
            registers_in_use = [inst[1] for inst in self.pipeline if inst[1] in ["ID", "EX", "MEM"]]
            if any(reg for reg in registers_in_use if reg in instruction):
                return True  # 存在冒險
        return False

    def execute_instruction(self, instruction):
        instruction = instruction.replace(",", "").strip()  # 移除逗號與多餘空白
        parts = instruction.split()
        if parts[0] == "lw":
            rt = int(parts[1][1:])
            offset, base = map(int, parts[2].strip("()").split("($"))
            self.registers[rt] = self.memory[self.registers[base] + offset]
        elif parts[0] == "sw":
            rt = int(parts[1][1:])
            offset, base = map(int, parts[2].strip("()").split("($"))
            self.memory[self.registers[base] + offset] = self.registers[rt]
        elif parts[0] == "add":
            rd = int(parts[1][1:])
            rs = int(parts[2][1:])
            rt = int(parts[3][1:])
            self.registers[rd] = self.registers[rs] + self.registers[rt]
        elif parts[0] == "beq":
            rs = int(parts[1][1:])
            rt = int(parts[2][1:])
            offset = int(parts[3])
            if self.registers[rs] == self.registers[rt]:
                self.pc += offset
        else:
            raise ValueError(f"Unknown instruction: {instruction}")
        return True

    def log_pipeline_state(self):
        # 記錄每個週期的 pipeline 狀態
        state = f"Cycle {self.cycles}: " + ", ".join([f"{inst} ({stage})" for inst, stage in self.pipeline])
        if self.stalled:
            state += " [STALL]"
        self.stage_log.append(state)
        print(state)  # 顯示到命令列

# 讀取 inputs/test3.txt
with open("inputs/test3.txt", "r") as f:
    instructions = f.readlines()

# 初始化模擬器與記憶體
pipeline = MIPSPipeline()
pipeline.load_memory({8: 5, 16: 10})  # 示例數據

# 執行指令並模擬 pipeline
cycles = pipeline.execute_pipeline(instructions)

# 寫入 outputs/test3.txt
with open("outputs/test3.txt", "w") as f:
    f.write(f"Total Cycles: {cycles}\n")
    f.write("Pipeline Stages per Cycle:\n")
    f.write("\n".join(pipeline.stage_log) + "\n")
    f.write(f"Registers: {pipeline.registers}\n")
    f.write(f"Memory: {pipeline.memory[:32]}\n")
