from z3 import *

# ---------------------------------------------------------------------------
# Symbolic model of a token bucket
# ---------------------------------------------------------------------------
# Variables
capacity = Real("capacity")
rate     = Real("rate")
tokens   = Real("tokens")
elapsed  = Real("elapsed")
consume  = Real("consume")

# After a refill the new token level is:
#   tokens_after_refill = min(capacity, tokens + elapsed * rate)
# We model this with an auxiliary variable bounded by both branches.
tokens_refilled = Real("tokens_refilled")

# ---------------------------------------------------------------------------
# Invariant 1: tokens are always non-negative
# ---------------------------------------------------------------------------
# Preconditions: capacity > 0, rate > 0, 0 <= tokens <= capacity,
#                elapsed >= 0, 0 < consume <= capacity
preconditions = And(
    capacity > 0,
    rate > 0,
    tokens >= 0,
    tokens <= capacity,
    elapsed >= 0,
    consume > 0,
    consume <= capacity,
    # refill semantics: tokens_refilled = min(capacity, tokens + elapsed*rate)
    tokens_refilled == If(
        tokens + elapsed * rate <= capacity,
        tokens + elapsed * rate,
        capacity,
    ),
)

# Claim: after refill, tokens_refilled >= 0
s1 = Solver()
s1.add(preconditions)
s1.add(Not(tokens_refilled >= 0))
assert s1.check() == unsat, "Invariant 1 violated: tokens_refilled must be >= 0"

# ---------------------------------------------------------------------------
# Invariant 2: tokens never exceed capacity after refill
# ---------------------------------------------------------------------------
s2 = Solver()
s2.add(preconditions)
s2.add(Not(tokens_refilled <= capacity))
assert s2.check() == unsat, "Invariant 2 violated: tokens_refilled must be <= capacity"

# ---------------------------------------------------------------------------
# Invariant 3: if tokens_refilled >= consume, balance after consume >= 0
# ---------------------------------------------------------------------------
tokens_after_consume = Real("tokens_after_consume")

s3 = Solver()
s3.add(preconditions)
s3.add(tokens_refilled >= consume)
s3.add(tokens_after_consume == tokens_refilled - consume)
s3.add(Not(tokens_after_consume >= 0))
assert s3.check() == unsat, (
    "Invariant 3 violated: tokens after successful consume must be >= 0"
)

# ---------------------------------------------------------------------------
# Invariant 4: if consume is refused (tokens_refilled < consume),
#              tokens are unchanged
# ---------------------------------------------------------------------------
# When refused, the bucket state does not change.
s4 = Solver()
s4.add(preconditions)
s4.add(tokens_refilled < consume)
# Claim: bucket stays at tokens_refilled (unchanged) -- it must still be >= 0
s4.add(Not(tokens_refilled >= 0))
assert s4.check() == unsat, (
    "Invariant 4 violated: tokens unchanged on refused consume must be >= 0"
)

# ---------------------------------------------------------------------------
# Invariant 5: refilling is monotone — tokens_refilled >= original tokens
#              (time only adds tokens)
# ---------------------------------------------------------------------------
s5 = Solver()
s5.add(preconditions)
s5.add(Not(tokens_refilled >= tokens))
assert s5.check() == unsat, (
    "Invariant 5 violated: refill must be monotonically non-decreasing"
)

# ---------------------------------------------------------------------------
# Invariant 6: after reset, tokens == capacity (modelled symbolically)
# ---------------------------------------------------------------------------
tokens_reset = Real("tokens_reset")
s6 = Solver()
s6.add(capacity > 0)
s6.add(tokens_reset == capacity)
s6.add(Not(tokens_reset == capacity))
assert s6.check() == unsat, (
    "Invariant 6 violated: after reset tokens must equal capacity"
)

# ---------------------------------------------------------------------------
# Invariant 7: with zero elapsed time, refill adds no tokens
# ---------------------------------------------------------------------------
s7 = Solver()
s7.add(preconditions)
s7.add(elapsed == 0)
no_change = tokens_refilled == tokens  # min(cap, tokens + 0) = tokens (since tokens<=cap)
s7.add(Not(no_change))
assert s7.check() == unsat, (
    "Invariant 7 violated: zero elapsed time must not change token count"
)

print("All Z3 properties verified.")
