class ContractViolation(Exception):
    """A Segment/Caption stream broke its contract.

    Raised instead of silently skipping or coercing bad data: a malformed
    or out-of-order stream must fail loudly (issue 0005).
    """
