# Advanced Usage

## SSH Commands

For operations not covered by git-review:

```bash
# Query open changes
ssh -p 29418 review.example.com gerrit query status:open project:myproject

# Query specific change
ssh -p 29418 review.example.com gerrit query change:12345

# Review from command line
ssh -p 29418 review.example.com gerrit review 12345,3 --verified +1 --message "'Looks good'"

# Abandon change
ssh -p 29418 review.example.com gerrit review 12345 --abandon
```

Full reference: [Gerrit SSH Commands](https://gerrit-review.googlesource.com/Documentation/cmd-index.html)

## JSON Output for Scripting

```bash
# Get change info as JSON
ssh -p 29418 review.example.com gerrit query --format=JSON change:12345

# Process with jq
ssh -p 29418 review.example.com gerrit query --format=JSON status:open | jq '.subject'
```

## Multiple Gerrit Servers

```bash
# Set remote for specific server
git config gitreview.remote gerrit-prod

# Or specify via command line
git review -r gerrit-staging
```
