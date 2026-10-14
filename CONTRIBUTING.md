# Contributing

Thanks for wanting to help! Here's how.

## 🐛 Found a Bug or Different Behavior?

**Open an issue** with:
1. Your Voicemeeter version (e.g., Potato 3.1.3.0)
2. Your OS (Windows 10/11, 32/64-bit)
3. Python version
4. Script you ran (or minimal reproducer)
5. Expected vs actual behavior
6. Console output (full stack trace)

## 💡 Found a New Discovery?

**Open a PR** that adds:
- Documentation update in `docs/VOICEMEETER_API_NOTES.md`
- Example script in `examples/` (if applicable)
- CHANGELOG.md entry

## 🌍 Porting to Another Language?

We especially welcome:
- **Rust** (crate using `libloading`)
- **C#** (P/Invoke)
- **Node.js** (`ffi-napi` or similar)
- **Go** (`cgo`)

Create a folder like `ports/rust/` with your code + a `README.md` explaining differences.

## 📝 Style Guidelines

### Documentation
- Use **markdown** with clear headers
- Include **code examples** (tested)
- Add **screenshots** for UI-related findings
- Cite **Voicemeeter version** when relevant

### Code
- Python: **PEP 8**, 4-space indent, type hints if possible
- Keep **examples standalone** (no local imports from a project)
- Include `if __name__ == "__main__":` block for runnable files
- Comments in English

### Commit Messages
- Format: `type: short description`
- Types: `feat`, `fix`, `docs`, `examples`, `chore`
- Example: `docs: clarify mode bit flags`

## 🚫 What We DON'T Accept

- ❌ Code that distributes Voicemeeter itself (that's VB-Audio's)
- ❌ Reverse-engineered DLL internals (we only document public API)
- ❌ Non-English-only documentation (bilingual OK)
- ❌ Changes that break existing examples

## 🧪 Testing Checklist

Before submitting PR, verify:
- [ ] Examples run without errors
- [ ] Voicemeeter version noted
- [ ] CHANGELOG updated
- [ ] No personal info in commits
- [ ] Commit message follows format

## 💬 Questions?

Open a Discussion thread or an Issue with the `question` label.

Thanks! 🎛️
