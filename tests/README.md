# What the tests are allowed to specify

Tests are evidence for an agreed contract, not a substitute for deciding it. The package core is generic Boolean syntax; database behavior is optional. Passing historical tests is not a compatibility requirement.

## Semantic laws

The independent Boolean evaluator in `transformations/test_boolean_contract.py` defines AND, OR, and NOT over arbitrary independent symbols. It checks simplification, canonicalization, and parse/serialize round trips across every assignment for 1,878 shallow expression trees and 512 deeper seeded samples. It does not call production implication/matching logic to obtain expected values. These checks guarantee meaning preservation for the exercised cases, not completeness or a particular normal form.

Evidence tests require that a reported removal has a surviving witness, and that diagnostics and rewrites use the same decision. They do not require one particular traversal, association, representative ordering, or exhaustive theorem proving.

## Explicit API and grammar choices

The documented grammar chooses uppercase operators, NOT > AND > OR precedence, balanced parentheses, and opaque terms composed of contiguous quoted/unquoted fragments. Raw terms retain case and quoting. Parsing consumes the full input and reports syntax errors with character offsets. Implicit AND requires explicit opt-in.

These are chosen contracts, not universal search-engine rules. A deliberate grammar/API change should update these tests after the contract is changed. Structural examples test the grammar; they do not claim a database interprets the same query identically.

API tests cover raw inventories with a caller-supplied normalization key, immutable ASTs, matcher substitution, validated diagnostic variants, and style-independent rendering. They avoid exact message snapshots, canonical branch ordering, and parentheses/ANSI-span placement.

## Optional conventions

`conventions/` tests apply only when callers explicitly select lexical behavior. Contiguous phrase containment and casefolded quote-stripped inventories are heuristics, not Boolean identities or verified PubMed semantics. Custom matcher substitution tests check that algorithms need only the published protocol, not the built-in implementation.

## Retired inherited assumptions

Removed tests and compatibility-only reporting helpers that required lowercase tuple/set projections, specialized cross-query inventory reports, exact formatted prefixes, object identity from composition, or numerous restatements of phrase-containment examples. Useful absorption scenarios remain covered by generic Boolean laws, regression cases, and explicit opt-in convention tests. Test count is not a quality target.
