import os 
class MUPS:
    pass


with open(os.path.join(os.path.dirname(__file__), '../inputs/test3.txt'), 'r') as f:
    lines = f.readlines()

print(lines)
