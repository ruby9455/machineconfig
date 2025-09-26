# gotch1: make sure we are in the right directory: repo root. Solution: check if .pyproject.toml exists, otherwise stop.
if (!(Test-Path "./pyproject.toml")) {
    Write-Host "Error: pyproject.toml not found in the current directory. Please run this script from the root of a Python project." -ForegroundColor Red
    exit 1
}

# Color definitions (using ANSI escape sequences for cross-platform compatibility)
$RED = "`e[0;31m"
$GREEN = "`e[0;32m"
$YELLOW = "`e[1;33m"
$BLUE = "`e[0;34m"
$PURPLE = "`e[0;35m"
$CYAN = "`e[0;36m"
$WHITE = "`e[1;37m"
$BOLD = "`e[1m"
$UNDERLINE = "`e[4m"
$NC = "`e[0m" # No Color

# Box drawing functions
function Draw-Box {
    param([string]$text, [string]$color)
    $width = 60
    $padding = [math]::Floor(($width - $text.Length) / 2)
    $line = "─" * $width

    Write-Host "${color}┌${line}┐${NC}"
    Write-Host ("${color}│" + (" " * $padding) + $text + (" " * $padding) + "│${NC}")
    Write-Host "${color}└${line}┘${NC}"
}

function Draw-Progress {
    param([int]$current, [int]$total, [string]$description)
    Write-Host "${CYAN}┌────────────────────────────────────────────────────────────┐${NC}"
    $padding = 50 - $description.Length - 8
    Write-Host ("${CYAN}│${NC} ${BOLD}${WHITE}Step ${current}/${total}:${NC} ${description}" + (" " * $padding) + "${CYAN}│${NC}")
    Write-Host "${CYAN}└────────────────────────────────────────────────────────────┘${NC}"
}

$TOTAL_STEPS = 7
$CURRENT_STEP = 0

Draw-Box "🚀 LINTING & TYPE CHECKING SUITE 🚀" "${BOLD}${CYAN}"
Write-Host

$CURRENT_STEP++
Draw-Progress $CURRENT_STEP $TOTAL_STEPS "Environment Setup"
Write-Host "${BLUE}🔧 Installing and updating development dependencies...${NC}"
# uv add pylint pyright mypy pyrefly ruff ty --dev  # linters and type checkers
# uv add --dev cleanpy pylint pyright mypy pyrefly --upgrade-package cleanpy pylint pyright mypy pyrefly
uv add --dev pyright --upgrade-package pyright
uv add --dev pylint --upgrade-package pylint
uv add --dev mypy --upgrade-package mypy
uv add --dev pyrefly --upgrade-package pyrefly
uv add --dev cleanpy --upgrade-package cleanpy

uv add types-requests types-toml types-PyYAML types-pytz types-paramiko types-urllib3 --dev
uv add types-mysqlclient types-SQLAlchemy --dev

Write-Host "${GREEN}✅ Environment setup complete!${NC}"
Write-Host

$CURRENT_STEP++
Draw-Progress $CURRENT_STEP $TOTAL_STEPS "Code Cleanup"
Write-Host "${YELLOW}🧹 Cleaning and formatting code...${NC}"
uv run -m cleanpy .
uv run -m ruff clean
# uv run -m ruff format .
uv run -m ruff check . --fix
uv run --no-dev --project $HOME/code/machineconfig -m machineconfig.scripts.python.ai.generate_files

New-Item -ItemType Directory -Force -Path .linters | Out-Null

Write-Host "${GREEN}🧹 Code cleanup complete!${NC}"
Write-Host

Draw-Box "🔍 TYPE CHECKERS & LINTERS 🔍" "${BOLD}${PURPLE}"

$CURRENT_STEP++
Draw-Progress $CURRENT_STEP $TOTAL_STEPS "Pyright Type Checker"
Write-Host "${BLUE}📋 Analyzing types with Pyright...${NC}"
Remove-Item ./.linters/pyright_result.md -ErrorAction SilentlyContinue
uv run pyright . | Out-File -FilePath ./.linters/pyright_result.md
Write-Host "${GREEN}✅ Results saved to ${UNDERLINE}./.linters/pyright_result.md${NC}"

$CURRENT_STEP++
Draw-Progress $CURRENT_STEP $TOTAL_STEPS "MyPy Type Checker"
Write-Host "${BLUE}📋 Analyzing types with MyPy...${NC}"
Remove-Item ./.linters/mypy_result.md -ErrorAction SilentlyContinue
uv run mypy . | Out-File -FilePath ./.linters/mypy_result.md
Write-Host "${GREEN}✅ Results saved to ${UNDERLINE}./.linters/mypy_result.md${NC}"

$CURRENT_STEP++
Draw-Progress $CURRENT_STEP $TOTAL_STEPS "Pylint Code Analysis"
Write-Host "${BLUE}📋 Analyzing code quality with Pylint...${NC}"
Remove-Item ./.linters/pylint_result.md -ErrorAction SilentlyContinue
uv run pylint ./src/ | Out-File -FilePath ./.linters/pylint_result.md
Write-Host "${GREEN}✅ Results saved to ${UNDERLINE}./.linters/pylint_result.md${NC}"

$CURRENT_STEP++
Draw-Progress $CURRENT_STEP $TOTAL_STEPS "Pyrefly Type Checker"
Write-Host "${BLUE}📋 Analyzing types with Pyrefly...${NC}"
Remove-Item ./.linters/pyrefly_result.md -ErrorAction SilentlyContinue
uv run pyrefly check . | Out-File -FilePath ./.linters/pyrefly_result.md
Write-Host "${GREEN}✅ Results saved to ${UNDERLINE}./.linters/pyrefly_result.md${NC}"

$CURRENT_STEP++
Draw-Progress $CURRENT_STEP $TOTAL_STEPS "Ruff Linter"
Write-Host "${BLUE}📋 Checking code style with Ruff...${NC}"
Remove-Item ./.linters/ruff_result.md -ErrorAction SilentlyContinue
uv run ruff check . | Out-File -FilePath ./.linters/ruff_result.md
Write-Host "${GREEN}✅ Results saved to ${UNDERLINE}./.linters/ruff_result.md${NC}"

Write-Host
Draw-Box "🎉 ALL CHECKS COMPLETED! 🎉" "${BOLD}${GREEN}"
Write-Host "${BOLD}${GREEN}📁 Check the ${UNDERLINE}.linters${NC}${BOLD}${GREEN} directory for detailed results.${NC}"