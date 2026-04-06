#!/usr/bin/env bash
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
# Step 1: Platform Check
# ─────────────────────────────────────────────────────────────────────────────

step_platform_check() {
  print_header "Step 1: Platform Check"

  local os
  os="$(uname -s)"

  if [[ "$os" == "Darwin" ]]; then
    IS_MACOS=true
    print_success "macOS detected — full automated setup available"
  else
    IS_MACOS=false
    print_warning "Non-macOS detected ($os) — some steps require manual installation"
    echo ""
    echo -e "  Install these tools manually before continuing:"
    echo -e "    ${BOLD}uv${RESET}   — https://docs.astral.sh/uv/"
    echo ""
    echo -e "  ${DIM}Press Enter to continue with the rest of setup...${RESET}"
    read -r
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Prerequisites
# ─────────────────────────────────────────────────────────────────────────────

step_prerequisites() {
  print_header "Step 2: Prerequisites"

  # Claude Code CLI
  if command -v claude &>/dev/null; then
    print_success "claude"
  else
    print_warning "claude not found — install Claude Code CLI to use this product OS or install plugins from the marketplace"
  fi

  if [[ "$IS_MACOS" == true ]]; then
    # Check Homebrew
    if ! command -v brew &>/dev/null; then
      print_error "Homebrew not found — install from https://brew.sh then re-run setup"
      exit 1
    fi
    print_success "Homebrew"

    # uv
    if command -v uv &>/dev/null; then
      print_skip "uv"
    else
      echo -e "  ${DIM}Installing uv...${RESET}"
      brew install uv
      print_success "uv installed"
    fi

    # npm / Node.js
    if command -v npm &>/dev/null; then
      print_skip "npm"
    else
      echo -e "  ${DIM}Installing Node.js (includes npm)...${RESET}"
      brew install node
      print_success "Node.js / npm installed"
    fi

  else
    # Non-macOS: just check what's available
    if command -v uv &>/dev/null; then
      print_success "uv"
    else
      print_warning "uv not found — install from https://docs.astral.sh/uv/"
    fi

    if command -v npm &>/dev/null; then
      print_success "npm"
    else
      print_warning "npm not found — install Node.js from https://nodejs.org"
    fi
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Python Dependencies
# ─────────────────────────────────────────────────────────────────────────────

step_python_deps() {
  print_header "Step 3: Python Dependencies"

  if ! command -v uv &>/dev/null; then
    print_warning "uv not available — skipping Python dependency install"
    print_info "Run 'uv sync' manually after installing uv"
    return
  fi

  cd "$REPO_DIR"
  echo -e "  ${DIM}Running uv sync...${RESET}"
  uv sync 2>&1 | while IFS= read -r line; do echo -e "  ${DIM}${line}${RESET}"; done
  print_success "Python dependencies installed"

  # Verify
  if uv run python -c "import mcp; import yaml" &>/dev/null; then
    print_success "Verified: mcp and pyyaml importable"
  else
    print_warning "Could not verify Python imports — check uv sync output"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: QMD Search Engine
# ─────────────────────────────────────────────────────────────────────────────

step_qmd() {
  print_header "Step 4: QMD Search Engine"

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
      qmd context add qmd://product-os "Personal PM operating system — tasks, initiatives, knowledge base, meetings, and references" 2>/dev/null
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
# Step 5: Knowledge Base Directories
# ─────────────────────────────────────────────────────────────────────────────

step_knowledge_dirs() {
  print_header "Step 5: Knowledge Base Directories"

  local dirs=(
    about-me
    company-context
    product-strategy
    frameworks
    processes
    product-analytics
    references
    voice-samples
    decisions
  )

  for dir in "${dirs[@]}"; do
    local path="$REPO_DIR/knowledge/$dir"
    if [[ -d "$path" ]]; then
      print_skip "knowledge/$dir/"
    else
      mkdir -p "$path"
      touch "$path/.gitkeep"
      print_success "Created knowledge/$dir/"
    fi
  done
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Template Files
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
  print_header "Step 6: Template Files"

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
| `frameworks/` | PM methodologies, mental models |
| `processes/` | How the team works, sprint cadence, release flow |
| `product-analytics/` | KPIs, metrics definitions, performance data |
| `product-strategy/` | Current strategy, vision, roadmap |
| `references/` | Articles, open requests, research docs |
| `voice-samples/` | Writing samples for AI voice matching |
| `decisions/` | Decision log — one file per significant decision |

---

## Domain Learning
*Agent-authored. Grows from real work over time. Each folder contains `knowledge.md`, `hypotheses.md`, `rules.md`.*

| Domain Folder | Created | Description |
|---------------|---------|-------------|
| *(none yet — rows added here automatically when domain folders are created)* | | |
INDEX_EOF
    print_success "Created knowledge/INDEX.md"
  fi

  # BACKLOG.md — small enough to create inline
  if [[ -f "$REPO_DIR/BACKLOG.md" ]]; then
    print_skip "BACKLOG.md"
  else
    cat > "$REPO_DIR/BACKLOG.md" << 'BACKLOG_EOF'
# Backlog

Your daily inbox for all notes, ideas, tasks, and thoughts. Capture everything here throughout the day.

Say `process my backlog` when you're ready to categorize and organize items into tasks, initiatives, or references.
BACKLOG_EOF
    print_success "Created BACKLOG.md"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 7: MCP Configuration
# ─────────────────────────────────────────────────────────────────────────────

PM_TASKS_JSON='{
    "pm-tasks": {
      "command": "uv",
      "args": ["run", "python", "tools/mcp-servers/task-manager/server.py"]
    }
  }'

PM_TASKS_MCP_FULL='{
  "mcpServers": {
    "pm-tasks": {
      "command": "uv",
      "args": ["run", "python", "tools/mcp-servers/task-manager/server.py"]
    }
  }
}'

step_mcp_config() {
  print_header "Step 7: MCP Configuration"

  local mcp_file="$REPO_DIR/.mcp.json"

  if [[ -f "$mcp_file" ]]; then
    if grep -q '"pm-tasks"' "$mcp_file" 2>/dev/null; then
      print_skip ".mcp.json (pm-tasks already configured)"
    else
      print_warning ".mcp.json exists but missing pm-tasks server"
      echo ""
      echo -e "  Add this to your .mcp.json under ${BOLD}mcpServers${RESET}:"
      echo ""
      echo -e "${DIM}$PM_TASKS_JSON${RESET}"
      echo ""
    fi
  else
    echo "$PM_TASKS_MCP_FULL" > "$mcp_file"
    print_success "Created .mcp.json with pm-tasks server"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 8: Cursor Setup (Optional)
# ─────────────────────────────────────────────────────────────────────────────

step_cursor_setup() {
  print_header "Step 8: Cursor Setup (Optional)"

  if ! ask_yn "Do you use Cursor?" "n"; then
    print_info "Skipping Cursor setup"
    return
  fi

  # Skills symlink — only needed if NOT using Claude Code,
  # since Cursor can read .claude/skills/ and plugins directly.
  local cursor_dir="$REPO_DIR/.cursor"
  mkdir -p "$cursor_dir"

  if command -v claude &>/dev/null; then
    print_info "Claude Code detected — skipping .cursor/skills symlink (Cursor reads .claude/skills/ directly)"
  elif [[ -L "$cursor_dir/skills" ]] || [[ -d "$cursor_dir/skills" ]]; then
    print_skip ".cursor/skills"
  else
    ln -s "../.claude/skills" "$cursor_dir/skills"
    print_success "Created .cursor/skills symlink"
  fi

  # Cursor MCP config
  local cursor_mcp="$cursor_dir/mcp.json"
  if [[ -f "$cursor_mcp" ]]; then
    if grep -q '"pm-tasks"' "$cursor_mcp" 2>/dev/null; then
      print_skip ".cursor/mcp.json (pm-tasks already configured)"
    else
      print_warning ".cursor/mcp.json exists but missing pm-tasks server"
      echo ""
      echo -e "  Add this to your .cursor/mcp.json under ${BOLD}mcpServers${RESET}:"
      echo ""
      echo -e "${DIM}$PM_TASKS_JSON${RESET}"
      echo ""
    fi
  else
    echo "$PM_TASKS_MCP_FULL" > "$cursor_mcp"
    print_success "Created .cursor/mcp.json with pm-tasks server"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 9: Plugin Marketplace (Optional)
# ─────────────────────────────────────────────────────────────────────────────

ask_scope() {
  echo ""
  echo -e "  Plugins can be installed at three scopes:"
  echo ""
  echo -e "    ${BOLD}user${RESET}    — Available across ALL your projects  (~/.claude/)"
  echo -e "    ${BOLD}project${RESET} — This project only, committed        (.claude/settings.json)"
  echo -e "    ${BOLD}local${RESET}   — This project only, not committed    (.claude/settings.local.json)"
  echo ""
  while true; do
    echo -en "  ${BOLD}?${RESET} Scope ${DIM}[user/project/local]${RESET} (default: user): "
    read -r _scope_answer
    _scope_answer="${_scope_answer:-user}"
    case "$(printf '%s' "$_scope_answer" | tr '[:upper:]' '[:lower:]')" in
      user|project|local) PLUGIN_SCOPE="$_scope_answer"; return ;;
      *) echo -e "  ${DIM}Please enter user, project, or local${RESET}" ;;
    esac
  done
}

build_plugin_list() {
  # Outputs tab-separated lines: name\tdescription, recommended first
  local raw
  raw="$(claude plugin list --available --json 2>/dev/null || true)"
  if [[ -z "$raw" ]]; then
    PLUGIN_LIST=()
    return
  fi
  # Parse JSON; put write-doc and write-comms first, rest sorted
  local all_lines recommended other
  all_lines="$(printf '%s' "$raw" | python3 -c "
import json, sys
data = json.load(sys.stdin)
plugins = data.get('available', [])
recommended = {'write-doc', 'write-comms'}
rec = [p for p in plugins if p['name'] in recommended]
other = [p for p in plugins if p['name'] not in recommended]
other.sort(key=lambda p: p['name'])
for p in rec + other:
    desc = p.get('description', '').replace('\t', ' ')
    print(p['name'] + '\t' + desc)
" 2>/dev/null || true)"
  if [[ -z "$all_lines" ]]; then
    PLUGIN_LIST=()
    return
  fi
  # Load into array
  PLUGIN_LIST=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && PLUGIN_LIST+=("$line")
  done <<< "$all_lines"
}

select_plugins_fzf() {
  # Takes plugin list as arguments (name\tdescription lines), returns selected names via stdout
  local -a entries=("$@")
  local fzf_input=""
  for entry in "${entries[@]}"; do
    local name desc star=""
    name="${entry%%	*}"
    desc="${entry#*	}"
    [[ "$name" == "write-doc" || "$name" == "write-comms" ]] && star=" ${YELLOW}★${RESET}"
    # For fzf we use plain text (no ANSI in the name field for easy parsing)
    if [[ "$name" == "write-doc" || "$name" == "write-comms" ]]; then
      fzf_input+="${name}  ★  ${desc}"$'\n'
    else
      fzf_input+="${name}     ${desc}"$'\n'
    fi
  done
  local selected
  selected="$(printf '%s' "$fzf_input" | fzf \
    --multi \
    --prompt="  Select plugins (TAB/SPACE toggles, ENTER confirms, ESC skips): " \
    --header="TAB/SPACE=toggle  ENTER=install selected  ESC=skip all  ★=recommended" \
    --no-info \
    2>/dev/null || true)"
  # Extract just the plugin name (first whitespace-delimited token)
  printf '%s' "$selected" | awk '{print $1}'
}

select_plugins_fallback() {
  # Takes plugin list as arguments (name\tdescription lines), returns selected names via stdout
  local -a entries=("$@")
  declare -A selected=()
  local names=()
  local descs=()
  for entry in "${entries[@]}"; do
    local name desc
    name="${entry%%	*}"
    desc="${entry#*	}"
    names+=("$name")
    descs+=("$desc")
    if [[ "$name" == "write-doc" || "$name" == "write-comms" ]]; then
      selected["$name"]=1
    fi
  done

  while true; do
    echo ""
    echo -e "  ${BOLD}Select plugins to install${RESET}  ${DIM}(number to toggle, d=done, s=skip all)${RESET}"
    echo ""
    local i=0
    for name in "${names[@]}"; do
      local check=" " star=""
      [[ "${selected[$name]:-0}" == "1" ]] && check="x"
      [[ "$name" == "write-doc" || "$name" == "write-comms" ]] && star=" ${YELLOW}★${RESET}"
      local desc="${descs[$i]}"
      # Truncate description to ~55 chars
      if [[ ${#desc} -gt 55 ]]; then
        desc="${desc:0:52}..."
      fi
      printf "    ${DIM}[%2d]${RESET} [${BOLD}%s${RESET}]${star} ${BOLD}%-20s${RESET} ${DIM}%s${RESET}\n" \
        "$((i+1))" "$check" "$name" "$desc"
      ((i++))
    done
    echo ""
    echo -en "  ${BOLD}>${RESET} "
    read -r choice
    case "$choice" in
      d|done)
        for name in "${names[@]}"; do
          [[ "${selected[$name]:-0}" == "1" ]] && echo "$name"
        done
        return ;;
      s|skip) return ;;
      ''|*[!0-9]*)
        echo -e "  ${DIM}Enter a number, d to confirm, or s to skip all${RESET}" ;;
      *)
        local idx=$((choice - 1))
        if [[ $idx -ge 0 && $idx -lt ${#names[@]} ]]; then
          local toggled="${names[$idx]}"
          if [[ "${selected[$toggled]:-0}" == "1" ]]; then
            unset "selected[$toggled]"
          else
            selected["$toggled"]=1
          fi
        else
          echo -e "  ${DIM}Number out of range${RESET}"
        fi ;;
    esac
  done
}

step_plugins() {
  print_header "Step 9: Plugin Marketplace (Optional)"

  if ! command -v claude &>/dev/null; then
    print_warning "Claude Code CLI not found — skipping plugin setup"
    print_info "Install Claude Code first, then run this setup again to install plugins"
    return
  fi

  echo -e "  The ${BOLD}Sams Product Plugins${RESET} marketplace adds skills like"
  echo -e "  analytics, grooming, research, writing, prototyping, and more."
  echo -e "  ${DIM}https://github.com/${MARKETPLACE_REPO}${RESET}"
  echo ""

  local marketplace_added=false
  if ask_yn "Add the plugin marketplace?" "y"; then
    echo -e "  ${DIM}Adding marketplace...${RESET}"
    if claude plugin marketplace add "$MARKETPLACE_REPO" 2>&1 | while IFS= read -r line; do echo -e "  ${DIM}${line}${RESET}"; done; then
      print_success "Plugin marketplace added"
      marketplace_added=true
    else
      print_warning "Could not add marketplace — you can add it later with:"
      echo -e "     ${GREEN}claude plugin marketplace add ${MARKETPLACE_REPO}${RESET}"
    fi
  else
    print_info "Skipped — add it anytime with:"
    echo -e "     ${GREEN}claude plugin marketplace add ${MARKETPLACE_REPO}${RESET}"
  fi

  # Plugin picker — only if marketplace was added successfully
  if [[ "$marketplace_added" == true ]]; then
    echo -e "  ${DIM}Fetching available plugins...${RESET}"
    PLUGIN_LIST=()
    build_plugin_list

    if [[ ${#PLUGIN_LIST[@]} -gt 0 ]]; then
      echo ""
      echo -e "  ${BOLD}${#PLUGIN_LIST[@]} plugins available.${RESET} Select which to install:"

      ask_scope

      local selected_names=()
      if command -v fzf &>/dev/null; then
        while IFS= read -r name; do
          [[ -n "$name" ]] && selected_names+=("$name")
        done < <(select_plugins_fzf "${PLUGIN_LIST[@]}")
      else
        while IFS= read -r name; do
          [[ -n "$name" ]] && selected_names+=("$name")
        done < <(select_plugins_fallback "${PLUGIN_LIST[@]}")
      fi

      if [[ ${#selected_names[@]} -gt 0 ]]; then
        echo ""
        local installed_plugins
        installed_plugins="$(claude plugin list 2>/dev/null || true)"
        for plugin in "${selected_names[@]}"; do
          if echo "$installed_plugins" | grep -q "$plugin" 2>/dev/null; then
            print_skip "$plugin (already installed)"
          else
            echo -e "  ${DIM}Installing ${plugin}...${RESET}"
            if claude plugin install "${plugin}@sams-product-plugins" -s "$PLUGIN_SCOPE" 2>&1 \
                | while IFS= read -r line; do echo -e "  ${DIM}${line}${RESET}"; done; then
              print_success "$plugin installed"
            else
              print_warning "Could not install ${plugin} — try manually:"
              echo -e "     ${GREEN}claude plugin install ${plugin}@sams-product-plugins -s ${PLUGIN_SCOPE}${RESET}"
            fi
          fi
        done
      else
        print_info "No plugins selected — install anytime with: ${GREEN}claude plugin install <name>@sams-product-plugins${RESET}"
      fi
    fi
  fi

  # Check which official plugins are already installed
  local installed_plugins
  installed_plugins="$(claude plugin list 2>/dev/null || true)"

  echo ""
  echo -e "  Claude also offers two official plugins that pair well with Product OS:"
  echo ""
  echo -e "  ${BOLD}skill-creator${RESET}"
  echo -e "  ${DIM}Create, modify, and test custom skills. Includes eval/benchmarking.${RESET}"
  echo ""
  echo -e "  ${BOLD}claude-md-management${RESET}"
  echo -e "  ${DIM}Audit, improve, and maintain CLAUDE.md files across your repos.${RESET}"
  echo ""

  if echo "$installed_plugins" | grep -q "skill-creator" 2>/dev/null; then
    print_skip "skill-creator (already installed)"
  elif ask_yn "Install skill-creator from Claude official plugins?" "y"; then
    echo -e "  ${DIM}Installing skill-creator...${RESET}"
    if claude plugin install skill-creator 2>&1 | while IFS= read -r line; do echo -e "  ${DIM}${line}${RESET}"; done; then
      print_success "skill-creator installed"
    else
      print_warning "Could not install — try manually: ${GREEN}claude plugin install skill-creator${RESET}"
    fi
  else
    print_info "Skipped"
  fi

  if echo "$installed_plugins" | grep -q "claude-md-management" 2>/dev/null; then
    print_skip "claude-md-management (already installed)"
  elif ask_yn "Install claude-md-management from Claude official plugins?" "y"; then
    echo -e "  ${DIM}Installing claude-md-management...${RESET}"
    if claude plugin install claude-md-management 2>&1 | while IFS= read -r line; do echo -e "  ${DIM}${line}${RESET}"; done; then
      print_success "claude-md-management installed"
    else
      print_warning "Could not install — try manually: ${GREEN}claude plugin install claude-md-management${RESET}"
    fi
  else
    print_info "Skipped"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 10: Verification
# ─────────────────────────────────────────────────────────────────────────────

step_verification() {
  print_header "Step 10: Verification"

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

  if command -v uv &>/dev/null; then
    print_success "uv installed"
    ((pass++))
  else
    print_error "uv not found"
    ((fail++))
  fi

  if command -v uv &>/dev/null && uv run python -c "import mcp; import yaml" &>/dev/null; then
    print_success "Python dependencies (mcp, pyyaml)"
    ((pass++))
  else
    print_error "Python dependencies — run: uv sync"
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
    print_error "qmd not found — run: npm install -g @tobilu/qmd"
    ((fail++))
  fi

  # Knowledge base
  echo ""
  echo -e "  ${BOLD}Knowledge Base${RESET}"
  local dir_count
  dir_count=$(find "$REPO_DIR/knowledge" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$dir_count" -ge 8 ]]; then
    print_success "knowledge/ subdirectories ($dir_count dirs)"
    ((pass++))
  else
    print_error "knowledge/ subdirectories (found $dir_count, expected 8)"
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
    "BACKLOG.md"
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

  if [[ -f "$REPO_DIR/.mcp.json" ]] && grep -q '"pm-tasks"' "$REPO_DIR/.mcp.json" 2>/dev/null; then
    print_success ".mcp.json with pm-tasks"
    ((pass++))
  else
    print_error ".mcp.json missing or pm-tasks not configured"
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

  echo -e "  ${BOLD}1.${RESET} Fill in your context files ${DIM}(15-20 min)${RESET}"
  echo -e "     - knowledge/about-me/about-me.md"
  echo -e "     - knowledge/company-context/company-overview.md"
  echo ""
  echo -e "  ${BOLD}2.${RESET} Define your quarterly goals in GOALS.md"
  echo ""
  echo -e "  ${BOLD}3.${RESET} Start brain-dumping to BACKLOG.md"
  echo ""
  echo -e "  ${BOLD}4.${RESET} Say ${GREEN}/process-backlog${RESET} when you're ready to organize"
  echo ""
  echo -e "  ${BOLD}5.${RESET} Browse & install plugins as needed ${DIM}(optional)${RESET}"
  echo -e "     ${DIM}https://github.com/${MARKETPLACE_REPO}${RESET}"
  echo -e "     ${GREEN}claude plugin install ${DIM}<plugin-name>${RESET}${GREEN}@sams-product-plugins${RESET}"
  echo ""
  echo -e "  ${DIM}See README.md for full usage guide${RESET}"
  echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

main() {
  print_banner
  step_platform_check
  step_prerequisites
  step_python_deps
  step_qmd
  step_knowledge_dirs
  step_template_files
  step_mcp_config
  step_cursor_setup
  step_plugins
  step_verification
  print_next_steps
}

main "$@"
