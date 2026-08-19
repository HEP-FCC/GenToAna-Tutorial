# Contributing

This repo is a living tutorial: instructors maintain the material between
schools, and students are welcome to send fixes for anything they hit
during the exercises.

## For students

- Found a typo, a broken command, or a step that doesn't match the current
  software stack? Open an issue, or fork the repo and open a pull request
  with the fix. This applies to any part of the tutorial, including the
  `.../<ee|hh>/solutions/` folders — PRs improving or correcting them are
  just as welcome as anywhere else.
- Keep questions about the exercises themselves for the tutorial's Mattermost
  channel rather than GitHub issues, so other students can see the answer too.
- Small, focused PRs (one fix per PR) are easier to review than bundled ones.

## For instructors

- New material goes under the relevant stage/collider folder
  (`Gen|Sim|Analysis/<ee|hh>/`); keep the corresponding
  `.../<ee|hh>/solutions/` folder in sync with any change to the exercise
  text so students can't get out of step with the reference answer.
- `main` holds the canonical, up-to-date version of the tutorial. Cut a
  branch (or tag) per school/date before making school-specific tweaks
  (fixed sample paths, pinned stack versions, schedule-specific trimming),
  and merge generally-useful fixes back to `main`.
- When updating generation/Delphes cards (WHIZARD, Pythia, Delphes IDEA/FCC-hh
  cards), note the FCCConfig/FCCDirac version they were validated against in
  the relevant README.
- Review PRs from students/co-instructors for correctness against the
  current FCCAnalyses stack before merging, since stack updates can silently
  break exercise steps.

## Style

- Material is plain Markdown; keep prose short and code blocks copy-pasteable.
- Prefer relative links between tutorial pages so branches/tags stay
  self-contained.

## License

By contributing, you agree that your contribution is licensed under this
repository's [CC BY-SA 4.0 license](LICENSE).
