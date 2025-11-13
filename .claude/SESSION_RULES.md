# SESSION RULES - READ FIRST

**⚠️ CRITICAL: These rules MUST be followed in EVERY session and EVERY prompt.**

## 🔴 TDD ENFORCEMENT RULES

### Rule 1: Tests Before Code (MANDATORY)
```
❌ FORBIDDEN: Writing implementation code before tests exist
✅ REQUIRED: Tests must be written first and failing before any implementation
```

### Rule 2: Verification Protocol
Before writing ANY implementation code, Claude MUST:
1. ✅ Verify test file exists
2. ✅ Show test code that will be satisfied
3. ✅ Run test and confirm it FAILS (RED state)
4. ✅ Only then write minimum implementation
5. ✅ Run test again and confirm it PASSES (GREEN state)

### Rule 3: No Shortcuts
```
❌ FORBIDDEN: "Let me implement this function..."
❌ FORBIDDEN: "Here's the implementation..."
❌ FORBIDDEN: Skipping tests for "simple" functions

✅ REQUIRED: "Let me write the test first..."
✅ REQUIRED: "Here's the failing test..."
✅ REQUIRED: Every function has tests, no exceptions
```

### Rule 4: Spec is Law
- All function signatures MUST match `docs/TDD_SPEC.md`
- All test cases in TDD_SPEC.md MUST be implemented
- No deviations without explicit user approval

### Rule 5: User Accountability
**User: You MUST challenge me if I:**
- Skip the TDD cycle
- Write implementation before tests
- Don't verify RED → GREEN states
- Deviate from TDD_SPEC.md

**Stop me immediately and say:**
> "⚠️ TDD VIOLATION: Tests must be written first. Shall I write the test for [function_name] before implementing?"

---

## 📋 Mandatory Checklist Per Function

Copy this checklist for EVERY function:

```
Function: _______________________

[ ] 1. Read specification from TDD_SPEC.md
[ ] 2. Create/open test file
[ ] 3. Write test case(s) from spec
[ ] 4. Run test → Verify FAILS (RED)
[ ] 5. Write minimum implementation
[ ] 6. Run test → Verify PASSES (GREEN)
[ ] 7. Refactor if needed (keep GREEN)
[ ] 8. Commit test + implementation together
```

**Never skip a checkbox.**

---

## 🚫 Violation Examples

### ❌ WRONG:
```
User: "Implement calculate_dau"
Claude: "Here's the implementation..."  ← VIOLATION!
```

### ✅ CORRECT:
```
User: "Implement calculate_dau"
Claude: "Let me start by writing the test first. According to TDD_SPEC.md,
test_calculate_dau_basic should verify..."
[writes test]
[runs test - shows RED]
"Now that we have a failing test, I'll implement the function..."
```

---

## 🔄 Session Start Protocol

At the START of EVERY session, Claude MUST:
1. Read this file: `.claude/SESSION_RULES.md`
2. Read: `docs/TDD_SPEC.md` (at least scan structure)
3. Ask: "Are we following strict TDD? What function should I start with?"
4. Verify: If code exists, check that tests exist first

---

## 📞 User Commands

**If I violate TDD:**
- User says: `"TDD CHECK"` → I must show proof of test-first approach
- User says: `"RED GREEN"` → I must show the failing test, then passing test
- User says: `"SPEC CHECK"` → I must verify against TDD_SPEC.md

---

## 💡 Quick Reference

**The TDD mantra:**
```
RED (failing test) → GREEN (passing test) → REFACTOR (improve code)
```

**Never:**
- Write functions without tests
- Skip the RED state
- Deviate from TDD_SPEC.md

**Always:**
- Test first, code second
- Show the test failing before implementing
- Reference TDD_SPEC.md for requirements

---

**This document is the contract. Following it ensures TDD consistency across all sessions.**

Last Updated: 2025-11-13
Version: 1.0
