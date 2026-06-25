# Security

## Reporting vulnerabilities

To report a security vulnerability, please open a [GitHub issue](https://github.com/odyssey4me/agent-skills/issues) with the label `security`. For sensitive disclosures, contact the maintainer directly.

## Dependency management

### Python dependencies

Python dependencies are managed by [uv](https://docs.astral.sh/uv/) with a lockfile (`uv.lock`). [Renovate](https://docs.renovatebot.com/) monitors for updates and opens PRs automatically. Patch and minor updates auto-merge when CI passes. [Dependabot security alerts](https://docs.github.com/en/code-security/dependabot/dependabot-alerts) are enabled for CVE notifications.

### External CLI tools

Some skills depend on external CLI tools (e.g., `gog` for Google Workspace, `gh` for GitHub). These are not installed by the skill — users install them separately.

#### gogcli (gog)

The Google Workspace skill pins a specific gogcli version with SHA-256 checksums in `skills/google/dependencies.json`. The update and validation process:

1. **Renovate** detects new [gogcli releases](https://github.com/openclaw/gogcli/releases) and opens a PR bumping the version. gogcli PRs require manual review (no auto-merge) and have a 7-day minimum release age.

2. **CI validation** (`validate-gogcli` workflow) runs automatically on the PR:
   - Fetches release checksums from the GitHub release and updates `dependencies.json`
   - Downloads the release tarball and verifies its SHA-256 checksum
   - Clones the gogcli source at the tagged version
   - Runs [`govulncheck`](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck) to scan for known CVEs in gogcli's Go dependencies
   - Stamps a validation timestamp in `dependencies.json`

3. **Manual review and merge** after all checks pass.

The `check` command (`skills/google/scripts/google.py check`) reports whether the installed binary matches the pinned version and when it was last validated.

#### Limitations

- **No SLSA provenance** — gogcli does not publish signed build provenance attestations, so we cannot cryptographically verify that release binaries were built from the claimed source
- **No code audit** — govulncheck covers known CVEs in dependencies but does not audit gogcli's own application code; gosec and go vet are covered by [gogcli's own CI](https://github.com/openclaw/gogcli/blob/main/.github/workflows/ci.yml)

## CI security checks

- **[CodeQL](https://codeql.github.com/)** — enabled on push to `main`, scans Python code for security vulnerabilities
- **[Dependabot security alerts](https://docs.github.com/en/code-security/dependabot)** — monitors Python dependencies for known CVEs
- **[Renovate OSV vulnerability alerts](https://docs.renovatebot.com/configuration-options/#osvvulnerabilityalerts)** — additional vulnerability scanning via the OSV database
- **[skillsaw](https://github.com/stbenjam/skillsaw)** — lints agent skill structure and content (run in strict mode locally and in CI)
- **Secret scanning** — enabled with push protection to prevent accidental credential commits
