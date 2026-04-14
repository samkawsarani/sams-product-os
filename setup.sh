#!/usr/bin/env bash
#
# Sams Product OS — Setup Script
# Creates workspace structure, seeds starter files, installs optional tooling.
#
# ┌─────────────────────────────────────────────────────────────────────────┐
# │ AGENT INSTRUCTIONS                                                      │
# │                                                                         │
# │ If you are an AI agent (e.g. Claude Code) reading this file:            │
# │ Do NOT execute this script as bash. Instead, walk through the           │
# │ setup interactively using your tools.                                   │
# │                                                                         │
# │ Follow these steps:                                                     │
# │                                                                         │
# │ 1. CREATE WORKSPACE STRUCTURE                                           │
# │    - Create knowledge/ subdirs: about-me, company-context,              │
# │      product-strategy, processes, product-analytics, references,        │
# │      voice-samples, decisions, people, opportunities                    │
# │    - Create tasks/ subdirs: _archived/                                  │
# │    - Create projects/ folder                                            │
# │    - Copy templates to their destinations (skip if file exists):        │
# │        templates/about-me-template.md  → knowledge/about-me/about-me.md│
# │        templates/company-overview-template.md                           │
# │                          → knowledge/company-context/company-overview.md│
# │        templates/goals-template.md     → GOALS.md                      │
# │        templates/backlog-template.md   → tasks/BACKLOG.md              │
# │        templates/active-template.md    → tasks/ACTIVE.md               │
# │                                                                         │
# │ 2. ASK THE USER THESE QUESTIONS ONE AT A TIME:                          │
# │    Q1: "What's your current role?"                                      │
# │        e.g. Product Manager, Senior Engineer, Founder, VP               │
# │    Q2: "What's your primary professional focus right now?"              │
# │        e.g. Launching a new product, scaling the team, hitting OKRs    │
# │    Q3: "What are your 2–4 goals this quarter?"                          │
# │        e.g. Ship mobile redesign, improve activation by 20%             │
# │                                                                         │
# │ 3. GENERATE GOALS.md                                                    │
# │    Use answers to populate GOALS.md using templates/goals-template.md  │
# │                                                                         │
# │ 4. SUMMARIZE                                                            │
# │    Tell the user what was created and suggest next steps:               │
# │    - Fill in knowledge/about-me/about-me.md with your background        │
# │    - Brain dump into tasks/BACKLOG.md                                   │
# │    - Run /process-backlog to triage                                     │
# └─────────────────────────────────────────────────────────────────────────┘
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Sams Product OS — Interactive Setup
# ─────────────────────────────────────────────────────────────────────────────

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# Plugin marketplace
MARKETPLACE_REPO="samkawsarani/sams-product-plugins"

# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

print_banner() {
  echo ""
  echo -e "${BOLD}╔══════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}║       SAMS PRODUCT OS — Setup        ║${RESET}"
  echo -e "${BOLD}╚══════════════════════════════════════╝${RESET}"
  echo ""
}

print_header() {
  echo ""
  echo -e "${BLUE}${BOLD}── $1 ──${RESET}"
  echo ""
}

print_success() {
  echo -e "  ${GREEN}✔${RESET} $1"
}

print_skip() {
  echo -e "  ${DIM}–${RESET} $1 ${DIM}(already exists)${RESET}"
}

print_warning() {
  echo -e "  ${YELLOW}!${RESET} $1"
}

print_error() {
  echo -e "  ${RED}✘${RESET} $1"
}

print_info() {
  echo -e "  ${DIM}$1${RESET}"
}

ask_yn() {
  local prompt="$1"
  local default="${2:-n}"
  local hint
  if [[ "$default" == "y" ]]; then
    hint="[Y/n]"
  else
    hint="[y/N]"
  fi
  while true; do
    echo -en "  ${BOLD}?${RESET} ${prompt} ${DIM}${hint}${RESET} "
    read -r answer
    answer="${answer:-$default}"
    case "$(printf '%s' "$answer" | tr '[:upper:]' '[:lower:]')" in
      y|yes) return 0 ;;
      n|no)  return 1 ;;
      *)     echo -e "  ${DIM}Please answer y or n${RESET}" ;;
    esac
  done
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Prerequisites
# ─────────────────────────────────────────────────────────────────────────────

step_prerequisites() {
  print_header "Step 1: Prerequisites"

  # Claude Code CLI
  if command -v claude &>/dev/null; then
    print_success "claude"
  else
    print_warning "claude not found — install from https://claude.ai/code"
  fi

  # Node.js / npm — needed for QMD search (optional)
  if command -v npm &>/dev/null; then
    print_success "npm (Node.js)"
  else
    print_warning "npm not found — install Node.js to enable QMD search: https://nodejs.org"
    print_info "QMD is optional — the agent falls back to file search without it"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: QMD Search Engine
# ─────────────────────────────────────────────────────────────────────────────

step_qmd() {
  print_header "Step 2: QMD Search Engine"

  if ! command -v npm &>/dev/null; then
    print_warning "npm not available — skipping QMD installation"
    print_info "Install Node.js first, then re-run setup"
    return
  fi

  # Install qmd
  if command -v qmd &>/dev/null; then
    print_skip "qmd"
  else
    echo -e "  ${DIM}Installing QMD...${RESET}"
    npm install -g @tobilu/qmd 2>&1 | while IFS= read -r line; do echo -e "  ${DIM}${line}${RESET}"; done
    if command -v qmd &>/dev/null; then
      print_success "QMD installed"
    else
      print_warning "Could not install QMD — try manually: ${GREEN}npm install -g @tobilu/qmd${RESET}"
      return
    fi
  fi

  # Install QMD skill for Claude
  echo -e "  ${DIM}Installing QMD skill for Claude...${RESET}"
  if qmd skill install --global --yes 2>&1 | while IFS= read -r line; do echo -e "  ${DIM}${line}${RESET}"; done; then
    print_success "QMD skill installed (global + Claude symlink)"
  else
    print_warning "Could not install QMD skill — try manually: ${GREEN}qmd skill install --global --yes${RESET}"
  fi

  # Set up collection for this project
  if qmd collection list 2>/dev/null | grep -q "product-os"; then
    print_skip "QMD collection 'product-os'"
  else
    echo -e "  ${DIM}Adding QMD collection for this project...${RESET}"
    if qmd collection add "$REPO_DIR" --name product-os 2>&1 | while IFS= read -r line; do echo -e "  ${DIM}${line}${RESET}"; done; then
      print_success "QMD collection 'product-os' added"
      qmd context add qmd://product-os "Personal PM operating system — tasks, projects, knowledge base, meetings, and references" 2>/dev/null
      print_success "QMD collection context added"
    else
      print_warning "Could not add QMD collection — try manually:"
      echo -e "     ${GREEN}qmd collection add . --name product-os${RESET}"
    fi
  fi

  # Offer to run embeddings
  echo ""
  echo -e "  QMD can generate vector embeddings for semantic search."
  echo -e "  ${DIM}This may take a few minutes depending on your knowledge base size.${RESET}"
  if ask_yn "Run qmd embed now?" "n"; then
    echo -e "  ${DIM}Generating embeddings...${RESET}"
    qmd embed 2>&1 | while IFS= read -r line; do echo -e "  ${DIM}${line}${RESET}"; done
    print_success "QMD embeddings generated"
  else
    print_info "Skipped — run 'qmd embed' anytime to enable semantic search"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Knowledge Base Directories
# ─────────────────────────────────────────────────────────────────────────────

step_knowledge_dirs() {
  print_header "Step 3: Knowledge Base Directories"

  local dirs=(
    about-me
    company-context
    product-strategy
    processes
    product-analytics
    references
    voice-samples
    decisions
    people
    opportunities
  )

  for dir in "${dirs[@]}"; do
    local path="$REPO_DIR/knowledge/$dir"
    if [[ -d "$path" ]]; then
      print_skip "knowledge/$dir/"
    else
      mkdir -p "$path"
      print_success "Created knowledge/$dir/"
    fi
  done
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Template Files
# ─────────────────────────────────────────────────────────────────────────────

copy_template() {
  local source="$1"
  local target="$2"
  local label="$3"

  if [[ -f "$REPO_DIR/$target" ]]; then
    print_skip "$label"
  else
    local target_dir
    target_dir="$(dirname "$REPO_DIR/$target")"
    mkdir -p "$target_dir"
    cp "$REPO_DIR/$source" "$REPO_DIR/$target"
    print_success "Created $label"
  fi
}

step_template_files() {
  print_header "Step 4: Template Files"

  copy_template \
    "templates/about-me-template.md" \
    "knowledge/about-me/about-me.md" \
    "knowledge/about-me/about-me.md"

  copy_template \
    "templates/company-overview-template.md" \
    "knowledge/company-context/company-overview.md" \
    "knowledge/company-context/company-overview.md"

  copy_template \
    "templates/goals-template.md" \
    "GOALS.md" \
    "GOALS.md"

  copy_template \
    "templates/backlog-template.md" \
    "tasks/BACKLOG.md" \
    "tasks/BACKLOG.md"

  copy_template \
    "templates/active-template.md" \
    "tasks/ACTIVE.md" \
    "tasks/ACTIVE.md"

  # projects/ — committed discrete work
  mkdir -p "$REPO_DIR/projects"
  print_success "Created projects/"

  # tasks/_archived/ — monthly retrospective logs
  mkdir -p "$REPO_DIR/tasks/_archived"
  print_success "Created tasks/_archived/"

  # knowledge/INDEX.md — personal directory of knowledge folder contents
  if [[ -f "$REPO_DIR/knowledge/INDEX.md" ]]; then
    print_skip "knowledge/INDEX.md"
  else
    cat > "$REPO_DIR/knowledge/INDEX.md" << 'INDEX_EOF'
# Knowledge Index

Personal directory of all context and learned knowledge.
Last updated: $(date +%Y-%m-%d)

---

## Reference Context
*Curated by you. Set up once, updated as things change.*

| Folder | Contents |
|--------|----------|
| `about-me/` | Role, background, working style, 360 feedback |
| `company-context/` | Company overview, product info, competitors, org structure |
| `processes/` | How the team works, sprint cadence, release flow |
| `product-analytics/` | KPIs, metrics definitions, performance data |
| `product-strategy/` | Current strategy, vision, roadmap |
| `references/` | Articles, open requests, research docs |
| `voice-samples/` | Writing samples for AI voice matching |
| `decisions/` | Decision log — one file per significant decision |
| `opportunities/` | Observed problems and ideas to explore — groomed feature requests, market signals, patterns |
| `people/` | *(Optional)* One file per person — direct reports, stakeholders, key peers |

---

## Domain Learning
*Agent-authored. Grows from real work over time. Each folder contains `knowledge.md`, `hypotheses.md`, `rules.md`.*

| Domain Folder | Created | Description |
|---------------|---------|-------------|
| *(none yet — rows added here automatically when domain folders are created)* | | |
INDEX_EOF
    print_success "Created knowledge/INDEX.md"
  fi

}

# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Skills / Plugin Marketplace (Optional)
# ─────────────────────────────────────────────────────────────────────────────

step_plugins() {
  print_header "Step 5: Skills / Plugin Marketplace (Optional)"

  local marketplace_installed=false
  local has_claude=false
  command -v claude &>/dev/null && has_claude=true

  # Offer marketplace only if Claude Code is present
  if [[ "$has_claude" == true ]]; then
    echo -e "  ${DIM}https://github.com/${MARKETPLACE_REPO}${RESET}"
    echo ""
    if ask_yn "Install the Sams Product Plugins marketplace for Claude Code?" "y"; then
      echo -e "  ${DIM}Adding marketplace...${RESET}"
      local add_out
      add_out="$(claude plugin marketplace add "$MARKETPLACE_REPO" 2>&1 || true)"
      if echo "$add_out" | grep -qi "already\|exists\|success\|added" 2>/dev/null || [[ -z "$add_out" ]]; then
        print_success "Plugin marketplace added"
      else
        echo "$add_out" | while IFS= read -r line; do echo -e "  ${DIM}${line}${RESET}"; done
        print_warning "Marketplace may not have been added — continuing anyway"
      fi
      marketplace_installed=true
    else
      print_info "Skipped — add later: claude plugin marketplace add ${MARKETPLACE_REPO}"
    fi
  fi

  echo ""
  echo -e "  We recommend these two skills to get started with Product OS:"
  echo ""
  echo -e "  ${BOLD}write-doc${RESET}   — Generates PRDs, specs, briefs, and decision docs"
  echo -e "  ${BOLD}write-comms${RESET} — Drafts status updates, announcements, and stakeholder emails"
  echo ""

  if ask_yn "Install write-doc and write-comms now?" "y"; then
    if [[ "$marketplace_installed" == true ]]; then
      for skill in write-doc write-comms; do
        echo -e "  ${DIM}Installing ${skill}...${RESET}"
        if claude plugin install "${skill}@sams-product-plugins" 2>&1 \
            | while IFS= read -r line; do echo -e "  ${DIM}${line}${RESET}"; done; then
          print_success "$skill installed"
        else
          print_warning "Could not install ${skill} — try: ${GREEN}claude plugin install ${skill}@sams-product-plugins${RESET}"
        fi
      done
    else
      echo -e "  ${DIM}Installing write-doc and write-comms via npx...${RESET}"
      if npx skills add "$MARKETPLACE_REPO" --skill write-doc write-comms --yes--global 2>&1 \
          | while IFS= read -r line; do echo -e "  ${DIM}${line}${RESET}"; done; then
        print_success "write-doc and write-comms installed"
      else
        print_warning "Could not install — try: ${GREEN}npx skills add ${MARKETPLACE_REPO} --skill write-doc write-comms${RESET}"
      fi
    fi
  else
    if [[ "$marketplace_installed" == true ]]; then
      print_info "Install later: claude plugin install write-doc@sams-product-plugins"
      print_info "Install later: claude plugin install write-comms@sams-product-plugins"
    else
      print_info "Install later: npx skills add ${MARKETPLACE_REPO} --skill write-doc write-comms"
    fi
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Verification
# ─────────────────────────────────────────────────────────────────────────────

step_verification() {
  print_header "Step 6: Verification"

  local pass=0
  local fail=0

  # Prerequisites
  echo -e "  ${BOLD}Prerequisites${RESET}"
  if command -v claude &>/dev/null; then
    print_success "claude CLI"
    ((pass++))
  else
    print_error "claude CLI not found"
    ((fail++))
  fi

  if command -v npm &>/dev/null; then
    print_success "npm"
    ((pass++))
  else
    print_error "npm not found — install Node.js"
    ((fail++))
  fi

  if command -v qmd &>/dev/null; then
    print_success "qmd"
    ((pass++))
  else
    print_warning "qmd not found (optional) — run: npm install -g @tobilu/qmd"
  fi

  # Knowledge base
  echo ""
  echo -e "  ${BOLD}Knowledge Base${RESET}"
  local dir_count
  dir_count=$(find "$REPO_DIR/knowledge" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$dir_count" -ge 10 ]]; then
    print_success "knowledge/ subdirectories ($dir_count dirs)"
    ((pass++))
  else
    print_error "knowledge/ subdirectories (found $dir_count, expected 10)"
    ((fail++))
  fi

  # Template files
  echo ""
  echo -e "  ${BOLD}Template Files${RESET}"
  local templates=(
    "knowledge/INDEX.md"
    "knowledge/about-me/about-me.md"
    "knowledge/company-context/company-overview.md"
    "GOALS.md"
    "tasks/BACKLOG.md"
    "tasks/ACTIVE.md"
  )
  for tmpl in "${templates[@]}"; do
    if [[ -f "$REPO_DIR/$tmpl" ]]; then
      print_success "$tmpl"
      ((pass++))
    else
      print_error "$tmpl — missing"
      ((fail++))
    fi
  done

  # AI config
  echo ""
  echo -e "  ${BOLD}AI Configuration${RESET}"
  if [[ -d "$REPO_DIR/.claude/skills" ]]; then
    print_success ".claude/skills/ directory"
    ((pass++))
  else
    print_error ".claude/skills/ directory missing"
    ((fail++))
  fi

  # Summary
  echo ""
  echo -e "  ──────────────────────────────"
  echo -e "  ${GREEN}${pass} passed${RESET}  ${fail:+${RED}${fail} failed${RESET}}"
  if [[ "$fail" -gt 0 ]]; then
    echo -e "  ${DIM}Fix the items above, then re-run ./setup.sh to verify${RESET}"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Next Steps
# ─────────────────────────────────────────────────────────────────────────────

print_next_steps() {
  print_header "Setup Complete — Next Steps"

  echo -e "  ${BOLD}1.${RESET} Delete any ${DIM}.gitkeep${RESET} files — they're placeholders, not needed once you add real content"
  echo ""
  echo -e "  ${BOLD}2.${RESET} Fill in your context files ${DIM}(15-20 min)${RESET}"
  echo -e "     - knowledge/about-me/about-me.md"
  echo -e "     - knowledge/company-context/company-overview.md"
  echo ""
  echo -e "  ${BOLD}3.${RESET} Define your quarterly goals in GOALS.md"
  echo ""
  echo -e "  ${BOLD}4.${RESET} Start brain-dumping to tasks/BACKLOG.md"
  echo ""
  echo -e "  ${BOLD}5.${RESET} Say ${GREEN}/process-backlog${RESET} when you're ready to organize"
  echo ""
  echo -e "  ${BOLD}6.${RESET} Add more skills anytime:"
  echo -e "     Via marketplace:  ${GREEN}claude plugin install <name>@sams-product-plugins${RESET}"
  echo -e "     Via npx:          ${GREEN}npx skills add ${MARKETPLACE_REPO} --skill <name>${RESET}"
  echo -e "     Install all:      ${GREEN}npx skills add ${MARKETPLACE_REPO}${RESET}"
  echo ""
  echo -e "  ${DIM}See README.md for full usage guide${RESET}"
  echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

main() {
  print_banner
  step_prerequisites
  step_qmd
  step_knowledge_dirs
  step_template_files
  step_plugins
  step_verification
  print_next_steps
}

main "$@"
