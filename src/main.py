import os
class MIPSPipeline:
    def __init__(self):
        self.registers = [1] * 32
        self.memory = [1] * 1024  # 模擬的記憶體
        self.pc = 0
        self.pipeline = []  # 用於模擬 pipeline 的每個階段
        self.cycles = -1
        self.stage_log = []  # 用於記錄每個週期的 pipeline 狀態
        self.stalled = False  # 是否因為 hazard 停滯
        self.branch_taken = False  # beq 是否成立
        self.branch_pc = None  # beq 在 WB 階段才改變 PC
        # self.branch_canceled = False  # 一開始是 False，如果 beq 成立，則改為 True
        self.branch_stall_count = 0  # beq 的 ID 階段需要 stall 兩次
        self.registers[0] = 0  # $zero 永遠為 0

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
                


            # ✅ beq 在 WB 階段影響 PC，但不清空 pipeline
            if self.branch_taken and self.branch_pc is not None:
                self.pc = self.branch_pc
                self.branch_taken = False

            # 加入新的指令到 pipeline
            if not self.stalled and self.pc < len(instructions):
                # ★ 在這裡做「把逗號換成空白」再 split 的動作
                raw_inst = instructions[self.pc].strip()
                raw_inst = raw_inst.replace(",", " ")
                self.pipeline.append((raw_inst, "IF"))
                self.pc += 1

        return self.cycles

    def process_pipeline(self):
        data_hazard = False
        stalled_by_beq = False  

        for i in range(len(self.pipeline)):
            instruction, stage = self.pipeline[i]

            if stage == "IF":
                if stalled_by_beq:
                    continue
                if self.check_hazard(instruction, i, stage):
                    data_hazard = True
                    continue
                else:
                    self.pipeline[i] = (instruction, "ID")

            elif stage == "ID":


                if self.check_hazard(instruction, i, stage):
                    data_hazard = True
                    continue
                else:
                    # beq 指令在 ID 階段就要判斷是否要跳 吃飯完回來寫
                    if "beq" in instruction:
                        rs = int(instruction.split()[1][1:])
                        rt = int(instruction.split()[2][1:])
                        if self.registers[rs] == self.registers[rt]:
                            self.branch_taken = True
                            self.branch_pc = self.pc + int(instruction.split()[3])-1
                            # self.branch_canceled = True
                            for j in range(i+1,len(self.pipeline)):
                                self.pipeline[j] = ("", "DONE")

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
        self.stalled = data_hazard

    def check_hazard(self, instruction, idx, stage):
        """
        只檢查 pipeline[:idx] (更前面的指令)，
        確認是否會造成對當前指令的 hazard。
        """
        if stage == "IF":
            # 檢查pipeline有沒有ID
            for j in range(idx):
                inst_j, stage_j = self.pipeline[j]
                if stage_j == "ID":
                    return True
            return False
        # instruction 已經是沒有逗號的字串，如 "add $1 $1 $2"
        parts = instruction.split()  # 這樣就能拿到 ["add", "$1", "$1", "$2"] (以 add 為例)
        op = parts[0]
        sources = []
        target = None


        if op in ["add", "sub"]:
            target = int(parts[1][1:])   # parts[1] 是 "$1"
            # 例如 parts[2]="$1", parts[3]="$2"
            sources = [int(p[1:]) for p in parts[2:] if p.startswith("$")]
        elif op == "lw":
            # lw $2, 8($0) -> 轉成 "lw $2 8($0)" -> parts = ["lw","$2","8($0)"]
            rt = parts[1]  # "$2"
            target = int(rt[1:])
            if "(" in parts[2]:
                # "8($0)" -> offset=8, base=$0
                base_str = parts[2].split("(")[1].strip(")")
                sources = [int(base_str[1:])]  # 取出 $0 -> 0
        elif op == "sw":
            # sw $4, 24($0) -> "sw $4 24($0)" -> parts = ["sw","$4","24($0)"]
            # sw 需要把 $4, $0 都當作 source
            rt = parts[1]  # "$4"
            if "(" in parts[2]:
                base_str = parts[2].split("(")[1].strip(")")
                sources = [int(rt[1:]), int(base_str[1:])]
        elif op == "beq":
            # beq $4, $4, 1 -> "beq $4 $4 1" -> parts = ["beq","$4","$4","1"]
            rs = int(parts[1][1:])
            rt = int(parts[2][1:])
            sources = [rs, rt]

        # 依序檢查「更前面的指令」是否會造成 hazard

        
        if op == "beq": 
            # beq 指令的 hazard 檢查
            # 如果rt, rs 在pipeline[:idx]中
            # add sub 時 EX會Forward 到 beq 的ID ，所以 IF ID EX 會造成 hazard
            # lw 時 MEM會Forward 到 beq 的ID ，所以 IF ID EX MEM 會造成 hazard
            # sw 沒差
            for j in range(idx):
                inst_j, stage_j = self.pipeline[j]
                inst_j_parts = inst_j.split() 
                inst_j_op = inst_j_parts[0]
                inst_j_target = int(inst_j_parts[1][1:])
                if inst_j_target not in sources:
                    continue
                
                
                if inst_j_op in ["add", "sub"]:
                    if stage_j in ["IF", "ID", "EX", "MEM"]:
                        return True
                if inst_j_op in ["lw"]:
                    if stage_j in ["IF", "ID", "EX", "MEM", "WB"]:
                        return True
            
        elif op in ["add", "sub"]:
            # add sub 指令的 hazard 檢查
            # 如果 rs, rt 在 pipeline[:idx] 中
            # add sub 時 EX會Forward 到 add sub 的ID ，所以 IF ID EX 會造成 hazard
            # lw 時 MEM會Forward 到 add sub 的ID ，所以 IF ID EX MEM 會造成 hazard
            # sw 沒差
            for j in range(idx):
                inst_j, stage_j = self.pipeline[j]
                inst_j_parts = inst_j.split()
                inst_j_op = inst_j_parts[0]
                inst_j_target = int(inst_j_parts[1][1:])
                if inst_j_target not in sources:
                    continue
                
                if inst_j_op in ["add", "sub"]:
                    if stage_j in ["IF", "ID", "EX"]:
                        return True
                if inst_j_op in ["lw"]:
                    if stage_j in ["IF", "ID", "EX", "MEM"]: #再確認一下
                        return True
        elif op in ["lw"]:
            return False



                


            
        
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
        # 這裡也要先切好 parts
        parts = instruction.split()
        op = parts[0]

        # if self.branch_canceled and op not in ["beq"]:
        #     return True

        if op == "lw":
            # parts = ["lw","$2","8($0)"]
            rt = parts[1]       # "$2"
            offset_base = parts[2]  # "8($0)"
            offset_str, base_str = offset_base.split("(")
            offset = int(offset_str)
            base_reg = int(base_str.strip(")")[1:])
            mem_address = (self.registers[base_reg] + offset) // 4
            self.registers[int(rt[1:])] = self.memory[mem_address]

        elif op == "sw":
            # parts = ["sw","$4","24($0)"]
            rt = parts[1]       # "$4"
            offset_base = parts[2]  # "24($0)"
            offset_str, base_str = offset_base.split("(")
            offset = int(offset_str)
            base_reg = int(base_str.strip(")")[1:])
            mem_address = (self.registers[base_reg] + offset) // 4
            self.memory[mem_address] = self.registers[int(rt[1:])]

        elif op == "add":
            # parts = ["add","$1","$1","$2"]
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
            # parts = ["beq","$4","$4","1"]
            rs = int(parts[1][1:])
            rt = int(parts[2][1:])
            offset = int(parts[3])

        else:
            raise ValueError(f"Unknown instruction: {instruction}")

        return True


# ------------------ 以下是 main 的執行與輸出 ------------------ 
test_case = 4

with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), f"inputs/test{test_case}.txt"), 'r') as f:
    instructions = f.readlines()

pipeline = MIPSPipeline()
cycles = pipeline.execute_pipeline(instructions)

registers_str = f"{pipeline.registers}"
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