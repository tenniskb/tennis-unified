"""Test fixed pattern."""
import re
# For +---+---+ we have: + --- + --- +
# Pattern needs: \+[-:=]+\+[-:=]+\+
# Or generically: \+[-:=]+\+[-:=]+\+ or \+ followed by pairs \+[-:=]+
# So: \+([-:=]+\+)+  meaning start with +, then alternate: dashes+, plus+, ...

# For 2-cell: +---+---+ structure: +, dashes, +, dashes, +
# Regex: \+[-:=]+\+[-:=]+\+  (3 explicit +s, 2 cell-content groups)
# For 3-cell: +---+---+---+ → \+[-:=]+\+[-:=]+\+[-:=]+\+ (4 +s, 3 cells)

# Generic pattern: \+ followed by pairs of (cell-content, +)
PAT = re.compile(r"^\+[-:=]+(?:\+[-:=]+)*\+$")
# Or with explicit count
PAT2 = re.compile(r"^\+[-:=]+\+[-:=]+\+$")  # exactly 2 cells

tests = [
    "+---+---+",            # 2 cells
    "+---+---+---+",        # 3 cells
    "+---+---+---+---+",    # 4 cells
    "+====================================================================================================+========================================+",  # 2 cells long
]
for t in tests:
    print(f"Generic match {t[:30]}...: {bool(PAT.match(t))}")
    print(f"  2-cell match: {bool(PAT2.match(t))}")