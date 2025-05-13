# В начале commit.ps1
param(
    [string]$Message
)

if (-not $Message) {
    # Если при запуске не передали параметр, запрашиваем у пользователя
    $Message = Read-Host 'Enter commit message'
}

# Теперь используем $Message в Git-команде
git add .
git commit -m $Message
git push
