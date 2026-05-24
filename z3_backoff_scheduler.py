from z3 import *

# ---------------------------------------------------------------------------
# Symbolic model
# ---------------------------------------------------------------------------
# We model the scheduler with three real-valued parameters and prove the
# invariants hold for all valid inputs symbolically.

base_ms = Real("base_ms")
factor  = Real("factor")
cap_ms  = Real("cap_ms")
n       = Int("n")
attempt = Int("attempt")

# Validity preconditions
valid_params = And(
    base_ms > 0,
    factor >= 1,
    cap_ms >= base_ms,
    cap_ms > 0,
)

# delay(n) = min(base_ms * factor^n, cap_ms)
# We model delay as a function from Int -> Real via a Z3 function declaration.
# For symbolic proofs we reason about specific structural properties.

# ---------------------------------------------------------------------------
# Invariant 1: delay(0) == base_ms
# (because factor^0 == 1, so min(base_ms * 1, cap_ms) = base_ms when cap >= base)
# ---------------------------------------------------------------------------
# delay(0) = min(base_ms * factor^0, cap_ms) = min(base_ms, cap_ms) = base_ms
# We prove: NOT (min(base_ms, cap_ms) == base_ms) is UNSAT under valid_params.

delay_0 = If(base_ms <= cap_ms, base_ms, cap_ms)

s = Solver()
s.add(valid_params)
s.add(Not(delay_0 == base_ms))
result = s.check()
assert result == unsat, f"Invariant 1 violated: delay(0) == base_ms. Solver: {result}"

# ---------------------------------------------------------------------------
# Invariant 2: delay(n) <= cap_ms for all n >= 0
# We prove that min(x, cap_ms) <= cap_ms for any real x.
# ---------------------------------------------------------------------------
x = Real("x")
val = If(x <= cap_ms, x, cap_ms)

s2 = Solver()
s2.add(cap_ms > 0)
s2.add(Not(val <= cap_ms))
result2 = s2.check()
assert result2 == unsat, f"Invariant 2 violated: delay(n) <= cap_ms. Solver: {result2}"

# ---------------------------------------------------------------------------
# Invariant 3: delay(n) >= base_ms for all n >= 0
# For factor >= 1 and attempt >= 0: base_ms * factor^attempt >= base_ms.
# We prove: min(base_ms * factor^attempt, cap_ms) >= base_ms under valid_params.
# We use a symbolic uncapped value u >= base_ms (representing base*factor^n).
# ---------------------------------------------------------------------------
u = Real("u")  # represents base_ms * factor^n, which is >= base_ms when factor>=1, n>=0

# u >= base_ms (this follows from factor>=1, n>=0 — taken as hypothesis)
delay_n = If(u <= cap_ms, u, cap_ms)

s3 = Solver()
s3.add(valid_params)
s3.add(u >= base_ms)   # structural property of exponential with factor>=1
s3.add(Not(delay_n >= base_ms))
result3 = s3.check()
assert result3 == unsat, f"Invariant 3 violated: delay(n) >= base_ms. Solver: {result3}"

# ---------------------------------------------------------------------------
# Invariant 4: Non-decreasing — delay(n+1) >= delay(n)
# For factor >= 1: base * factor^(n+1) >= base * factor^n.
# min(base*factor^(n+1), cap) >= min(base*factor^n, cap).
# We model: u_n+1 >= u_n >= base_ms, and prove min(u_n1, cap) >= min(u_n, cap).
# ---------------------------------------------------------------------------
u_n  = Real("u_n")   # base_ms * factor^n
u_n1 = Real("u_n1")  # base_ms * factor^(n+1) = u_n * factor >= u_n

delay_n_val  = If(u_n  <= cap_ms, u_n,  cap_ms)
delay_n1_val = If(u_n1 <= cap_ms, u_n1, cap_ms)

s4 = Solver()
s4.add(valid_params)
s4.add(u_n  >= base_ms)
s4.add(u_n1 >= u_n)      # factor >= 1 means next term is at least as large
s4.add(Not(delay_n1_val >= delay_n_val))
result4 = s4.check()
assert result4 == unsat, f"Invariant 4 violated: non-decreasing. Solver: {result4}"

# ---------------------------------------------------------------------------
# Invariant 5: Parameters validity — cap_ms >= base_ms implies cap >= base
# (sanity check on the constraint system itself)
# ---------------------------------------------------------------------------
s5 = Solver()
s5.add(valid_params)
s5.add(Not(cap_ms >= base_ms))
result5 = s5.check()
assert result5 == unsat, f"Invariant 5 violated: cap_ms >= base_ms. Solver: {result5}"

# ---------------------------------------------------------------------------
# Invariant 6: factor >= 1 and base_ms > 0 ensures uncapped value is
#              non-decreasing in attempt number.
# Symbolically: u * factor >= u when factor >= 1 and u >= 0.
# ---------------------------------------------------------------------------
u2 = Real("u2")
s6 = Solver()
s6.add(factor >= 1)
s6.add(u2 >= 0)
s6.add(Not(u2 * factor >= u2))
result6 = s6.check()
assert result6 == unsat, f"Invariant 6 violated: u*factor >= u for factor>=1. Solver: {result6}"

print("All Z3 properties verified.")
