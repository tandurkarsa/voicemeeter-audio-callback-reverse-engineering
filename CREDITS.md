# Credits

## 🙏 Authorship & Attribution

This repository exists because of an **honest collaboration between a human
and an AI**.

### 🧠 The Human — Ideation & Direction
**[YOUR_NAME / YOUR_GITHUB_USERNAME]**

- Initiated the project
- Defined the workflow and design goals
- Provided the real-world context (Voicemeeter usage patterns)
- Ran every test on real hardware
- Made every technical decision
- Asked the right questions to unblock the AI
- Caught bugs by testing in production scenarios

**Contribution type:** Ideation, direction, verification, execution.

### 🤖 The AI — Reverse-Engineering & Documentation
**DeepSeek (DeepSeek-V3 / deepseek-chat)** by DeepSeek AI

- Analyzed binary headers, SDK examples, and community sources
- Wrote the ctypes wrappers and example code
- Drafted the documentation
- Traced through logic to identify mode/command mismatches
- Suggested hypotheses that were then verified by the human

**Contribution type:** Code generation, documentation, analysis.

### 🎯 Why We're Being Transparent

This project demonstrates that **modern software development can be a
partnership between human intuition and AI capabilities**. The human
brought the *"what"* and *"why"*; the AI brought the *"how"*.

Neither could have produced this repo alone:
- AI can't test on real hardware or know that a user's VAIO audio was leaking to LFE
- Human doesn't have time to read hundreds of pages of C headers and PDF docs

**We believe transparency about AI involvement is a virtue, not a weakness.**

---

## 📚 Sources Consulted

- `VoicemeeterRemoteAPI.pdf` — Official API documentation (X.1.2.9, Sept 2026)
- `VoicemeeterRemote.h` — C header (extracted via Rust bindings)
- `vmr_client.c` — Official C example
- `vmr_matrix.c` — Official APO example
- Community discussion: VB-Audio Forum, GitHub issues from other projects
- Real hardware testing on Voicemeeter Potato 3.1.3.0

---

## 🎓 If You Use This Documentation

You don't need to credit us, but if you find it useful, we'd love to know.
Open an issue or a discussion — tell us what you built!

---

*Last updated: 2026-10-14*