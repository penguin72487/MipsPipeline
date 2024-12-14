#include <bits/stdc++.h>
#include <filesystem>
#define endl "\n"
using namespace std;
namespace fs = std::filesystem;

int main() {
    cin.tie(0)->sync_with_stdio(0);
    cout.tie(0);
    
    fs::path input_Path = "inputs";
    fs::path output_Path = "outputs";
    vector<string> input_Files = {"test1.txt", "test2.txt", "test3.txt", "test4.txt", "test5.txt", "test6.txt"};

    if (!fs::exists(output_Path)) {
        fs::create_directory(output_Path);
    }

    for (const auto& file : input_Files) {
        fs::path input = input_Path / file;
        fs::path output = output_Path / file;

        if (!fs::exists(input)) {
            cerr << "Error: File does not exist: " << input << endl;
            continue;
        }

        // 打開輸入檔案
        ifstream fin(input);
        if (!fin) {
            cerr << "Error opening input file: " << input << endl;
            continue;
        }

        // 打開輸出檔案
        ofstream fout(output);
        if (!fout) {
            cerr << "Error opening output file: " << output << endl;
            continue;
        }

        string instruction;
        char trash;
        while (fin >> instruction) {
            if (instruction == "lw") {
                int rd, offset, rs;
                fin >> trash >> rd >> trash >> offset >> trash >> trash >> rs >> trash;
                fout << "lw $" << rd << ", " << offset << "($" << rs << ")" << endl;
            } else if (instruction == "sw") {
                int rd, offset, rs;
                fin >> trash >> rd >> trash >> offset >> trash >> trash >> rs >> trash;
                fout << "sw $" << rd << ", " << offset << "($" << rs << ")" << endl;
            } else if (instruction == "beq") {
                int rs, rt, offset;
                fin >> trash >> rs >> trash >> trash >> rt >> trash >> offset;
                fout << "beq $" << rs << ", $" << rt << ", " << offset << endl;
            } else if (instruction == "add") {
                int rd, rs, rt;
                fin >> trash >> rd >> trash >> trash >> rs >> trash >> trash >> rt;
                fout << "add $" << rd << ", $" << rs << ", $" << rt << endl;
            } else if (instruction == "sub") {
                int rd, rs, rt;
                fin >> trash >> rd >> trash >> trash >> rs >> trash >> trash >> rt;
                fout << "sub $" << rd << ", $" << rs << ", $" << rt << endl;
            } else {
                fout << "Unknown instruction: " << instruction << endl;
            }
        }

        fin.close();
        fout.close();
    }

    return 0;
}
