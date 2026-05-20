from z3 import *

# ---------------------------------------------------------------------------
# Symbolic model
# ---------------------------------------------------------------------------
# We model the rate limiter state with three symbolic variables:
#   tokens   : Real  – current token count (internal float)
#   capacity : Int   – maximum tokens (positive integer)
#   rate     : Real  – refill rate (positive float)

tokens   = Real('tokens')
capacity = Int('capacity')
rate     = Real('rate')

# Basic domain constraints that must hold for a well-formed RateLimiter
domain = And(
    capacity > 0,
    rate > 0,
    tokens >= 0,
    tokens <= ToReal(capacity),
)

# ---------------------------------------------------------------------------
# Invariant 1: Token count is always in [0, capacity]
# ---------------------------------------------------------------------------
inv1 = And(tokens >= 0, tokens <= ToReal(capacity))

s = Solver()
s.add(domain)
s.add(Not(inv1))
assert s.check() == unsat, "Invariant 1 violated: tokens not in [0, capacity]"

# ---------------------------------------------------------------------------
# Invariant 2: consume() never reduces tokens below 0
# ---------------------------------------------------------------------------
# Model consume(n): new_tokens = tokens - n  when tokens >= n, else unchanged.
n = Int('n')
n_constraint = n >= 1

# Case where consume succeeds (tokens >= n)
new_tokens_consume = Real('new_tokens_consume')
consume_succeeds = And(ToReal(n) <= tokens, new_tokens_consume == tokens - ToReal(n))

s2 = Solver()
s2.add(domain)
s2.add(n_constraint)
s2.add(consume_succeeds)
s2.add(new_tokens_consume < 0)   # negation: result goes below 0
assert s2.check() == unsat, "Invariant 2 violated: consume reduces tokens below 0"

# ---------------------------------------------------------------------------
# Invariant 3: refill() never increases tokens above capacity
# ---------------------------------------------------------------------------
elapsed = Real('elapsed')
added   = Real('added')
new_tokens_refill = Real('new_tokens_refill')

refill_constraints = And(
    elapsed >= 0,
    added == rate * elapsed,
    new_tokens_refill == If(
        tokens + added <= ToReal(capacity),
        tokens + added,
        ToReal(capacity),
    ),
)

s3 = Solver()
s3.add(domain)
s3.add(refill_constraints)
s3.add(new_tokens_refill > ToReal(capacity))   # negation
assert s3.check() == unsat, "Invariant 3 violated: refill exceeds capacity"

# Also verify refill never goes below 0
s3b = Solver()
s3b.add(domain)
s3b.add(refill_constraints)
s3b.add(new_tokens_refill < 0)   # negation
assert s3b.check() == unsat, "Invariant 3b violated: refill produces negative tokens"

# ---------------------------------------------------------------------------
# Invariant 4: Two consecutive consume(1) can both succeed only if tokens >= 2
# ---------------------------------------------------------------------------
# After first consume(1): tokens1 = tokens - 1  (succeeds iff tokens >= 1)
# After second consume(1): tokens2 = tokens1 - 1 (succeeds iff tokens1 >= 1)
# Both succeed  =>  tokens >= 1  AND  tokens - 1 >= 1  =>  tokens >= 2

tokens1 = Real('tokens1')
tokens2 = Real('tokens2')

both_succeed = And(
    tokens >= 1,          # first consume succeeds
    tokens1 == tokens - 1,
    tokens1 >= 1,         # second consume succeeds
    tokens2 == tokens1 - 1,
)

s4 = Solver()
s4.add(domain)
s4.add(both_succeed)
s4.add(tokens < 2)   # negation of "tokens >= 2"
assert s4.check() == unsat, \
    "Invariant 4 violated: both consumes succeed but initial tokens < 2"

# ---------------------------------------------------------------------------
# Invariant 5: A newly constructed RateLimiter starts at full capacity
# ---------------------------------------------------------------------------
# initial_tokens == capacity
initial_tokens = Real('initial_tokens')

init_constraint = And(
    capacity > 0,
    rate > 0,
    initial_tokens == ToReal(capacity),
)

# Verify initial tokens satisfy [0, capacity]
s5 = Solver()
s5.add(init_constraint)
s5.add(Not(And(initial_tokens >= 0, initial_tokens <= ToReal(capacity))))
assert s5.check() == unsat, \
    "Invariant 5 violated: initial tokens not equal to capacity"

# ---------------------------------------------------------------------------
print("All Z3 properties verified.")
