class MIPSPipeline:
    def __init__(self):
        self.registers = [1] * 32
        self.memory = [1] * 1024  # 模擬的記憶體
        self.pc = 0
        self.pipeline = []  # 用於模擬 pipeline 的每個階段
        self.cycles = -1
        self.stage_log = []  # 用於記錄每個週期的 pipeline 狀態
        self.stalled = False  # 用於表示是否有 stall
        self.registers[0] = 0  # $zero 寄存器的值永遠為 0

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
        data_hazard = False  # 是否遇到數據冒險

        for i in range(len(self.pipeline)):
            instruction, stage = self.pipeline[i]

            if stage == "IF":
                if self.check_hazard(instruction):
                    data_hazard = True  # 發現數據冒險，標記 stall
                    continue
                else:
                    self.pipeline[i] = (instruction, "ID")
            elif stage == "ID":
                if self.check_hazard(instruction):
                    data_hazard = True  # 發現數據冒險，標記 stall
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

        # ✅ 修正這一行
        self.pipeline = [(inst, stage) for inst, stage in self.pipeline if stage != "DONE"]

        # 如果遇到數據冒險，則 stall 只影響當前 cycle
        self.stalled = data_hazard




    def check_hazard(self, instruction):
        parts = instruction.replace(",", "").split()
        op = parts[0]
        sources = []
        target = None

        # 提取目標和來源寄存器
        if op in ["add", "sub"]:
            target = int(parts[1][1:])
            sources = [int(part[1:]) for part in parts[2:] if part.startswith("$")]
        elif op == "lw":
            target = int(parts[1][1:])
            if "(" in parts[2]:
                sources = [int(parts[2].split("(")[1][1:].strip(")"))]
        elif op == "sw":
            if "(" in parts[2]:
                sources = [int(parts[1][1:]), int(parts[2].split("(")[1][1:].strip(")"))]

        # 檢查流水線中是否有數據冒險
        for inst, stage in self.pipeline:
            inst_parts = inst.replace(",", "").split()
            inst_op = inst_parts[0]
            inst_target = None

            if inst_op in ["add", "sub", "lw"]:
                inst_target = int(inst_parts[1][1:])

            # 檢測數據冒險 (RAW Hazard)
            if inst_target and inst_target in sources:
                if stage == "ID":  # 在 ID 階段，表示數據還未準備好，必須 stall
                    return True
                if stage == "EX" and inst_op == "lw":  
                    # 如果前面是 lw，並且正在 EX 階段，那麼數據還沒到 MEM，add 需要 stall
                    return True
                if stage in ["MEM", "WB"]:  
                    # 如果已經到了 MEM 或 WB，Forwarding 機制可用，不需要 stall
                    continue

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
        r = ""
        st = [[item[0].split()[0], item[1], ""] for item in self.pipeline]
        for i in range(len(st)):
            r += "    " + st[i][0] + " " + st[i][1] + " " + st[i][2] + "\n"
        if self.cycles == 0:
            return
        state = f"Cycle {self.cycles}: \n" + r
        self.stage_log.append(state)
        print(self.pipeline)


test_case = 2

# 讀取 inputs/test.txt
with open(f"inputs/test{test_case}.txt", "r") as f:
    instructions = f.readlines()

# 初始化模擬器與記憶體
pipeline = MIPSPipeline()
# pipeline.load_memory({8: 5, 16: 10})

# 執行指令並模擬 pipeline
cycles = pipeline.execute_pipeline(instructions)

w_mem = []
mem_word = ""
n = 0
while len(w_mem) < 32:
    w_mem.append(pipeline.memory[n]) 
    mem_word += "W"+ str(n//4) + " "
    n+=4
# 寫入 outputs/test.txt
with open(f"outputs/test{test_case}.txt", "w") as f:
    f.write(f"Case {test_case}: \n## Each clocks\n")
    f.write("\n".join(pipeline.stage_log) + "\n\n")
    f.write(f"## Final Result:\n\nTotal Cycles: {cycles}\n\n")
    f.write(f"Final Register Values:\n")
    f.write(f"Registers: {pipeline.registers}\n\n")
    f.write(f"Final Memory Values:\n")
    f.write(f"{w_mem}\n")
