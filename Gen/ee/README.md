# Gen - FCC-ee

WHIZARD generates the hard process e+e- -> mu+ mu- H, then Pythia8 showers,
hadronizes, and decays H -> b b. See the callout below for why the process
is e+e- -> mu+ mu- H and not e+e- -> Z H.

## Environment setup

Everything needed (WHIZARD, Pythia8, the Key4hep/Gaudi tools) comes from the
Key4hep stack:

```
source /cvmfs/sw.hsf.org/key4hep/setup.sh
```

(`/cvmfs/fcc.cern.ch/sw/latest/setup.sh` provides the same Key4hep stack
plus FCC-specific tools on top.)

## Step 1: WHIZARD - hard process

Check WHIZARD is available:

```
which whizard
```

WHIZARD has no complete, supported interface to Pythia8 — only to the
legacy PYTHIA6. So this step only generates the hard process and writes it
out as LHEf; showering, hadronization, and the H -> b b decay all happen as
an explicit separate step in Pythia8 (Step 2 below), rather than inside
WHIZARD itself.

The card, [`mumuH.sin`](mumuH.sin):

```
model = SM

# Center of mass energy
sqrts = 240 GeV

process mumuH = e1, E1 => e2, E2, H

beams = e1, E1 => gaussian => isr

gaussian_spread1 = 0.185%
gaussian_spread2 = 0.185%

?isr_handler      = true
$isr_handler_mode = "recoil"
isr_alpha         = 0.0072993
isr_mass          = 0.000511

# Production-quality precision (slow to integrate live):
# integrate (mumuH) { iterations = 10:100000:"gw", 5:200000:"" }
# Classroom default (faster, lower precision):
integrate (mumuH) { iterations = 3:2000:"gw" }

n_events = 1000

$lhef_version  = "3.0"
sample_format  = lhef
simulate (mumuH) { $sample = "mumuH" }
```

Run it in its own directory:

```
mkdir -p test_whizard/mumuH && cd test_whizard/mumuH
cp ../../mumuH.sin .
whizard mumuH.sin
```

This produces `mumuH.lhe`.

Two settings are deliberately left out rather than pinned explicitly,
relying on their WHIZARD defaults:

- **`mH` (Higgs mass)** — not set, because WHIZARD's `SM` model already
  defaults it to 125 GeV (`parameter mH = 125` in `SM.mdl`).
- **`?keep_beams` / `?keep_remnants`** — not set, relying on their
  defaults (`false` and `true`). `?keep_beams = true` writes the original
  beam particles into the LHE record as extra entries, which breaks
  reading the file into Pythia8 downstream — WHIZARD's own manual
  explicitly warns against this. `?keep_remnants` only has any effect
  when `?keep_beams = true`, so it's inert either way here.

### Why mu mu H, not Z H?

WHIZARD is asked to generate e+e- -> mu+ mu- H directly, rather than
e+e- -> Z H with Z -> mu mu. The final state looks the same, but the
generator-level parent history doesn't: in the mu mu H process the two
muons' parent particles are the incoming e+/e-, not a Z boson. This matters
downstream once students truth-match particles in the Analysis stage —
don't be surprised the muons have no Z parent in the event record.

## Step 2: Pythia8 - shower, hadronize, decay H -> b b

FCC-ee tooling doesn't call Pythia8 as a bare standalone binary — it goes
through the Gaudi components in
[`key4hep/k4Gen`](https://github.com/key4hep/k4Gen) (`PythiaInterface` +
`GenAlg`), run with `k4run`, the same framework used later for Delphes and
FCCAnalyses. `PythiaInterface` reads a `.cmd` card, which can point at an
external LHE file, as in `k4Gen`'s own
[`data/Pythia_LHEinput.cmd`](https://github.com/key4hep/k4Gen/blob/main/k4Gen/data/Pythia_LHEinput.cmd)
example.

The card, [`mumuH_Hbb.cmd`](mumuH_Hbb.cmd):

```
! Reads the WHIZARD LHE output from Step 1 and forces H -> b b. Vertex/time
! smearing is done separately in the Gaudi steering script
! (pythia_mumuH.py), not here.

! Read in the WHIZARD LHEf file
Beams:frameType = 4
Beams:LHEF = mumuH.lhe
Beams:setProductionScalesFromLHEF = off
Beams:allowMomentumSpread = off

! ISR already handled by WHIZARD's isr_handler in Step 1 - keep off here to
! avoid double-counting radiation. FSR stays on (Pythia8 default): it's what
! actually showers the H -> b b decay products before hadronization - with
! it off, b/bbar go straight into string fragmentation with zero shower.
PartonLevel:ISR = off

Check:epTolErr = 1e-1
LesHouches:matchInOut = off

! Force H -> b b
25:onMode  = off
25:onIfAny = 5

! No long-lived-particle or Bose-Einstein settings here - Pythia8's
! defaults already give the desired behaviour for both; see
! Gen/ee/README.md's Open TODOs.
```

> **The ISR photon isn't present in the output.** WHIZARD's ISR treatment
> correctly reduces the visible mu mu H system's kinematics to reflect the
> radiated energy (its total energy varies event-by-event, roughly
> 235.5-239.7 GeV instead of a fixed 240, with occasional non-zero net
> transverse momentum), but the radiated photon itself is classified by
> WHIZARD as a "beam remnant" and — with `?keep_beams = false` — isn't
> written into the event record. This doesn't affect this tutorial's two
> measurements (mu mu recoil mass, H -> b b dijet mass — both driven by
> the visible mu/mu/b/bbar kinematics, which already reflect the
> ISR-induced recoil), but it does mean there's no possibility of
> reconstructing an ISR photon downstream in `Sim/ee`/`Analysis`.

Steering script [`pythia_mumuH.py`](pythia_mumuH.py), adapted from
`k4Gen`'s own
[`options/pythia.py`](https://github.com/key4hep/k4Gen/blob/main/k4Gen/options/pythia.py)
example — reads the card above and writes EDM4hep rather than plain HepMC
(`HepMCFileWriter`'s own docstring says plain HepMC is for debugging, not
event storage). Beamspot vertex/time smearing is applied via the Gaudi
`GaussSmearVertex` tool wired into `GenAlg`, rather than Pythia8's own
`Beams:allowVertexSpread`, which would apply it a second time on top of
this:

```python
from Gaudi.Configuration import *
from GaudiKernel import SystemOfUnits as units
from edm4hep import labels as e4_labels

from Configurables import EventDataSvc
from k4FWCore import ApplicationMgr, IOSvc
ApplicationMgr().EvtSel = 'NONE'
ApplicationMgr().EvtMax = 1000
ApplicationMgr().ExtSvc += ["RndmGenSvc", EventDataSvc("EventDataSvc")]

# Beamspot vertex/time smearing (FCC-ee IDEA values). Done here via the
# Gaudi VertexSmearingTool rather than Pythia8's own Beams:allowVertexSpread,
# so it isn't applied twice.
from Configurables import GaussSmearVertex
smeartool = GaussSmearVertex()
smeartool.xVertexSigma = 5.96e-3 * units.mm
smeartool.yVertexSigma = 23.8e-6 * units.mm
smeartool.zVertexSigma = 0.397 * units.mm
smeartool.tVertexSigma = 10.89 * units.mm

from Configurables import PythiaInterface
pythia8gentool = PythiaInterface()
pythia8gentool.pythiacard = "mumuH_Hbb.cmd"

from Configurables import GenAlg
pythia8gen = GenAlg("Pythia8")
pythia8gen.SignalProvider = pythia8gentool
pythia8gen.VertexSmearingTool = smeartool
pythia8gen.hepmc.Path = "hepmc"
# A small fraction of events (~1 in a few thousand) hit an unrecoverable
# Pythia8-level failure (e.g. energy-momentum conservation check) that
# retrying doesn't fix. Without raising this, Gaudi's default ErrorMax = 1
# means a single such event aborts the whole run - only shows up at scale
# (not in a 1000-event test). ErrorMax = 20 lets a handful be skipped
# instead. Deprecated on some Gaudi versions but still functional.
pythia8gen.ErrorMax = 20
ApplicationMgr().TopAlg += [pythia8gen]

from Configurables import HepMCToEDMConverter
hepmc_converter = HepMCToEDMConverter()
hepmc_converter.hepmc.Path = "hepmc"
hepmc_converter.hepmcStatusList = []
hepmc_converter.GenParticles.Path = e4_labels.MCParticles
ApplicationMgr().TopAlg += [hepmc_converter]

iosvc = IOSvc()
iosvc.Output = "mumuH_Hbb.root"
```

Copy both files next to the LHE file produced in Step 1 and run:

```
cp ../../mumuH_Hbb.cmd ../../pythia_mumuH.py .
k4run pythia_mumuH.py
```

This produces `mumuH_Hbb.root`, an EDM4hep file with the showered,
hadronized, H -> b b decayed event record, in an `MCParticles` collection.

`Sim/ee` consumes this file's `MCParticles` collection directly via
`k4SimDelphesAlg` from
[`key4hep/k4SimDelphes`](https://github.com/key4hep/k4SimDelphes) — that
component takes a generic `edm4hep::MCParticleCollection` as input,
independent of how it was produced.

## Open TODOs

- **Background samples** — undecided whether this tutorial includes any
  background processes alongside the mumuH signal, and if so how they'd be
  generated. One tentative idea floated: generate backgrounds with pure
  Pythia8 (no WHIZARD step), since Pythia8 alone can produce e.g. generic
  qqbar/WW/ZZ final states without needing WHIZARD's matrix-element
  machinery. Not decided or attempted.
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
production configuration (see References) unported, since PYTHIA6 and
Pythia8 don't always define equivalent-sounding parameters the same way —
porting the tuned numbers directly would risk introducing wrong physics.
The approach instead is to match which *feature* was enabled and use
Pythia8's own default values for how it behaves:

- **Bose-Einstein correlations** — left off (Pythia8 default). It only
  affects identical-boson pairs (pions/kaons), not muons, so the mu mu
  recoil mass is unaffected; for the H -> b b dijet mass it's at most a
  small within-jet momentum redistribution, since the algorithm is
  designed to conserve overall jet 4-momentum.
- **Long-lived particle stability** — left off (Pythia8 default). The
  reference PYTHIA6 configuration uses a cylindrical decay-vertex-position
  cutoff (`MSTJ(22)=4`), not a proper-lifetime one — Pythia8's
  `ParticleDecays:limitCylinder` is the actual analog, not
  `ParticleDecays:limitTau0`. At FCC-ee energies, K_S0/Lambda decay well
  within that cylinder anyway, so Pythia8's default behaviour (its own
  built-in per-particle lifetime threshold, which also decays K_S0/Lambda)
  already matches.
- **Fragmentation function for b/c quarks** — no change needed: Pythia8's
  manual states that for massive quarks, the Bowler modification to the
  Lund fragmentation function (PYTHIA6's `MSTJ(11)=3`) is already the
  default.
- **Higgs mass and width** — no change: Pythia8's own default (125.0 GeV,
  4.08 MeV width) already closely matches the reference configuration's
  125 GeV / 4.143 MeV.
- **Lund `a`/`b`/`sigma` and diquark/meson-multiplet tune** — left at
  Pythia8's own defaults (`StringZ:aLund`/`bLund`, `StringPT:sigma`,
  `StringFlav:...`): these are baseline numeric tuning parameters Pythia8
  always applies some value for, not on/off features, so cross-code
  numeric equivalence isn't assumed. For reference, the PYTHIA6
  configuration's Lund a/b (0.11/0.52) differ substantially from Pythia8's
  defaults (0.68/0.98) — a real tune difference, not just an unset
  default.
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

## References

- WHIZARD card this stage's `mumuH.sin` is adapted from:
  [`wzp6_ee_mumuH_Hbb_ecm240.sin`](https://github.com/HEP-FCC/FCC-config/blob/winter2023/FCCee/Generator/Whizard/v3.0.3/wzp6_ee_mumuH_Hbb_ecm240.sin)
  (`FCC-config`, `winter2023` branch — production campaigns live on their
  own branch, not on `main`).
- Pythia8 card this stage's `mumuH_Hbb.cmd` is adapted from:
  [`p8_ee_default.cmd`](https://github.com/HEP-FCC/FCC-config/blob/winter2023/FCCee/Generator/Pythia8/p8_ee_default.cmd)
  (`FCC-config`, `winter2023` branch).

## What's next

The showered, H -> b b decayed sample (`mumuH_Hbb.root`) is the input to
Delphes fast simulation with the FCC-ee IDEA card — see `Sim/ee`.
