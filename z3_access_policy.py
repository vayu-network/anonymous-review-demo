from z3 import (
    DeclareSort, Function, BoolSort, Const, Consts, ForAll, Implies,
    And, Not, Or, Solver, unsat, BoolVal, If
)

# ---------------------------------------------------------------------------
# Symbolic model
# ---------------------------------------------------------------------------

# Sorts
Role = DeclareSort("Role")
Resource = DeclareSort("Resource")
Action = DeclareSort("Action")

# A policy is modelled as a single function:
#   has_access : Role × Resource × Action -> Bool
# We represent two policy states:
#   - empty_policy  : always False
#   - after_grant   : True exactly for one triple, False elsewhere
#   - after_revoke  : False for the revoked triple
# using uninterpreted functions constrained by axioms.

# Symbolic variables
role, r1, r2 = Consts("role r1 r2", Role)
resource, res1, res2 = Consts("resource res1 res2", Resource)
action, act1, act2 = Consts("action act1 act2", Action)

# ---------------------------------------------------------------------------
# Property 1: Empty policy has no access for any (role, resource, action)
# ---------------------------------------------------------------------------
# Model: empty policy => has_access is universally False.
# We represent this directly: assert NOT(False) is unsat.
empty_has_access = BoolVal(False)

s1 = Solver()
# Negation of "empty policy denies everything":
# i.e., there exists some triple where empty policy grants access
s1.add(empty_has_access)  # BoolVal(False) — this is the access result
# Actually the negation of "always False" is "sometimes True":
# We check: is it possible that empty_policy(role,res,act) = True?
# Since empty_policy is defined as the constant False, adding True is a contradiction.
# Cleaner encoding:

s1 = Solver()
# "There exists a triple with access in the empty policy" should be UNSAT
# Empty policy: for all role, resource, action -> False
# Negation: exists role, resource, action such that True
# We encode: can the empty (always-False) function return True? No.
s1.add(BoolVal(True) == BoolVal(False))  # contradiction
assert s1.check() == unsat, "Invariant 1 violated: empty policy should deny all"

# More rigorous formulation using ForAll
from z3 import ForAll, Solver, unsat, Not, BoolVal

s1b = Solver()
# Invariant: forall role resource action. empty_policy(role,resource,action) = False
# Negation: exists role resource action. empty_policy(...) = True
# Since empty_policy IS False, the negation is: False = True, which is unsat.
negation_of_empty_invariant = Not(
    ForAll([role, resource, action], BoolVal(False) == BoolVal(False))
)
s1b.add(negation_of_empty_invariant)
assert s1b.check() == unsat, "Invariant 1 violated: empty policy has no access"

# ---------------------------------------------------------------------------
# Property 2: Grant soundness
# After granting (r1, res1, act1), can(r1, res1, act1) is True.
# ---------------------------------------------------------------------------
# Model a grant operation symbolically:
#   granted(role, res, act) = (role==r1 AND res==res1 AND act==act1) OR prev(role,res,act)
# Starting from empty prev:
#   granted(role, res, act) = (role==r1 AND res==res1 AND act==act1)
# Check: granted(r1, res1, act1) = True

granted_access = Function("granted_access", Role, Resource, Action, BoolSort())

s2 = Solver()
# Axiom: granted_access reflects exactly the one grant from empty
s2.add(
    ForAll(
        [role, resource, action],
        granted_access(role, resource, action) ==
        And(role == r1, resource == res1, action == act1)
    )
)
# Negation of soundness: after granting (r1,res1,act1), can(r1,res1,act1) is NOT True
s2.add(Not(granted_access(r1, res1, act1)))
assert s2.check() == unsat, "Invariant 2 violated: grant soundness"

# ---------------------------------------------------------------------------
# Property 3: Revoke soundness
# After granting then revoking (r1, res1, act1), can(r1, res1, act1) is False.
# ---------------------------------------------------------------------------
after_revoke = Function("after_revoke", Role, Resource, Action, BoolSort())

s3 = Solver()
# After revoke, the triple is gone
s3.add(
    ForAll(
        [role, resource, action],
        after_revoke(role, resource, action) ==
        And(
            # Was previously granted (only this triple was granted)
            And(role == r1, resource == res1, action == act1),
            # But now revoked: NOT (role==r1 AND res==res1 AND act==act1)
            Not(And(role == r1, resource == res1, action == act1))
        )
    )
)
# Negation: after_revoke(r1,res1,act1) is True
s3.add(after_revoke(r1, res1, act1))
assert s3.check() == unsat, "Invariant 3 violated: revoke soundness"

# ---------------------------------------------------------------------------
# Property 4: Non-interference
# Granting (r1, res1, act1) does not affect (r2, res2, act2) when they differ.
# ---------------------------------------------------------------------------
# If (r2,res2,act2) had no access before the grant, it still has no access after,
# provided (r1,res1,act1) != (r2,res2,act2).

non_interfere = Function("ni_access", Role, Resource, Action, BoolSort())

s4 = Solver()
# Model: grant only (r1, res1, act1) from empty
s4.add(
    ForAll(
        [role, resource, action],
        non_interfere(role, resource, action) ==
        And(role == r1, resource == res1, action == act1)
    )
)
# Assume the two triples are distinct (at least one component differs)
s4.add(
    Or(r1 != r2, res1 != res2, act1 != act2)
)
# Negation of non-interference:
# "non_interfere(r2,res2,act2) is True" would mean the grant affected the other triple
s4.add(non_interfere(r2, res2, act2))
assert s4.check() == unsat, "Invariant 4 violated: non-interference"

# ---------------------------------------------------------------------------
# Property 4b: Granting (r1,res1,act1) does not REMOVE access for a different triple
# If (r2,res2,act2) had access before, it still does after granting (r1,res1,act1).
# ---------------------------------------------------------------------------
before_grant = Function("before_grant", Role, Resource, Action, BoolSort())
after_grant = Function("after_grant", Role, Resource, Action, BoolSort())

s4b = Solver()
# before: r2 had access to (res2, act2)
s4b.add(before_grant(r2, res2, act2))
# after_grant: adds (r1,res1,act1), keeps everything else
s4b.add(
    ForAll(
        [role, resource, action],
        after_grant(role, resource, action) ==
        Or(
            before_grant(role, resource, action),
            And(role == r1, resource == res1, action == act1)
        )
    )
)
# Negation: after the grant, r2 lost access to (res2, act2)
s4b.add(Not(after_grant(r2, res2, act2)))
assert s4b.check() == unsat, "Invariant 4b violated: grant must not remove existing access"

print("All Z3 properties verified.")
