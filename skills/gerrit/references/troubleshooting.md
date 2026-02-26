# Troubleshooting

```bash
# Re-run setup
git review -s

# Force setup (fixes common issues)
git review -s --force

# Verbose output for debugging
git review -v

# Check configuration
cat .gitreview
git config -l | grep gitreview

# Test SSH connection
ssh -p 29418 youruser@review.example.com gerrit version
```

## Common Issues

**"We don't know where your gerrit is"**
```bash
git review -s              # Run setup
# Or create .gitreview file manually
```

**"fatal: 'gerrit' does not appear to be a git repository"**
```bash
git review -s              # Setup remote
git remote -v              # Verify gerrit remote exists
```

**"Permission denied (publickey)"**
```bash
# Add SSH key to Gerrit (Settings > SSH Keys)
# Or configure username:
git config --global gitreview.username youruser
```

**Change-Id missing**
```bash
# Install commit-msg hook
curl -Lo .git/hooks/commit-msg \
  https://review.example.com/tools/hooks/commit-msg
chmod u+x .git/hooks/commit-msg

# Or let git-review install it
git review -s
```
