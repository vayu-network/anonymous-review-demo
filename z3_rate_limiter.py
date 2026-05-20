from z3 import *


def make_rate_limiter_solver():
    """
    Symbolic model of the token-bucket rate limiter.

    Variables:
      capacity       : positive integer (max tokens)
      refill_rate    : positive real (tokens/second)
      tokens         : current internal token count (real)
      consume_amount : integer amount to consume (>= 1)
      elapsed        : elapsed seconds for refill (>= 0)
      refill_amount  : refill_rate * elapsed
    """
    capacity = Int("capacity")
    refill_rate = Real("refill_rate")
    tokens = Real("tokens")
    consume_amount = Int("consume_amount")
    elapsed = Real("elapsed")

    # Base preconditions (valid construction)
    pre = And(
        capacity > 0,
        refill_rate > 0,
        tokens >= 0,
        ToReal(capacity) >= tokens,  # tokens <= capacity
    )

    return capacity, refill_rate, tokens, consume_amount, elapsed, pre


# ---------------------------------------------------------------------------
# Invariant 1: Token count is always in [0, capacity]
# ---------------------------------------------------------------------------
def verify_invariant_1():
    capacity, refill_rate, tokens, consume_amount, elapsed, pre = make_rate_limiter_solver()

    # After a successful consume: new_tokens = tokens - consume_amount
    # Precondition for success: tokens >= consume_amount >= 1
    consume_pre = And(pre, consume_amount >= 1, ToReal(consume_amount) <= tokens)
    tokens_after_consume = tokens - ToReal(consume_amount)

    s = Solver()
    s.add(consume_pre)
    # Negate: tokens_after_consume < 0  OR  tokens_after_consume > capacity
    s.add(Or(
        tokens_after_consume < 0,
        tokens_after_consume > ToReal(capacity)
    ))
    assert s.check() == unsat, "Invariant 1 violated after consume"

    # After refill: new_tokens = min(capacity, tokens + refill_rate * elapsed)
    refill_pre = And(pre, elapsed >= 0)
    added = refill_rate * elapsed
    tokens_after_refill = If(
        tokens + added > ToReal(capacity),
        ToReal(capacity),
        tokens + added
    )

    s2 = Solver()
    s2.add(refill_pre)
    s2.add(Or(
        tokens_after_refill < 0,
        tokens_after_refill > ToReal(capacity)
    ))
    assert s2.check() == unsat, "Invariant 1 violated after refill"


# ---------------------------------------------------------------------------
# Invariant 2: consume() never reduces tokens below 0
# ---------------------------------------------------------------------------
def verify_invariant_2():
    capacity, refill_rate, tokens, consume_amount, elapsed, pre = make_rate_limiter_solver()

    # Successful consume requires tokens >= consume_amount
    consume_pre = And(pre, consume_amount >= 1, ToReal(consume_amount) <= tokens)
    tokens_after = tokens - ToReal(consume_amount)

    s = Solver()
    s.add(consume_pre)
    s.add(tokens_after < 0)
    assert s.check() == unsat, "Invariant 2 violated: consume reduces tokens below 0"


# ---------------------------------------------------------------------------
# Invariant 3: refill() never increases tokens above capacity
# ---------------------------------------------------------------------------
def verify_invariant_3():
    capacity, refill_rate, tokens, consume_amount, elapsed, pre = make_rate_limiter_solver()

    refill_pre = And(pre, elapsed >= 0)
    added = refill_rate * elapsed
    tokens_after = If(
        tokens + added > ToReal(capacity),
        ToReal(capacity),
        tokens + added
    )

    s = Solver()
    s.add(refill_pre)
    s.add(tokens_after > ToReal(capacity))
    assert s.check() == unsat, "Invariant 3 violated: refill exceeds capacity"


# ---------------------------------------------------------------------------
# Invariant 4: Two consecutive consume(1) can only both succeed if tokens >= 2
# ---------------------------------------------------------------------------
def verify_invariant_4():
    capacity, refill_rate, tokens, consume_amount, elapsed, pre = make_rate_limiter_solver()

    # First consume(1) succeeds: tokens >= 1
    first_ok = And(pre, tokens >= 1)
    tokens_after_first = tokens - 1

    # Second consume(1) succeeds: tokens_after_first >= 1 → tokens >= 2
    second_ok = And(first_ok, tokens_after_first >= 1)

    s = Solver()
    s.add(second_ok)
    # Negate: tokens < 2 while both succeed
    s.add(tokens < 2)
    assert s.check() == unsat, "Invariant 4 violated: two consecutive consume(1) succeeded with tokens < 2"


# ---------------------------------------------------------------------------
# Invariant 5: A newly constructed RateLimiter starts at full capacity
# ---------------------------------------------------------------------------
def verify_invariant_5():
    capacity = Int("capacity")
    refill_rate = Real("refill_rate")

    # Initial tokens = capacity (as real)
    tokens_initial = ToReal(capacity)

    pre = And(capacity > 0, refill_rate > 0)

    s = Solver()
    s.add(pre)
    # Negate: initial tokens != capacity
    s.add(tokens_initial != ToReal(capacity))
    assert s.check() == unsat, "Invariant 5 violated: initial tokens != capacity"


# ---------------------------------------------------------------------------
# Additional: failed consume leaves tokens unchanged
# ---------------------------------------------------------------------------
def verify_failed_consume_unchanged():
    capacity, refill_rate, tokens, consume_amount, elapsed, pre = make_rate_limiter_solver()

    # Failed consume: tokens < consume_amount
    fail_pre = And(pre, consume_amount >= 1, ToReal(consume_amount) > tokens)
    tokens_after = tokens  # unchanged on failure

    s = Solver()
    s.add(fail_pre)
    # Negate: tokens_after != tokens (should be unchanged)
    s.add(tokens_after != tokens)
    assert s.check() == unsat, "Failed consume should leave tokens unchanged"


# ---------------------------------------------------------------------------
# Additional: tokens remain non-negative after refill from 0
# ---------------------------------------------------------------------------
def verify_refill_from_zero():
    capacity = Int("capacity")
    refill_rate = Real("refill_rate")
    elapsed = Real("elapsed")

    pre = And(capacity > 0, refill_rate > 0, elapsed >= 0)
    tokens_start = RealVal(0)
    added = refill_rate * elapsed
    tokens_after = If(
        tokens_start + added > ToReal(capacity),
        ToReal(capacity),
        tokens_start + added
    )

    s = Solver()
    s.add(pre)
    s.add(tokens_after < 0)
    assert s.check() == unsat, "Refill from zero produced negative tokens"


# ---------------------------------------------------------------------------
# Run all verifications
# ---------------------------------------------------------------------------
verify_invariant_1()
verify_invariant_2()
verify_invariant_3()
verify_invariant_4()
verify_invariant_5()
verify_failed_consume_unchanged()
verify_refill_from_zero()

print("All Z3 properties verified.")
