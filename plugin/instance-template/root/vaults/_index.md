---
type: index
tags: [os, vaults, federation]
---
# Federated Vaults

Symlinks that pull project-local vaults into this Obsidian graph **without moving their files**. Each stays owned by, and beside, its repository.

| Vault | Symlink target | Owner repository | Conventions |
|-------|----------------|------------------|-------------|
| _(none yet)_ | | | |

## Adding a federated vault

```bash
ln -s ../../<repository>/<vault-folder> vaults/<name>
```

## Rules

- **Edit federated notes in their own conventions**, not this instance's: they belong to their repository.
- Their content is committed in their repositories; this one commits only the symlinks.
- On a machine without those checkouts the symlinks dangle. That is harmless: Obsidian shows them empty.
- Knowledge that matters across projects is still **promoted** into [[memory/wiki/_index|memory/wiki/]]. Federation is for navigation, promotion is for canon.
