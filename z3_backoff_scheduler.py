from z3 import *

# ---------------------------------------------------------------------------
# Symbolic model
# ---------------------------------------------------------------------------
# We model the scheduler with three real-valued parameters and prove the
# key invariants hold for all valid inputs and all attempt indices.

base  = Real("base")   # base_ms
fac   = Real("fac")    # factor
cap   = Real("cap")    # cap_ms
n     = Int("n")       # attempt index

# Validity preconditions for parameters
valid_params = And(
    base > 0,
    fac >= 1,
    cap >= base,
)

# The delay function: min(base * fac^n, cap)
# Z3 doesn't have a native power over reals for symbolic exponents, so we
# model f(n) = base * r where r >= 1 represents fac**n symbolically.
# We introduce r as an uninterpreted representative of fac**n satisfying:
#   r >= 1   (since fac >= 1, n >= 0  =>  fac**n >= 1)
#   r >= fac^0 = 1  (already covered)
# For non-decreasing we use r_n and r_n1 = r_n * fac.

r   = Real("r")    # represents fac**n  (>= 1 when fac>=1, n>=0)
r1  = Real("r1")   # represents fac**(n+1) = r * fac

# Symbolic delay values
def sym_delay(r_val: ArithRef) -> ArithRef:
    raw = base * r_val
    return If(raw <= cap, raw, cap)

d_n  = sym_delay(r)
d_n1 = sym_delay(r1)

# Precondition: r represents fac**n for n>=0, fac>=1 => r >= 1
param_and_r = And(valid_params, n >= 0, r >= 1, r1 == r * fac)

# ---------------------------------------------------------------------------
# Invariant 1: delay(0) == base_ms
# (r = fac**0 = 1, so delay(0) = min(base*1, cap) = min(base, cap) = base
#  because cap >= base)
# ---------------------------------------------------------------------------
inv1_premise = And(base > 0, fac >= 1, cap >= base)
delay_0 = If(base <= cap, base, cap)  # min(base*1, cap)

s = Solver()
# Negate: delay(0) != base
s.add(inv1_premise)
s.add(delay_0 != base)
result = s.check()
assert result == unsat, f"Invariant 1 violated: delay(0) != base_ms  ({result})"

# ---------------------------------------------------------------------------
# Invariant 2: delay(n) <= cap_ms  for all n >= 0
# ---------------------------------------------------------------------------
s = Solver()
s.add(param_and_r)
s.add(d_n > cap)
result = s.check()
assert result == unsat, f"Invariant 2 violated: delay(n) > cap_ms  ({result})"

# ---------------------------------------------------------------------------
# Invariant 3: delay(n) >= base_ms  for all n >= 0
# (since fac >= 1 and r >= 1 => base*r >= base; then min(base*r, cap) >= base
#  because cap >= base >= base)
# ---------------------------------------------------------------------------
s = Solver()
s.add(param_and_r)
s.add(d_n < base)
result = s.check()
assert result == unsat, f"Invariant 3 violated: delay(n) < base_ms  ({result})"

# ---------------------------------------------------------------------------
# Invariant 4: delay(n+1) >= delay(n)  (non-decreasing)
# r1 = r * fac >= r  (since fac >= 1, r >= 1)
# so base * r1 >= base * r
# min(base*r1, cap) >= min(base*r, cap) follows from monotonicity of min
# ---------------------------------------------------------------------------
s = Solver()
s.add(param_and_r)
s.add(d_n1 < d_n)
result = s.check()
assert result == unsat, f"Invariant 4 violated: delay(n+1) < delay(n)  ({result})"

# ---------------------------------------------------------------------------
# Invariant 5: Constructor rejects factor < 1
# If fac < 1 we should NOT have a valid scheduler.  Prove that fac < 1
# implies the premise "fac >= 1" is false (trivially consistent check).
# More usefully: prove that with fac < 1, base*r can be < base when r < 1,
# i.e., the non-decreasing property would break.  We show that assuming
# fac < 1 and 0 < fac and r >= 0 and r1 = r*fac, it IS possible that
# r1 < r — meaning the invariant would be violated, so rejection is correct.
# ---------------------------------------------------------------------------
s = Solver()
s.add(base > 0)
s.add(And(fac > 0, fac < 1))  # invalid factor
s.add(r > 0)
s.add(r1 == r * fac)
s.add(r1 < r)  # we expect this to be SAT (counter-model exists)
result = s.check()
assert result == sat, (
    "Invariant 5 sanity check failed: expected SAT when factor < 1 breaks monotonicity"
)

# ---------------------------------------------------------------------------
# Invariant 6: cap_ms < base_ms is rejected — prove that with cap < base,
# delay(0) = min(base, cap) = cap != base, violating Req 4.
# ---------------------------------------------------------------------------
s = Solver()
s.add(base > 0, fac >= 1, cap > 0, cap < base)  # invalid: cap < base
delay_0_bad = If(base <= cap, base, cap)
s.add(delay_0_bad == base)  # assert delay(0) == base would hold
result = s.check()
assert result == unsat, (
    f"Invariant 6 violated: cap < base should make delay(0) != base, but got {result}"
)

print("All Z3 properties verified.")
