import re
PAT = re.compile(r"^\s*\+[-:=]+(?:\+[-:=]+)+\s*\r?$")
# Earlier test said simple works
PAT2 = re.compile(r"^\+(?:[-:=]+\+){2,}\s*\r?$")
test = "+---+---+---+"
print("Simple {2,}:", bool(PAT2.match(test)))

# Now what fails?
line = "+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+"
print("Line len:", len(line))
print("First 20:", line[:20])
print("Last 20:", line[-20:])

# Try pattern with explicit + separator
PAT3 = re.compile(r"^\s*\+[-:=]+\+[-:=]+\+\s*$")
print("3 sep:", bool(PAT3.match(line)))

PAT4 = re.compile(r"^\s*\+(?:[-:=]+\+){2,}\s*$")
print("Generic with {2,}:", bool(PAT4.match(line)))

# Wait - the line has many + signs in many cells. Let me count
plus_positions = [i for i, c in enumerate(line) if c == '+']
print(f"Plus positions: {len(plus_positions)} -> first 5: {plus_positions[:5]}, last 5: {plus_positions[-5:]}")