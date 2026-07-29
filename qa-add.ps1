function qa-add {
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Files
    )
    
    if ($Files.Count -eq 0) {
        Write-Host "Usage: qa-add <files>" -ForegroundColor Yellow
        Write-Host "  qa-add ."          -ForegroundColor Gray
        Write-Host "  qa-add file1.py"   -ForegroundColor Gray
        Write-Host "  qa-add -A"         -ForegroundColor Gray
        return
    }
    
    $REPO_ROOT = (Get-Location).Path
    
    # Find code_scanner.py - check current dir first, then bitbucket-qa/
    $scanner = $null
    if (Test-Path "code_scanner.py") {
        $scanner = "code_scanner.py"
    } elseif (Test-Path "bitbucket-qa\code_scanner.py") {
        $scanner = "bitbucket-qa\code_scanner.py"
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Pre-Add Quality Check" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    $errors = 0
    
    # STEP 1: Syntax check
    Write-Host ">>> 1/3 Syntax check..." -ForegroundColor White
    
    $pyFiles = @()
    foreach ($f in $Files) {
        if ($f -eq "." -or $f -eq "-A" -or $f -eq "--all") {
            $staged = git diff --cached --name-only --diff-filter=ACM -- "*.py" 2>$null
            if ($staged) { $pyFiles += $staged }
            $untracked = git ls-files --others --exclude-standard -- "*.py" 2>$null
            if ($untracked) { $pyFiles += $untracked }
        } elseif ($f -like "*.py") {
            $pyFiles += $f
        }
    }
    $pyFiles = $pyFiles | Select-Object -Unique
    
    if ($pyFiles.Count -eq 0) {
        Write-Host "  No .py files — skipping syntax check." -ForegroundColor Gray
    } else {
        foreach ($f in $pyFiles) {
            if (Test-Path $f) {
                $escaped = $f.Replace("'", "''").Replace('"', '""').Replace('`', '``')
                $result = & python -c "import py_compile; py_compile.compile(r'$escaped', doraise=True)" 2>&1
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "  SYNTAX ERROR: $f" -ForegroundColor Red
                    $errors++
                }
            }
        }
        if ($errors -eq 0) {
            Write-Host "  All .py files pass syntax check." -ForegroundColor Green
        }
    }
    Write-Host ""
    
    # STEP 2: Code scanner
    Write-Host ">>> 2/3 Code scanner..." -ForegroundColor White
    
    if ($scanner) {
        $result = & python $scanner $REPO_ROOT 2>&1
        $result | ForEach-Object { Write-Host $_ }
        if ($result -match "RESULT: BLOCKED") {
            $errors++
        }
    } else {
        Write-Host "  code_scanner.py not found — skipping." -ForegroundColor Gray
    }
    Write-Host ""
    
    # STEP 3: Large file check
    Write-Host ">>> 3/3 Large file check (>1MB)..." -ForegroundColor White

    $codeExtensions = @(".py", ".js", ".ts", ".tsx", ".jsx", ".php", ".css", ".scss", ".html", ".yml", ".yaml", ".json", ".xml", ".md", ".txt", ".sh", ".bat", ".ps1")
    $largeFiles = @()
    foreach ($f in $Files) {
        if ($f -eq "." -or $f -eq "-A" -or $f -eq "--all") {
            $changed = git diff --name-only 2>$null
            $untracked = git ls-files --others --exclude-standard 2>$null
            $allFiles = @()
            if ($changed) { $allFiles += $changed }
            if ($untracked) { $allFiles += $untracked }
            foreach ($cf in $allFiles) {
                $ext = [System.IO.Path]::GetExtension($cf).ToLower()
                if ($codeExtensions -contains $ext -and (Test-Path $cf)) {
                    $size = (Get-Item $cf).Length
                    if ($size -gt 1MB) {
                        $largeFiles += "$cf ($([math]::Round($size/1MB, 1)) MB)"
                    }
                }
            }
        } elseif (Test-Path $f) {
            $ext = [System.IO.Path]::GetExtension($f).ToLower()
            if ($codeExtensions -contains $ext) {
                $size = (Get-Item $f).Length
                if ($size -gt 1MB) {
                    $largeFiles += "$f ($([math]::Round($size/1MB, 1)) MB)"
                }
            }
        }
    }
    
    if ($largeFiles.Count -gt 0) {
        Write-Host "  WARNING: Large files detected:" -ForegroundColor Yellow
        $largeFiles | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
    } else {
        Write-Host "  No large files detected." -ForegroundColor Green
    }
    Write-Host ""
    
    # RESULT
    if ($errors -gt 0) {
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "  ADD BLOCKED — Fix errors above first" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        return
    }
    
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Checks passed — running git add" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    & git add @Files
    Write-Host "Files staged successfully!" -ForegroundColor Green
}