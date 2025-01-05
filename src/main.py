class MIPSPipeline:
    def __init__(self):
        self.registers = [1] * 32
        self.memory = [1] * 1024  # 模擬的記憶體
        self.pc = 0
        self.pipeline = []  # 用於模擬 pipeline 的每個階段
        self.cycles = -1
        self.stage_log = []  # 用於記錄每個週期的 pipeline 狀態
        self.stalled = False  # 是否因為 hazard 停滯
        self.branch_taken = False  # `beq` 是否成立
        self.branch_pc = None  # `beq` 在 WB 階段才改變 `PC`
        self.branch_canceled = False  # 一開始是 False，如果 `beq` 成立，則改為 True
        self.branch_stall_count = 0  # `beq` 的 `ID` 階段需要 stall 兩次
        self.registers[0] = 0  # `$zero` 永遠為 0

    def execute_pipeline(self, instructions):
        while self.pc < len(instructions) or len(self.pipeline) > 0:
            self.cycles += 1

            # debug print
            print(f"[DEBUG] cycle={self.cycles}, pc={self.pc}, pipeline={self.pipeline}, "
                  f"branch_taken={self.branch_taken}, branch_pc={self.branch_pc}, "
                  f"stall_count={self.branch_stall_count}")
            
            self.log_pipeline_state()

            # 處理 pipeline
            if self.pipeline:
                self.process_pipeline()

            # ✅ `beq` 在 `WB` 階段影響 `PC`，但不清空 pipeline
            if self.branch_taken and self.branch_pc is not None:
                self.pc = self.branch_pc
                self.branch_taken = False

            # 加入新的指令到 pipeline
            if not self.stalled and self.pc < len(instructions):
                instruction = instructions[self.pc].strip()
                self.pipeline.append((instruction, "IF"))
                self.pc += 1

        return self.cycles

    def process_pipeline(self):
        data_hazard = False
        stalled_by_beq = False  

        # 逐一處理 pipeline 裡的指令
        for i in range(len(self.pipeline)):
            instruction, stage = self.pipeline[i]

            if stage == "IF":
                if stalled_by_beq:
                    continue
                # 改成檢查前面指令
                if self.check_hazard(instruction, i):
                    data_hazard = True
                    continue
                else:
                    self.pipeline[i] = (instruction, "ID")

            elif stage == "ID":
                # 對 beq 做 stall
                if "beq" in instruction:
                    if self.branch_stall_count < 2:
                        self.branch_stall_count += 1
                        data_hazard = True
                        stalled_by_beq = True
                        continue
                    else:
                        self.branch_stall_count = 0

                if self.check_hazard(instruction, i):
                    data_hazard = True
                    continue
                else:
                    self.pipeline[i] = (instruction, "EX")

            elif stage == "EX":
                if self.execute_instruction(instruction):
                    self.pipeline[i] = (instruction, "MEM")

            elif stage == "MEM":
                self.pipeline[i] = (instruction, "WB")

            elif stage == "WB":
                if "beq" in instruction and self.branch_taken:
                    self.branch_pc = self.pc
                self.pipeline[i] = (instruction, "DONE")

        # 移除執行完成 (DONE) 的指令
        self.pipeline = [(inst, stage) for inst, stage in self.pipeline if stage != "DONE"]
        # 若本週期有資料 hazard，需要 stall
        self.stalled = data_hazard

    def check_hazard(self, instruction, idx):
        """
        只檢查 pipeline[:idx] (更前面的指令)，
        確認是否會造成對當前指令的 hazard。
        """
        parts = instruction.replace(",", "").split()
        op = parts[0]
        sources = []
        target = None

        # 解析當前這條指令的 source 和 target
        if op in ["add", "sub"]:
            target = int(parts[1][1:])
            sources = [int(part[1:]) for part in parts[2:] if part.startswith("$")]
        elif op == "lw":
            target = int(parts[1][1:])
            if "(" in parts[2]:
                sources = [int(parts[2].split("(")[1][1:].strip(")"))]
        elif op == "sw":
            if "(" in parts[2]:
                # sw $rt, offset($base)
                # 會讀 rt(作為source) 以及 base(也是source)
                sources = [int(parts[1][1:]), int(parts[2].split("(")[1][1:].strip(")"))]

        # 依序檢查「更前面的指令」是否會造成 hazard
        for j in range(idx):
            inst_j, stage_j = self.pipeline[j]
            inst_j_parts = inst_j.replace(",", "").split()
            inst_j_op = inst_j_parts[0]
            inst_j_target = None

            if inst_j_op in ["add", "sub", "lw"]:
                inst_j_target = int(inst_j_parts[1][1:])
            
            # 假設前面指令要寫入 inst_j_target，
            # 而當前指令要讀 sources => hazard
            if inst_j_target and inst_j_target in sources:
                # 依照典型 MIPS pipeline hazard 規則
                if stage_j == "ID":
                    return True
                # lw 在 EX 時尚未讀完記憶體 => 需要 forward or stall
                if stage_j == "EX" and inst_j_op == "lw":
                    return True
                # MEM, WB 中 => 資料已可 forward 或即將寫回 => 不 stall
                if stage_j in ["MEM", "WB"]:
                    continue
        
        return False

    def get_signal(self, stage, instruction):
        op = instruction.split()[0]
        signal_format = {
            "lw": {
                "EX": "01 010 11",  
                "MEM": "010 11",    
                "WB": "11"          
            },
            "sw": {
                "EX": "X1 001 0X",  
                "MEM": "001 0X",    
                "WB": "0X"          
            },
            "add": {
                "EX": "10 000 10",  
                "MEM": "000 10",    
                "WB": "10"          
            },
            "sub": {
                # 你若需要 sub 也有控制訊號，可加在此處
                "EX": "10 000 10",  
                "MEM": "000 10",    
                "WB": "10"          
            },
            "beq": {
                "EX": "X0 100 0X",  
                "MEM": "100 0X",    
                "WB": "0X"          
            }
        }
        return signal_format.get(op, {}).get(stage, "")
    
    def log_pipeline_state(self):
        # 當 cycle == 0 時，直接不做任何紀錄
        if self.cycles == 0:
            return

        state = f"Cycle {self.cycles}\n"
        for instruction, stage in self.pipeline:
            signal = self.get_signal(stage, instruction)
            if stage in ["EX", "MEM", "WB"]:
                state += f"{instruction}: {stage} {signal}\n"
            else:
                state += f"{instruction}: {stage}\n"
        self.stage_log.append(state)

    def execute_instruction(self, instruction):
        parts = instruction.replace(",", "").strip().split()
        op = parts[0]

        # 如果 branch_canceled 已為 True，直接 return True，但跳過任何寫入
        # （不過 'beq' 自己還是要跑判定，所以要排除掉 beq）
        if self.branch_canceled and op not in ["beq"]:
            # 依然 return True 讓 pipeline 繼續往下做 MEM, WB，但實際不改任何東西
            return True

        if op == "lw":
            rt = int(parts[1][1:])
            offset, base = map(int, parts[2].strip("()").split("($"))
            mem_address = (self.registers[base] + offset) // 4
            self.registers[rt] = self.memory[mem_address]

        elif op == "sw":
            rt = int(parts[1][1:])
            offset, base = map(int, parts[2].strip("()").split("($"))
            mem_address = (self.registers[base] + offset) // 4
            self.memory[mem_address] = self.registers[rt]

        elif op == "add":
            rd = int(parts[1][1:])
            rs = int(parts[2][1:])
            rt = int(parts[3][1:])
            if not self.branch_taken:
                self.registers[rd] = self.registers[rs] + self.registers[rt]

        elif op == "sub":
            rd = int(parts[1][1:])
            rs = int(parts[2][1:])
            rt = int(parts[3][1:])
            if not self.branch_taken:
                self.registers[rd] = self.registers[rs] - self.registers[rt]

        elif op == "beq":
            rs = int(parts[1][1:])
            rt = int(parts[2][1:])
            offset = int(parts[3])
            if self.registers[rs] == self.registers[rt]:
                self.branch_taken = True
                self.branch_pc = self.pc + offset
                # ★ 這裡設 branch_canceled
                self.branch_canceled = True
        else:
            raise ValueError(f"Unknown instruction: {instruction}")

        return True


# 下面是執行並輸出結果的程式片段 (維持原樣，只是略做註解)
test_case = 1
with open(f"inputs/test{test_case}.txt", "r") as f:
    instructions = f.readlines()

pipeline = MIPSPipeline()
cycles = pipeline.execute_pipeline(instructions)

# Registers: 直接轉成字串即可
registers_str = f"{pipeline.registers}"

# Memory: 假設只顯示前 32 格
mem_ary = pipeline.memory[:32]
mem_str = f"{mem_ary}"

output_text = f"""
Case {test_case}: 
## Each clocks
{''.join(pipeline.stage_log)}

## Final Result:

Total Cycles: {cycles}

Final Register Values:
{registers_str}

Final Memory Values:
{mem_str}
"""

print(output_text)

with open(f"outputs/test{test_case}.txt", "w") as f:
    f.write(output_text)
