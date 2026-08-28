# Gen - FCC-ee: Open TODOs

- **Background samples** — WW and ZZ (the two largest backgrounds) are now
  covered as an optional side task, see [`backgrounds.md`](backgrounds.md);
  both generated with pure Pythia8 (no WHIZARD step needed). Still open:
  whether/how this tutorial folds these into the main flow (e.g. does
  `Analysis` actually use them for anything, or are they just a generation
  exercise) versus leaving them as a standalone side task.
- **Jupyter notebook export** — Jupyter itself was ruled out as the primary
  authoring format (too complicated with FCCAnalyses, per planning notes),
  but a one-way export of this markdown material to `.ipynb` (e.g. via
  [`jupytext`](https://jupytext.readthedocs.io/)) could still be useful for
  students who'd rather work in a notebook. Not attempted — would need some
  markup convention to mark which fenced code blocks are meant to be
  executable Python cells versus illustrative shell/Sindarin/Pythia8-card
  snippets, since jupytext doesn't know the difference on its own.
- **Syntax highlighting for WHIZARD/Pythia8 files** — neither WHIZARD's
  Sindarin (`.sin`) format nor Pythia8's `.cmd` cards have a grammar in
  GitHub's Linguist (so no fenced-code-block language tag lights them up on
  GitHub) or an existing VSCodium/VSCode extension. Writing a small custom
  TextMate grammar for one or both (packaged as a minimal VSCodium
  extension, or bundled in this repo) would fix local editing at least;
  GitHub rendering would still fall back to a closest-fit generic tag (e.g.
  `ini`-ish for the Pythia8 cards) or plain text. Not started.

`mumuH_Hbb.cmd` leaves several PYTHIA6-only settings from the reference
production configuration (see `README.md`'s References) unported, since
PYTHIA6 and Pythia8 don't always define equivalent-sounding parameters the
same way — porting the tuned numbers directly would risk introducing wrong
physics. The approach instead is to match which *feature* was enabled and
use Pythia8's own default values for how it behaves:

- **Bose-Einstein correlations** — left off (Pythia8 default). It only
  affects identical-boson pairs (pions/kaons), not muons, so the mu mu
  recoil mass is unaffected; for the H -> b b dijet mass it's at most a
  small within-jet momentum redistribution, since the algorithm is
  designed to conserve overall jet 4-momentum (see the
  [Pythia8 manual](https://pythia.org/manuals/pythia8315/Welcome.html)).
- **Long-lived particle stability** — left off (Pythia8 default). The
  reference PYTHIA6 configuration uses a cylindrical decay-vertex-position
  cutoff (`MSTJ(22)=4`), not a proper-lifetime one — the actual Pythia8
  analog is `ParticleDecays:limitCylinder`, not `ParticleDecays:limitTau0`
  (see the [Pythia8 manual](https://pythia.org/manuals/pythia8315/Welcome.html)).
  At FCC-ee energies, K_S0/Lambda decay well within that cylinder anyway,
  so Pythia8's default behaviour (its own built-in per-particle lifetime
  threshold, which also decays K_S0/Lambda) already matches.
- **Fragmentation function for b/c quarks** — no change needed: for
  massive quarks, the Bowler modification to the Lund fragmentation
  function (PYTHIA6's `MSTJ(11)=3`) is already Pythia8's default (see the
  [Pythia8 manual](https://pythia.org/manuals/pythia8315/Welcome.html)).
- **Higgs mass and width** — no change: Pythia8's own default (125.0 GeV,
  4.08 MeV width) already closely matches the reference configuration's
  125 GeV / 4.143 MeV.
- **Lund `a`/`b`/`sigma` and diquark/meson-multiplet tune** — left at
  Pythia8's own defaults (`StringZ:aLund`/`bLund`, `StringPT:sigma`,
  `StringFlav:...`, see the
  [Pythia8 manual](https://pythia.org/manuals/pythia8315/Welcome.html)):
  these are baseline numeric tuning parameters Pythia8 always applies
  some value for, not on/off features, so cross-code numeric equivalence
  isn't assumed. For reference, the PYTHIA6 configuration's Lund a/b
  (0.11/0.52) differ substantially from Pythia8's defaults (0.68/0.98) —
  a real tune difference, not just an unset default.
- **Tau decay** — no external tool used (the reference configuration
  defers tau decay to an external tool like TAUOLA for correct
  spin/polarization correlations). Taus do appear in this chain (not from
  the forced H -> b b decay, but from semitauonic B-hadron decays after
  the b/bbar hadronize, at the ~2-3%-per-B branching level), but they're
  secondary objects inside b-jets, and neither of this tutorial's
  measurements is sensitive to tau polarization, so Pythia8's own native
  tau decay treatment is adequate. `PythiaInterface`'s `doEvtGenDecays`
  option (currently off) would route B-hadron decays through EvtGen
  instead of Pythia8's built-in table if more precise modeling is ever
  needed.
