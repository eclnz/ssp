from string_parser import (
    canonicalize,
    classify_change,
    collect_terms,
    combine,
    find_absorbed_branches,
    find_and_redundancies,
    find_duplicate_terms,
    find_subsumed_branches,
    find_subsumed_terms,
    format_simplification_diff,
    format_string_diff,
    lint_string,
    parse,
    simplify,
    suggest_simplification,
    unparse,
)


class TestCollectTerms:
    def test_single_term(self) -> None:
        assert collect_terms(parse("COPD")) == {"copd"}

    def test_and_expression(self) -> None:
        assert collect_terms(parse("COPD AND NIV")) == {"copd", "niv"}

    def test_or_expression(self) -> None:
        assert collect_terms(parse("COPD OR AECOPD")) == {"copd", "aecopd"}

    def test_not_expression(self) -> None:
        assert collect_terms(parse("COPD NOT asthma")) == {"copd", "asthma"}

    def test_quoted_phrase_stripped(self) -> None:
        terms = collect_terms(parse('"high flow nasal cannula"'))
        assert "high flow nasal cannula" in terms

    def test_nested_brackets(self) -> None:
        terms = collect_terms(parse('(COPD OR "chronic obstructive pulmonary disease") AND (NIV OR BiPAP)'))
        assert terms == {"copd", "chronic obstructive pulmonary disease", "niv", "bipap"}

    def test_deeply_nested_brackets(self) -> None:
        terms = collect_terms(parse('((COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)) AND RCT'))
        assert terms == {"copd", "aecopd", "non-invasive ventilation", "niv", "rct"}

    def test_case_insensitive(self) -> None:
        assert collect_terms(parse("COPD AND copd")) == {"copd"}

    def test_quoted_and_unquoted_same_term(self) -> None:
        terms = collect_terms(parse('NIV AND "NIV"'))
        assert terms == {"niv"}


class TestClassifyChange:
    def test_pure_expansion(self) -> None:
        added, removed = classify_change(
            '(COPD OR "chronic obstructive pulmonary disease") AND NIV',
            '(COPD OR "chronic obstructive pulmonary disease") AND (NIV OR BiPAP)',
        )
        assert added == {"bipap"}
        assert removed == set()

    def test_pure_narrowing(self) -> None:
        added, removed = classify_change(
            '(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV OR BiPAP)',
            '(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)',
        )
        assert added == set()
        assert removed == {"bipap"}

    def test_mixed_change(self) -> None:
        added, removed = classify_change(
            '(COPD OR AECOPD) AND "non-invasive ventilation"',
            '(COPD OR AECOPD) AND "high flow nasal cannula"',
        )
        assert added == {"high flow nasal cannula"}
        assert removed == {"non-invasive ventilation"}

    def test_structural_change_same_terms(self) -> None:
        added, removed = classify_change(
            "(COPD AND NIV)",
            "COPD OR NIV",
        )
        assert added == set()
        assert removed == set()

    def test_identical_strings(self) -> None:
        added, removed = classify_change(
            '(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)',
            '(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)',
        )
        assert added == set()
        assert removed == set()

    def test_quoted_phrase_expansion(self) -> None:
        added, removed = classify_change(
            "COPD AND NIV",
            'COPD AND (NIV OR "high flow nasal oxygen")',
        )
        assert added == {"high flow nasal oxygen"}
        assert removed == set()


class TestFindSubsumedTerms:
    def test_basic_subphrase(self) -> None:
        # "high flow" subsumes "high flow therapy"
        pairs = find_subsumed_terms({"high flow", "high flow therapy", "copd"})
        assert ("high flow", "high flow therapy") in pairs

    def test_middle_subphrase(self) -> None:
        # "flow nasal" appears inside "high flow nasal cannula"
        pairs = find_subsumed_terms({"flow nasal", "high flow nasal cannula"})
        assert ("flow nasal", "high flow nasal cannula") in pairs

    def test_no_subsumption(self) -> None:
        assert find_subsumed_terms({"copd", "niv", "bipap"}) == []

    def test_exact_match_not_flagged(self) -> None:
        # same term twice would be a duplicate, not a subphrase
        assert find_subsumed_terms({"high flow"}) == []

    def test_multiple_subsumed_by_one(self) -> None:
        pairs = find_subsumed_terms({"high flow", "high flow therapy", "high flow nasal cannula"})
        broader = {p[0] for p in pairs}
        narrower = {p[1] for p in pairs}
        assert broader == {"high flow"}
        assert narrower == {"high flow therapy", "high flow nasal cannula"}


class TestFindAndRedundancies:
    def test_basic(self) -> None:
        # "flow" is always satisfied when "high flow" is
        pairs = find_and_redundancies(parse('flow AND "high flow"'))
        assert ("flow", "high flow") in pairs

    def test_quoted_phrase_vs_quoted_phrase(self) -> None:
        pairs = find_and_redundancies(parse('"high flow" AND "high flow therapy"'))
        assert ("high flow", "high flow therapy") in pairs

    def test_no_redundancy(self) -> None:
        assert find_and_redundancies(parse("COPD AND NIV AND oxygen")) == []

    def test_nested_and(self) -> None:
        # redundancy inside a deeper AND
        pairs = find_and_redundancies(parse('COPD AND (flow AND "high flow")'))
        assert ("flow", "high flow") in pairs

    def test_or_boundary_respected(self) -> None:
        # "flow" and "high flow" are in different OR branches — NOT AND-connected
        pairs = find_and_redundancies(parse('flow OR "high flow"'))
        assert pairs == []

    def test_complex_nested(self) -> None:
        # (COPD OR AECOPD) AND (flow AND "high flow nasal") — redundancy inside inner AND
        expr = parse('(COPD OR AECOPD) AND (flow AND "high flow nasal")')
        pairs = find_and_redundancies(expr)
        assert ("flow", "high flow nasal") in pairs
        # COPD is not AND-connected to flow (separated by OR on the left)
        assert not any("copd" in p for p in pairs)

    def test_multi_word_phrases_no_false_positive(self) -> None:
        # "nasal cannula" and "high flow" share no subphrase relationship
        pairs = find_and_redundancies(parse('"nasal cannula" AND "high flow"'))
        assert pairs == []


class TestFindAbsorbedBranches:
    def test_basic_absorption(self) -> None:
        # "high flow" OR ("high flow therapy" AND COPD) — "high flow" absorbs the AND
        results = find_absorbed_branches(parse('"high flow" OR ("high flow therapy" AND COPD)'))
        assert len(results) == 1
        absorber, and_terms = results[0]
        assert absorber == "high flow"
        assert "high flow therapy" in and_terms

    def test_exact_term_match_absorbed(self) -> None:
        # COPD OR (COPD AND NIV) = COPD
        results = find_absorbed_branches(parse("COPD OR (COPD AND NIV)"))
        assert any(a == "copd" and "copd" in t for a, t in results)

    def test_no_absorption(self) -> None:
        # unrelated terms — no absorption
        assert find_absorbed_branches(parse("COPD OR (NIV AND oxygen)")) == []

    def test_nested_or_absorption(self) -> None:
        # (A OR B) OR (A AND C) — A should absorb at the top-level OR
        expr = parse("COPD OR AECOPD OR (COPD AND NIV)")
        results = find_absorbed_branches(expr)
        assert any(a == "copd" for a, _ in results)

    def test_complex_quoted_absorption(self) -> None:
        # "high flow" absorbs ("high flow nasal" AND "high flow therapy")
        # because "high flow" is subphrase of both terms in the AND
        expr = parse('"high flow" OR ("high flow nasal" AND "high flow therapy")')
        results = find_absorbed_branches(expr)
        assert any(a == "high flow" for a, _ in results)

    def test_partial_subsumption_sufficient(self) -> None:
        # T only needs to subsume ONE term in the AND for the branch to be absorbed
        # "high flow" OR ("high flow therapy" AND "nasal cannula")
        # "high flow" ⊂ "high flow therapy" → AND branch absorbed
        expr = parse('"high flow" OR ("high flow therapy" AND "nasal cannula")')
        results = find_absorbed_branches(expr)
        assert any(a == "high flow" for a, _ in results)

    def test_no_false_positive_and_only(self) -> None:
        # Pure AND — no OR to absorb into
        assert find_absorbed_branches(parse('"high flow" AND "high flow therapy"')) == []


class TestFindDuplicateTerms:
    def test_simple_duplicate(self) -> None:
        assert "copd" in find_duplicate_terms(parse("COPD OR (COPD AND NIV)"))

    def test_quoted_duplicate(self) -> None:
        expr = parse('"high flow" OR ("high flow" AND COPD)')
        assert "high flow" in find_duplicate_terms(expr)

    def test_no_duplicate(self) -> None:
        assert find_duplicate_terms(parse("(COPD OR AECOPD) AND NIV")) == []

    def test_case_normalised(self) -> None:
        # COPD and copd should count as one repeated term
        assert "copd" in find_duplicate_terms(parse("COPD AND copd"))

    def test_deeply_nested_duplicate(self) -> None:
        expr = parse("((COPD OR NIV) AND (COPD OR oxygen))")
        assert "copd" in find_duplicate_terms(expr)

    def test_three_occurrences(self) -> None:
        expr = parse("COPD OR (COPD AND (COPD OR NIV))")
        dupes = find_duplicate_terms(expr)
        assert "copd" in dupes
        assert "niv" not in dupes


class TestFindSubsumedBranches:
    def test_bare_term_subsumes_and_branch(self) -> None:
        # "high flow" OR ("high flow therapy" AND COPD) — first branch subsumes second
        expr = parse('"high flow" OR ("high flow therapy" AND COPD)')
        results = find_subsumed_branches(expr)
        assert any({"high flow"} == s and {"high flow therapy", "copd"} == n for s, n in results)

    def test_and_branch_subsumes_and_branch(self) -> None:
        # (flow AND COPD) OR ("high flow" AND COPD) — first subsumes second
        expr = parse('(flow AND COPD) OR ("high flow" AND COPD)')
        results = find_subsumed_branches(expr)
        assert any({"flow", "copd"} == s and {"high flow", "copd"} == n for s, n in results)

    def test_extra_term_in_subsumed_still_subsumed(self) -> None:
        # ("high flow" AND COPD) OR ("high flow therapy" AND COPD AND NIV)
        # second branch has extra NIV but is still subsumed — any match of it satisfies the first
        expr = parse('("high flow" AND COPD) OR ("high flow therapy" AND COPD AND NIV)')
        results = find_subsumed_branches(expr)
        assert any({"high flow", "copd"} == s for s, _ in results)

    def test_no_subsumption_disjoint_terms(self) -> None:
        expr = parse("(COPD AND oxygen) OR (NIV AND BiPAP)")
        assert find_subsumed_branches(expr) == []

    def test_not_symmetric(self) -> None:
        # "high flow" subsumes "high flow therapy", not the other way round
        expr = parse('"high flow" OR "high flow therapy"')
        results = find_subsumed_branches(expr)
        subsuming = [s for s, _ in results]
        subsumed = [n for _, n in results]
        assert {"high flow"} in subsuming
        assert {"high flow therapy"} in subsumed
        assert not any(n == {"high flow"} for n in subsumed)

    def test_three_branches_transitive(self) -> None:
        # "flow" subsumes "high flow" subsumes "high flow therapy"
        expr = parse('flow OR "high flow" OR "high flow therapy"')
        results = find_subsumed_branches(expr)
        subsumed = {frozenset(n) for _, n in results}
        assert frozenset({"high flow"}) in subsumed
        assert frozenset({"high flow therapy"}) in subsumed

    def test_identical_branches_not_flagged(self) -> None:
        # identical branches are duplicates, not subsumptions
        expr = parse("COPD OR COPD")
        assert find_subsumed_branches(expr) == []


class TestCombineMultipleStrings:
    """Cross-string analysis: SS1, SS2, SS3 treated as a joint OR."""

    def test_combine_two(self) -> None:
        ss1 = parse("COPD AND NIV")
        ss2 = parse("COPD AND oxygen")
        expr = combine(ss1, ss2)
        # COPD appears in both — should be flagged as duplicate
        assert "copd" in find_duplicate_terms(expr)

    def test_combine_three(self) -> None:
        ss1 = parse('"high flow"')
        ss2 = parse('"high flow therapy" AND COPD')
        ss3 = parse("NIV AND COPD")
        expr = combine(ss1, ss2, ss3)
        # "high flow" subsumes "high flow therapy" across SS1 and SS2
        terms = collect_terms(ss1) | collect_terms(ss2) | collect_terms(ss3)
        assert ("high flow", "high flow therapy") in find_subsumed_terms(terms)
        # "high flow" OR ("high flow therapy" AND COPD) — SS1 absorbs SS2 branch
        assert any(a == "high flow" for a, _ in find_absorbed_branches(expr))
        # COPD appears in SS2 and SS3
        assert "copd" in find_duplicate_terms(expr)

    def test_cross_string_branch_subsumption(self) -> None:
        # SS2 is fully subsumed by SS1: "high flow" satisfies "flow", COPD=COPD
        ss1 = parse("flow AND COPD")
        ss2 = parse('"high flow" AND COPD')
        expr = combine(ss1, ss2)
        results = find_subsumed_branches(expr)
        assert any({"flow", "copd"} == s and {"high flow", "copd"} == n for s, n in results)

    def test_cross_string_no_false_and_redundancy(self) -> None:
        # find_and_redundancies should NOT flag cross-OR terms — they're not AND-connected
        ss1 = parse("flow AND COPD")
        ss2 = parse('"high flow" AND COPD')
        pairs = find_and_redundancies(combine(ss1, ss2))
        assert not any({"flow", "high flow"} == set(p) for p in pairs)

    def test_combine_single(self) -> None:
        ss = parse("COPD AND NIV")
        assert combine(ss) is ss


class TestSimplify:
    def test_or_subsumption_removed(self) -> None:
        # "high flow therapy" is subsumed — should be dropped
        result = unparse(simplify(parse('"high flow" OR "high flow therapy"')))
        assert result == '"high flow"'

    def test_and_redundancy_removed(self) -> None:
        # "flow" is broader than "high flow" — should be dropped from AND
        result = unparse(simplify(parse('flow AND "high flow" AND COPD')))
        assert "flow" not in result.split()  # bare "flow" gone
        assert "high flow" in result
        assert "COPD" in result or "copd" in result

    def test_multiple_or_branches_removed(self) -> None:
        expr = parse('"high flow" OR "high flow therapy" OR ("high flow nasal" AND COPD)')
        result = unparse(simplify(expr))
        assert result == '"high flow"'

    def test_no_change_when_clean(self) -> None:
        s = '(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)'
        assert unparse(simplify(parse(s))) == unparse(parse(s))

    def test_nested_and_within_or(self) -> None:
        # (flow AND COPD) OR ("high flow" AND COPD) — second branch subsumed
        result = unparse(simplify(parse('(flow AND COPD) OR ("high flow" AND COPD)')))
        assert "high flow" not in result
        assert "flow" in result
        assert "COPD" in result or "copd" in result


class TestLintAndSuggest:
    def test_lint_or_redundancy(self) -> None:
        issues = lint_string('"high flow" OR "high flow therapy"')
        assert any("OR redundancy" in i for i in issues)

    def test_lint_and_redundancy(self) -> None:
        issues = lint_string('flow AND "high flow" AND COPD')
        assert any("AND redundancy" in i for i in issues)

    def test_lint_duplicate(self) -> None:
        issues = lint_string("COPD OR (COPD AND NIV)")
        assert any("Duplicate" in i for i in issues)

    def test_lint_clean_string(self) -> None:
        assert lint_string("(COPD OR AECOPD) AND NIV") == []

    def test_suggest_returns_none_when_clean(self) -> None:
        assert suggest_simplification("COPD AND NIV") is None

    def test_suggest_returns_simpler_string(self) -> None:
        result = suggest_simplification('"high flow" OR "high flow therapy"')
        assert result == '"high flow"'

    def test_suggest_complex(self) -> None:
        result = suggest_simplification('"high flow" OR "high flow therapy" OR ("high flow nasal" AND COPD)')
        assert result == '"high flow"'


class TestCanonicalize:
    def test_or_branches_sorted(self) -> None:
        a = unparse(canonicalize(parse("COPD OR AECOPD")))
        b = unparse(canonicalize(parse("AECOPD OR COPD")))
        assert a == b

    def test_and_operands_sorted(self) -> None:
        a = unparse(canonicalize(parse("NIV AND COPD")))
        b = unparse(canonicalize(parse("COPD AND NIV")))
        assert a == b

    def test_nested_reorder(self) -> None:
        a = unparse(canonicalize(parse("(COPD OR AECOPD) AND (NIV OR BiPAP)")))
        b = unparse(canonicalize(parse("(AECOPD OR COPD) AND (BiPAP OR NIV)")))
        assert a == b

    def test_genuinely_different_strings_differ(self) -> None:
        a = unparse(canonicalize(parse("COPD AND NIV")))
        b = unparse(canonicalize(parse("COPD AND BiPAP")))
        assert a != b

    def test_deeply_nested_or_within_and(self) -> None:
        # ((A OR B) AND (C OR D)) vs ((B OR A) AND (D OR C))
        a = unparse(canonicalize(parse("(A OR B) AND (C OR D)")))
        b = unparse(canonicalize(parse("(B OR A) AND (D OR C)")))
        assert a == b

    def test_deeply_nested_and_within_or(self) -> None:
        # ((A AND B) OR (C AND D)) vs ((B AND A) OR (D AND C))
        a = unparse(canonicalize(parse("(A AND B) OR (C AND D)")))
        b = unparse(canonicalize(parse("(B AND A) OR (D AND C)")))
        assert a == b

    def test_three_levels_deep(self) -> None:
        # (((COPD OR AECOPD) AND NIV) OR (BiPAP AND (ILD OR IPF)))
        # vs reordered at every level
        a = unparse(canonicalize(parse("((COPD OR AECOPD) AND NIV) OR (BiPAP AND (ILD OR IPF))")))
        b = unparse(canonicalize(parse("(BiPAP AND (IPF OR ILD)) OR (NIV AND (AECOPD OR COPD))")))
        assert a == b

    def test_or_branch_order_independent_of_complexity(self) -> None:
        # Two complex AND branches in different OR order
        a = unparse(canonicalize(parse("(COPD AND NIV AND oxygen) OR (ILD AND BiPAP)")))
        b = unparse(canonicalize(parse("(ILD AND BiPAP) OR (oxygen AND COPD AND NIV)")))
        assert a == b

    def test_not_nodes_preserved(self) -> None:
        # NOT should not affect the canonical form of its siblings
        a = unparse(canonicalize(parse("(COPD OR AECOPD) AND NOT asthma")))
        b = unparse(canonicalize(parse("(AECOPD OR COPD) AND NOT asthma")))
        assert a == b

    def test_mixed_depth_reorder(self) -> None:
        # Reorder at depth 1 only — depth 2 unchanged; still equal
        a = unparse(canonicalize(parse("(A AND (B OR C)) OR (D AND (E OR F))")))
        b = unparse(canonicalize(parse("(D AND (F OR E)) OR (A AND (C OR B))")))
        assert a == b


class TestFormatStringDiff:
    def test_reordered_or_returns_none(self) -> None:
        assert format_string_diff("COPD OR AECOPD", "AECOPD OR COPD") is None

    def test_reordered_and_returns_none(self) -> None:
        assert format_string_diff("COPD AND NIV", "NIV AND COPD") is None

    def test_reordered_nested_returns_none(self) -> None:
        assert (
            format_string_diff(
                "(COPD OR AECOPD) AND (NIV OR BiPAP)",
                "(AECOPD OR COPD) AND (BiPAP OR NIV)",
            )
            is None
        )

    def test_genuine_addition_not_none(self) -> None:
        assert format_string_diff("COPD AND NIV", "COPD AND NIV AND BiPAP") is not None

    def test_genuine_removal_not_none(self) -> None:
        assert format_string_diff("COPD AND NIV", "COPD") is not None

    def test_or_collapse_shows_removed_term_not_whole_branch(self) -> None:
        # (COPD OR AECOPD) → COPD: AECOPD removed, COPD retained — not a wholesale replacement
        pair = format_string_diff(
            "(COPD OR AECOPD) AND (NIV OR BiPAP)",
            "COPD AND (NIV OR BiPAP)",
        )
        assert pair is not None
        was, now = pair
        assert "\033[31m" in was  # something is red
        assert "AECOPD" in was  # AECOPD flagged
        assert "COPD" in now  # COPD present in result
        # COPD should not itself be coloured green (it wasn't added)
        assert "\033[32mCOPD\033[0m" not in now

    def test_or_expansion_shows_added_term_not_whole_branch(self) -> None:
        # COPD → (COPD OR AECOPD): AECOPD added, COPD retained
        pair = format_string_diff(
            "COPD AND (NIV OR BiPAP)",
            "(COPD OR AECOPD) AND (NIV OR BiPAP)",
        )
        assert pair is not None
        was, now = pair
        assert "\033[32m" in now  # something is green
        assert "AECOPD" in now  # AECOPD flagged
        assert "\033[32mCOPD\033[0m" not in now  # COPD not falsely green


class TestFormatSimplificationDiff:
    def test_removed_branches_highlighted(self) -> None:
        diff = format_simplification_diff('"high flow" OR "high flow therapy"')
        assert diff is not None
        assert "\033[31m" in diff  # red escape present
        assert '"high flow therapy"' in diff  # removed term shown
        assert diff.startswith('"high flow"')  # kept term comes first, unstyled

    def test_none_when_no_change(self) -> None:
        assert format_simplification_diff("COPD AND NIV") is None

    def test_kept_branch_not_highlighted(self) -> None:
        diff = format_simplification_diff('"high flow" OR "high flow therapy" OR COPD')
        assert diff is not None
        # COPD is not subsumed by "high flow" — should not be in red
        reset = "\033[0m"
        red = "\033[31m"
        # find COPD segment — should not be preceded by red code
        assert f"{red}COPD{reset}" not in diff and f"{red}copd{reset}" not in diff
