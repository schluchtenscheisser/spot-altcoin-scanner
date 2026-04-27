# Archived Legacy Daily Workflow

> **Note:** This file archives the legacy daily scanner workflow and is kept for historical reference only. It is not part of Independence v2.1 pre-production or production, and it must not be moved back into `.github/workflows/` without an explicit architecture decision.

```yaml
name: Daily Scanner Run

on:
  schedule:
    # Runs daily at 6:00 AM UTC
    # - cron: '10 4 * * *'
  workflow_dispatch: # Allows manual trigger

permissions:
  contents: write
  
jobs:
  scan:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v5
    
    - name: Set up Python
      uses: actions/setup-python@v6
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run scanner
      env:
        CMC_API_KEY: ${{ secrets.CMC_API_KEY }}
        RAW_SNAPSHOT_BASEDIR: snapshots/raw
        RAW_SNAPSHOT_CSV_GZIP: "1"
      run: |
        python -m scanner.main --mode standard
    
    - name: Commit and push reports
      run: |
        git config --local user.email "github-actions[bot]@users.noreply.github.com"
        git config --local user.name "github-actions[bot]"
        git add reports/ snapshots/
        git diff --quiet && git diff --staged --quiet || git commit -m "Daily scan: $(date +'%Y-%m-%d')"
        git push
```
