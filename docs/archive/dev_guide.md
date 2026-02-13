# Developer Guide
Version: v1.0  
Language: English  
Audience: Developer + GPT

---
## Working with AI Assistants

This project is developed with AI assistance. This guide documents the workflow.

---

## Developer Profile

**Background:**
- Not a professional developer
- Limited coding knowledge
- Works in GitHub Web Interface + Codespaces
- Needs complete, copy-paste-ready solutions

**Development Environment:**
- GitHub Web for file editing
- Codespaces for testing
- Terminal commands via Codespace terminal

---

## Standard Workflow

### 1. Code Implementation

**AI provides:**
- ✅ Complete file content (not snippets)
- ✅ Exact file path (e.g., `scanner/clients/mexc_client.py`)
- ✅ Clear instructions: "Open file X, REPLACE entire content with:"
- ✅ No partial edits unless explicitly requested

**For changes/updates:**
- ✅ "FIND this block: `[exact code]`"
- ✅ "REPLACE with: `[new code]`"
- ✅ Line numbers as reference (ca. line X)

---

### 2. Testing

**AI provides:**
- ✅ Complete test file (e.g., `test_mexc.py`)
- ✅ Where to save it (repo root)
- ✅ Single-line terminal command with `&&` chains

**Example:**
```bash
git pull origin main && python test_mexc.py
```

**NOT multiple separate commands** (error-prone)

---

### 3. Cleanup

**After successful test:**

Single command to:
- Remove test file
- Stage changes
- Commit
- Push

**Example:**
```bash
rm test_mexc.py && git add -A && git commit -m "Phase X complete" && git push origin main
```

---

### 4. Terminal Commands

**Always provide:**
- ✅ Complete commands (copy-paste ready)
- ✅ Chained with `&&` for efficiency
- ✅ No multi-step manual sequences

**Avoid:**
- ❌ "Run command A, then command B, then C"
- ❌ Multi-line Python in terminal (use test files)

---

## File Organization Rules

### New Files
- Implementation: Direct path (e.g., `scanner/clients/new_file.py`)
- Tests: Repo root (e.g., `test_feature.py`)
- Docs: `docs/` folder

### Editing Files
- Always: "Open X, REPLACE entire content" (clearest)
- For small changes: "FIND line X, REPLACE with Y"

---

## Communication Style

### AI should:
- ✅ Give complete, working code
- ✅ Provide exact file paths
- ✅ Use `&&` command chains
- ✅ Create test files for validation
- ✅ Explain WHAT is being done (briefly)
- ✅ Avoid unnecessary prose

### AI should NOT:
- ❌ Provide partial code snippets
- ❌ Say "add this somewhere in the file"
- ❌ Give multi-step manual instructions
- ❌ Assume developer knowledge

---

## Information Gathering

### Before implementing:
- ✅ **Ask for existing code/structure** if needed
- ✅ Request relevant files (e.g., "Can you upload sample_file.py?")
- ✅ Ask about repo structure/dependencies
- ✅ Verify assumptions with developer

### AI should NOT:
- ❌ Guess implementation details from other modules
- ❌ Assume function signatures without seeing code
- ❌ Trial-and-error when info is available
- ❌ Invent structure - ask the developer

**Principle:** Developer has the information. Ask first, implement second.

**Example:**
```
"Before I implement the filter, I need to see:
1. sample_file.py (upload please)
2. How your data structure looks in pipeline.py
3. How your repo structure looks like (use Output from tree -L 3)

This ensures the code works on first try."
```

---

## Error Handling

**If something fails:**

1. Show complete error output
2. AI analyzes and provides fix
3. Fix is again: complete code + exact location
4. Test again

**No guessing, no trial-and-error**

---

## Git Workflow

**Currently:**
- Direct commits to `main`
- Clean, descriptive commit messages
- Format: `"Phase X: Feature description"`

**PR Validation:**
- Pull requests to `main` are validated by GitHub Actions workflow `.github/workflows/pr-ci.yml`
- Required CI gate: `pytest -q`
- Recommended branch rule: require status checks and up-to-date branches before merge

**Future:**
- Feature branches (after Phase 4)
- Will be documented when activated

---

## Session Handoff

**Between sessions / AI instances:**

1. **GPT Snapshot** in `snapshots/gpt/`
   - Contains: Status, next steps, context
   - Updated at session end

2. **Key files to reference:**
   - `snapshots/gpt/gpt_snapshot_YYYY-MM-DD.md` (latest)
   - `docs/spec.md` (master spec)
   - `docs/pipeline.md` (architecture)
   - `README.md` (project overview)

3. **First message in new session:**
```
   I'm working on spot-altcoin-scanner (GitHub: schluchtenscheisser/spot-altcoin-scanner).
   
   Please read:
   - snapshots/gpt/gpt_snapshot_YYYY-MM-DD.md (upload if needed)
   - docs/spec.md (upload if needed)
   - docs/dev_guide.md (this file)
   
   Then continue with Phase X.
   
   Remember: I'm not a developer. Provide complete code + && command chains.
```

---

## Examples

### Good: Complete Implementation
```
Create scanner/pipeline/filters.py

Content:
[complete 200 lines of code]

Then test:
python test_filters.py

Cleanup:
rm test_filters.py && git add -A && git commit -m "Phase 4.1: Filters" && git push origin main
```

### Bad: Partial Instructions
```
Add this function to filters.py somewhere:
def filter_midcaps():
    # your code here
```
(Missing: where exactly? complete context? how to test?)

---

## Tools & Technologies

- **Language:** Python 3.11+
- **Development:** GitHub Web + Codespaces
- **Testing:** Command-line execution
- **Dependencies:** See `requirements.txt`
- **APIs:** MEXC (free), CoinMarketCap (free tier)

---

## End of `dev_guide.md`
