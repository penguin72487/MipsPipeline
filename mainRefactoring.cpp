#include <iostream>
#include <fstream>
#include <string>

using namespace std;

// Global Variables
int IF_PCSrc;
int EX_ALUOP0, EX_ALUOP1, EX_RegDst, EX_ALUSrc, EX_Branch, EX_MemRead, EX_MemWrite, EX_RegWrite, EX_MemtoReg, rs, rt, rd, sign_extend;
int MEM_Branch, MEM_MemRead, MEM_MemWrite, MEM_RegWrite, MEM_MemtoReg, MEM_Result, WriteData, Zero, MEM_Destination;
int WB_RegWrite, WB_MemtoReg, WB_Result, ReadData, WB_Destination;
static int Memory[32] = {0};
static int Register[32] = {0};
static int line = 0;
string instruction;
char Cyc[5][4];
int cycle = 1;
static int stall_count = 0;
bool IF_over = false, ID_over = false, EX_over = false, MEM_over = false, WB_over = false;
bool beq_comfirm = false;

// Function Prototypes
void IF();
void ID();
void EX();
void MEM();
void WB();
void init_value();
void output_cycle(int cycle);
void output_register_memory(fstream& out);
void output_signals(const string &stage, int regDst, int aluSrc, int branch, int memRead, int memWrite, int regWrite, int memToReg);

// IF Stage
void IF() {
    bool next_line = false;
    string temp = instruction;

    fstream input("memory.txt");
    for (int i = 0; i <= line; i++) {
        if (getline(input, instruction)) {
            if (i == line) {
                next_line = true;
                for (int i = 0; i < 3; i++) {
                    Cyc[0][i] = instruction[i];
                }
                Cyc[0][3] = '\0';

                fstream out("result.txt", ios::out | ios::app);
                out << "\t" << Cyc[0] << ":IF" << endl;

                if (stall_count > 0) {
                    ID_over = false;
                    IF_over = false;
                    instruction = temp;
                    return;
                }

                for (int i = 0; i < 4; i++) {
                    Cyc[1][i] = Cyc[0][i];
                    Cyc[0][i] = '0';
                }
            }
        }
    }

    if (next_line) line++;
    input.close();
    IF_over = true;
    ID_over = false;
}

// ID Stage
void ID() {
    if (stall_count > 0) {
        ID_over = false;
        if (Cyc[1][0] != '0') {
            fstream out("result.txt", ios::out | ios::app);
            out << "\t" << Cyc[1] << ":ID" << endl;
        }
        return;
    }

    // Parse instruction
    int format = 0;
    int space[3] = {0};
    int work = 0;

    for (size_t i = 0; i < instruction.length(); i++) {
        if (instruction[i] == ' ') {
            space[format++] = i;
        }
    }

    // Determine instruction format and set control signals
    if (format == 2) {
        if (instruction[0] == 'l') {
            EX_RegDst = 0; EX_ALUSrc = 1; EX_Branch = 0;
            EX_MemRead = 1; EX_MemWrite = 0; EX_RegWrite = 1; EX_MemtoReg = 1;
            work = 1;
        } else if (instruction[0] == 's') {
            EX_RegDst = 2; EX_ALUSrc = 1; EX_Branch = 0;
            EX_MemRead = 0; EX_MemWrite = 1; EX_RegWrite = 0; EX_MemtoReg = 2;
            work = 2;
        }
    } else if (format == 3) {
        if (instruction[0] == 'a') {
            EX_RegDst = 1; EX_ALUSrc = 0; EX_Branch = 0;
            EX_MemRead = 0; EX_MemWrite = 0; EX_RegWrite = 1; EX_MemtoReg = 0;
            work = 3;
        } else if (instruction[0] == 'b') {
            EX_RegDst = 2; EX_ALUSrc = 0; EX_Branch = 1;
            EX_MemRead = 0; EX_MemWrite = 0; EX_RegWrite = 0; EX_MemtoReg = 2;
            work = 4;
        }
    }

    // Handle stalls
    if (work == 1 && MEM_Destination == rs + sign_extend && MEM_RegWrite == 1) {
        stall_count = 2;
        return;
    }

    if (Cyc[1][0] != '0') {
        fstream out("result.txt", ios::out | ios::app);
        out << "\t" << Cyc[1] << ":ID" << endl;
    }

    for (int i = 0; i < 4; i++) {
        Cyc[2][i] = Cyc[1][i];
        Cyc[1][i] = '0';
    }

    ID_over = true;
    EX_over = false;
}

// EX Stage
void EX() {
    if (Cyc[2][0] != '0') {
        fstream out("result.txt", ios::out | ios::app);
        out << "\t" << Cyc[2] << ":EX ";
        output_signals("EX", EX_RegDst, EX_ALUSrc, EX_Branch, EX_MemRead, EX_MemWrite, EX_RegWrite, EX_MemtoReg);
    }

    if (EX_ALUSrc == 0) {
        MEM_Result = rt + rs;
    } else {
        MEM_Result = rs + sign_extend;
    }

    if (MEM_Result == 0) Zero = 1;
    if (EX_Branch == 1 && Zero == 1) line += sign_extend;

    MEM_Destination = rd;
    WriteData = rt;
    MEM_Branch = EX_Branch;
    MEM_RegWrite = EX_RegWrite;
    MEM_MemRead = EX_MemRead;
    MEM_MemWrite = EX_MemWrite;
    MEM_MemtoReg = EX_MemtoReg;

    EX_over = true;
    MEM_over = false;
}

// MEM Stage
void MEM() {
    if (Cyc[3][0] != '0') {
        fstream out("result.txt", ios::out | ios::app);
        out << "\t" << Cyc[3] << ":MEM ";
        output_signals("MEM", MEM_Branch, MEM_MemRead, MEM_MemWrite, 0, 0, MEM_RegWrite, MEM_MemtoReg);
    }

    if (MEM_MemRead == 1) ReadData = Memory[MEM_Result];
    if (MEM_MemWrite == 1) Memory[MEM_Result] = WriteData;

    WB_RegWrite = MEM_RegWrite;
    WB_Destination = MEM_Destination;
    WB_MemtoReg = MEM_MemtoReg;
    WB_Result = MEM_Result;

    MEM_over = true;
    WB_over = false;
}

// WB Stage
void WB() {
    if (Cyc[4][0] != '0') {
        fstream out("result.txt", ios::out | ios::app);
        out << "\t" << Cyc[4] << ":WB ";
        output_signals("WB", 0, 0, 0, 0, 0, WB_RegWrite, WB_MemtoReg);
    }

    if (WB_RegWrite == 1) {
        Register[WB_Destination] = WB_MemtoReg == 1 ? ReadData : WB_Result;
    }

    WB_over = true;
}

void output_signals(const string &stage, int regDst, int aluSrc, int branch, int memRead, int memWrite, int regWrite, int memToReg) {
    fstream out("result.txt", ios::out | ios::app);
    out << stage << " Signals: ";
    out << regDst << aluSrc << " " << branch << memRead << memWrite << " " << regWrite << memToReg << endl;
}

// Initialize Values
void init_value() {
    fill(begin(Memory), end(Memory), 1);
    fill(begin(Register), end(Register), 1);
    Register[0] = 0;
}

// Main Function
int main() {
    init_value();

    int max_line = 0;
    fstream input("memory.txt");
    while (getline(input, instruction)) max_line++;
    input.close();

    while (true) {
        output_cycle(cycle);
        if (!WB_over) WB();
        if (!MEM_over) MEM();
        if (!EX_over) EX();
        if (!ID_over || stall_count > 0) ID();
        if (line < max_line) IF();
        else IF_over = true;

        stall_count--;
        if (IF_over && ID_over && EX_over && MEM_over && WB_over) break;
        cycle++;
    }

    fstream out("result.txt", ios::out | ios::app);
    out << "Cycles required: " << cycle << endl;
    output_register_memory(out);
    out.close();

    return 0;
}

void output_cycle(int cycle) {
    fstream out("result.txt", ios::out | ios::app);
    out << "Cycle " << cycle << endl;
    out.close();
}

void output_register_memory(fstream& out) {
    out << "Registers:\n";
    for (int i = 0; i < 32; i++) out << "$" << i << " " << Register[i] << "\n";
    out << "Memory:\n";
    for (int i = 0; i < 32; i++) out << "W" << i << " " << Memory[i] << "\n";
}
