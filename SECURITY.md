# Security Policy 

## Keep your Open Cloud API key safe

This toolkit talks to the Roblox **Open Cloud API** using a secret **API key**.

**Never commit your key to GitHub.** This repository's `.gitignore` already blocks
the common key files and the migration data, but you should still double-check
before every commit.

### Recommended: keep the key in a separate file

Create a file **outside** this repository (e.g. `C:\Users\You\Downloads\roblox key data.txt`)
and point `scripts/config.py` at it:

```python
API_KEY_FILE = r"C:\Users\You\Downloads\roblox key data.txt"
```

If you must keep it inside the repo while testing, name it `key.txt` — it is
already ignored.

### If a key leaks

1. Go to **create.roblox.com → Credentials**.
2. **Delete** the leaked key immediately.
3. Create a new one and update your config.

Deleting a leaked key is instant and stops all further use.

### GitHub tokens

If you published this repo with a GitHub personal access token, **revoke the token**
afterwards (GitHub → Settings → Developer settings → Personal access tokens)
and, if pushed in a URL, re-point your remote to SSH.

## What we ask from contributors

- Never include real API keys, real player data, or real user IDs in commits,
  issues, or pull requests.
- Use the placeholder IDs in `scripts/config.example.py` in any examples.
