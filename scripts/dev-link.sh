#!/usr/bin/env bash
#
# dev-link.sh - Redirect Codex skill symlinks to a local repo checkout
#
# Usage:
#   ./scripts/dev-link.sh link [skill-name]    # Link all or one skill to local repo
#   ./scripts/dev-link.sh unlink [skill-name]  # Restore original symlinks
#   ./scripts/dev-link.sh status               # Show current link state
#
set -euo pipefail

CODEX_SKILLS_DIR="${CODEX_SKILLS_DIR:-${HOME}/.agents/skills}"
BACKUP_DIR="${CODEX_SKILLS_DIR}/.dev-link-backup"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_SKILLS_DIR="${REPO_ROOT}/skills"

usage() {
    cat <<EOF
Usage: $(basename "$0") <command> [skill-name]

Commands:
  link [skill]    Redirect skill symlinks to local repo checkout
  unlink [skill]  Restore original installed symlinks
  status          Show which skills are linked locally vs installed

Examples:
  $(basename "$0") link              # Link all skills
  $(basename "$0") link jira         # Link only jira
  $(basename "$0") unlink            # Restore all skills
  $(basename "$0") unlink jira       # Restore only jira
  $(basename "$0") status            # Show current state
EOF
}

# Get list of skills to operate on.
# If a skill name is provided, use that; otherwise use all skills in the repo.
get_skills() {
    local skill_name="${1:-}"
    if [[ -n "${skill_name}" ]]; then
        if [[ ! -d "${REPO_SKILLS_DIR}/${skill_name}" ]]; then
            echo "Error: Skill '${skill_name}' not found in ${REPO_SKILLS_DIR}" >&2
            exit 1
        fi
        echo "${skill_name}"
    else
        for skill_dir in "${REPO_SKILLS_DIR}"/*/; do
            basename "${skill_dir}"
        done
    fi
}

cmd_link() {
    local skill_name="${1:-}"
    local skills
    skills="$(get_skills "${skill_name}")"

    mkdir -p "${BACKUP_DIR}"

    local linked=0
    local skipped=0
    while IFS= read -r skill; do
        local codex_skill="${CODEX_SKILLS_DIR}/${skill}"
        local local_skill="${REPO_SKILLS_DIR}/${skill}"

        # Check if already linked to local repo
        if [[ -L "${codex_skill}" ]]; then
            local current_target
            current_target="$(readlink "${codex_skill}")"
            if [[ "${current_target}" == "${local_skill}" ]]; then
                echo "  skip: ${skill} (already linked to local repo)"
                skipped=$((skipped + 1))
                continue
            fi
        fi

        # Back up the original symlink target (or note if it doesn't exist)
        if [[ -L "${codex_skill}" ]]; then
            readlink "${codex_skill}" > "${BACKUP_DIR}/${skill}"
        elif [[ -d "${codex_skill}" ]]; then
            # It's a real directory, not a symlink - record this
            echo "  warn: ${skill} at ${codex_skill} is a directory, not a symlink; skipping" >&2
            skipped=$((skipped + 1))
            continue
        elif [[ ! -e "${codex_skill}" ]]; then
            # Doesn't exist yet - record this so unlink knows to remove it
            echo "__created__" > "${BACKUP_DIR}/${skill}"
        fi

        # Remove existing and create new symlink
        rm -f "${codex_skill}"
        ln -s "${local_skill}" "${codex_skill}"
        echo "  link: ${skill} -> ${local_skill}"
        linked=$((linked + 1))
    done <<< "${skills}"

    echo ""
    echo "Linked ${linked} skill(s), skipped ${skipped}."
    if [[ ${linked} -gt 0 ]]; then
        echo "Start a new Codex conversation to use local versions."
    fi
}

cmd_unlink() {
    local skill_name="${1:-}"
    local skills
    skills="$(get_skills "${skill_name}")"

    local restored=0
    local skipped=0
    while IFS= read -r skill; do
        local codex_skill="${CODEX_SKILLS_DIR}/${skill}"
        local backup_file="${BACKUP_DIR}/${skill}"

        if [[ ! -f "${backup_file}" ]]; then
            echo "  skip: ${skill} (no backup found, not dev-linked)"
            skipped=$((skipped + 1))
            continue
        fi

        local original_target
        original_target="$(cat "${backup_file}")"

        if [[ "${original_target}" == "__directory__" ]]; then
            echo "  skip: ${skill} (original installation is a directory)"
            rm -f "${backup_file}"
            skipped=$((skipped + 1))
            continue
        elif [[ "${original_target}" == "__created__" ]]; then
            # Was created by dev-link, just remove it
            rm -f "${codex_skill}"
            echo "  remove: ${skill} (was not installed before dev-link)"
        else
            # Restore the original symlink
            rm -f "${codex_skill}"
            ln -s "${original_target}" "${codex_skill}"
            echo "  restore: ${skill} -> ${original_target}"
        fi

        rm -f "${backup_file}"
        restored=$((restored + 1))
    done <<< "${skills}"

    echo ""
    echo "Restored ${restored} skill(s), skipped ${skipped}."

    # Clean up backup directory if empty
    if [[ -d "${BACKUP_DIR}" ]] && [[ -z "$(ls -A "${BACKUP_DIR}" 2>/dev/null)" ]]; then
        rmdir "${BACKUP_DIR}"
    fi
}

cmd_status() {
    local skills
    skills="$(get_skills "")"

    echo "Skill link status:"
    echo ""

    while IFS= read -r skill; do
        local codex_skill="${CODEX_SKILLS_DIR}/${skill}"

        if [[ -L "${codex_skill}" ]]; then
            local target
            target="$(readlink "${codex_skill}")"
            if [[ "${target}" == "${REPO_SKILLS_DIR}/"* ]]; then
                echo "  ${skill}: LOCAL (${target})"
            else
                echo "  ${skill}: installed (${target})"
            fi
        elif [[ -d "${codex_skill}" ]]; then
            echo "  ${skill}: installed (directory)"
        elif [[ ! -e "${codex_skill}" ]]; then
            echo "  ${skill}: not installed"
        fi
    done <<< "${skills}"
}

# Main
if [[ $# -lt 1 ]]; then
    usage
    exit 1
fi

command="$1"
shift

case "${command}" in
    link)
        cmd_link "${1:-}"
        ;;
    unlink)
        cmd_unlink "${1:-}"
        ;;
    status)
        cmd_status
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        echo "Error: Unknown command '${command}'" >&2
        echo "" >&2
        usage >&2
        exit 1
        ;;
esac
