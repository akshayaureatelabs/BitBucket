# qa-add profile loader
# Add this to your PowerShell profile to use qa-add function
#
# To load permanently:
#   . "<path-to-bitbucket-qa>/load-qa-add.ps1"
#
# Or add to PowerShell profile:
#   notepad $PROFILE
#   Add: . "<path-to-bitbucket-qa>/load-qa-add.ps1"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
. "$ScriptDir\qa-add.ps1"
Write-Host "qa-add function loaded! Usage: qa-add ." -ForegroundColor Green
