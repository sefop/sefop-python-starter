# CLAUDE.md

---

## Project overview

- Python starter reference implementation of the [SEFOP framework](https://github.com/fjzs/sefop) — a framework that brings software engineering techniques to 
  decision-support software.
- Every design decision should be commented clearly in the file so data scientists can understand its purpose.
- This project should use minimal dependencies so this repository can be used by scientists easily.
- Use simply language and comment the code relentlessly according to .claude/skills/comment-code/SKILL.md so any data scientist without knowledge in software engineering 
  can understand this repository.
- The project should be designed in such a way that it is easy to fork and reuse.

## Design Philosophy

Guided by "A Philosophy of Software Design" (Ousterhout):

- **Complexity is the enemy.** Minimize unnecessary complexity through clear interfaces and information hiding.
- **Invest in design upfront.** Strategic programming: spend time on clean abstractions now to avoid patchy workarounds later.
- **Design for the common case.** Optimize the expected usage pattern; handle edge cases without complicating the happy path.

Red flags that signal design problems: shallow modules, information leakage between layers, pass-through methods that add no value, and generic data containers that force callers to understand details.

## Code quality rules

- Never compare floats with `==` or `!=`; use `math.isclose()` instead (Python:S1244).