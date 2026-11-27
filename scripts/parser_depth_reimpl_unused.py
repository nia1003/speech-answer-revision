"""H1 check 1 / CP2: GSM8K dependency depth by program, PRE-FIX version (rules exactly as the frozen plan's
"程式抽取規則（目前版本）"). No fixes here; fixes belong to CP7.
  1. every <<expr=result>> is one step
  2. number token regex (?<![\w.])\d+(?:,\d{3})*(?:\.\d+)?
  3. a step depends on an earlier step if a number in its expr equals that step's result (take the nearest such step)
  4. depth = longest path in the dependency graph (in steps)
  5. ambiguous = a number equals an earlier step's result AND also appears among the question's numbers
usage: python3 parser_depth.py <gsm8k_test.jsonl> <out.jsonl>"""
import sys, re, json
from collections import Counter

NUM = re.compile(r"(?<![\w.])\d+(?:,\d{3})*(?:\.\d+)?")
CALC = re.compile(r"<<([^<>]*?)=([^<>=]*)>>")
val = lambda s: float(s.replace(",", ""))
nums = lambda s: [val(x) for x in NUM.findall(s)]

def depth_of(question, solution):
    qn = set(nums(question))
    steps = []                       # (result value or None, depth)
    amb = False
    for expr, res in CALC.findall(solution):
        r = nums(res); r = r[0] if r else None
        d = 1
        for x in nums(expr):
            hit = next((j for j in range(len(steps) - 1, -1, -1) if steps[j][0] == x), None)
            if hit is not None:
                d = max(d, steps[hit][1] + 1)
                if x in qn: amb = True
        steps.append((r, d))
    return (max((d for _, d in steps), default=0), len(steps), amb)

if __name__ == "__main__":
    rows = [json.loads(l) for l in open(sys.argv[1])]
    out = []
    for i, r in enumerate(rows):
        sol = r["answer"].split("####")[0].strip()
        d, n, a = depth_of(r["question"], sol)
        out.append({"idx": i, "parser_version": "pre-fix", "parser_depth": d, "parser_steps": n, "ambiguous": a,
                    "unmarked_lines": None})   # unmarked detection is a CP7 fix; not part of the pre-fix rules
    with open(sys.argv[2], "w") as f:
        for o in out: f.write(json.dumps(o) + "\n")
    print("depth", dict(sorted(Counter(o["parser_depth"] for o in out).items())),
          "ambiguous", sum(o["ambiguous"] for o in out))
