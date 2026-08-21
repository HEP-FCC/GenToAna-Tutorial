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

The golden card for this process,
[`wzp6_ee_mumuH_Hbb_ecm240.sin`](https://github.com/HEP-FCC/FCC-config/blob/winter2023/FCCee/Generator/Whizard/v3.0.3/wzp6_ee_mumuH_Hbb_ecm240.sin),
lives on the `winter2023` campaign branch of `FCC-config` (each production
campaign gets its own branch off `main` — the golden card wasn't on `main`
itself). That card does everything in one go: it showers, hadronizes, and
forces H -> b b internally through WHIZARD's built-in interface to the
*legacy* PYTHIA6, and writes `stdhep`. That's how production samples are
actually made, but it skips the explicit, separate Pythia8 step this
tutorial wants students to see and configure themselves.

> WHIZARD *can* be linked against PYTHIA8 at build time
> (`--enable-pythia8`), but as of the current WHIZARD manual (covering up
> to v3.4.3) that integration isn't finished: the "Parton shower and
> hadronization from PYTHIA8" manual section is an empty stub, and the
> documented values for `$shower_method` are only `"WHIZARD"` (in-house)
> and `"PYTHIA6"` — `"PYTHIA8"` isn't one of them. So showering with
> Pythia8 as a separate step (Step 2 below) isn't just the pedagogically
> cleaner choice, it's the only well-supported way to bring Pythia8 into
> this chain at all.

So `mumuH.sin` below keeps the golden card's physics (process, energy, beam
spread and ISR settings) but strips the internal shower/hadronization/decay
lines and switches the output to LHEf, the same bare-generator pattern used
by the existing tutorial's own
[`Z_mumu.sin`](https://fccsw.web.cern.ch/fccsw/share/gen/whizard/Zpole/Z_mumu.sin)
example. The card is [`mumuH.sin`](mumuH.sin) in this directory:

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

# Golden-card value (production-quality precision, slow to integrate live):
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
relying on their defaults:

- **`mH` (Higgs mass)** — not set, because WHIZARD's `SM` model already
  defaults it to 125 GeV (`parameter mH = 125` in `SM.mdl`), matching the
  golden card's own `PMAS(25,1)=125.` and confirmed empirically: generated
  LHE events carry the Higgs at exactly 125.0 GeV. Note the sibling
  `wzp6_ee_mumuH_ecm240.sin` card instead sets `mH = 125.1 GeV` explicitly
  — a minor inconsistency between FCC-config's own cards, not something
  reconciled here (see the Higgs mass/width item in Open TODOs).
- **`?keep_beams` / `?keep_remnants`** — not set, because their defaults
  (`false` and `true` respectively) are exactly what's needed here.
  `?keep_beams = true` is what caused the Step 2 crash (see the Status
  callout below) — it writes the original beam particles into the LHE
  record as extra entries, which WHIZARD's own manual explicitly warns
  against for reading into PYTHIA. Leaving it at its default `false` avoids
  that. `?keep_remnants` only has any effect when `?keep_beams = true`
  (per the manual), so with `?keep_beams` at its default it's inert either
  way and isn't worth setting.

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
external LHE file exactly like the working example shipped in `k4Gen` itself
([`data/Pythia_LHEinput.cmd`](https://github.com/key4hep/k4Gen/blob/main/k4Gen/data/Pythia_LHEinput.cmd)).

[`mumuH_Hbb.cmd`](mumuH_Hbb.cmd) in this directory is based on
[`FCC-config`'s `p8_ee_default.cmd`](https://github.com/HEP-FCC/FCC-config/blob/winter2023/FCCee/Generator/Pythia8/p8_ee_default.cmd)
(`winter2023` branch) — the actual card FCC-config uses to read WHIZARD LHE
output into Pythia8 — with H -> b b decay-forcing added on top:

```
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
```

`p8_ee_default.cmd` itself sets `PartonLevel:FSR = off` too — appropriate
*there* because its use case is WHIZARD LHE files with the full final state,
including any colored partons, already present at the matrix-element level
(nothing left for Pythia8 to decay+shower). That's not our case: our LHE
only has e+e- -> mu+ mu- H with the Higgs undecayed, and we rely on Pythia8
itself to decay H -> b b and shower the result. Checked this directly by
dumping the Pythia8 event record: with `FSR = off`, the b/bbar from the
Higgs decay went straight into hadronization with no shower emissions at
all (unrealistic jets); with `FSR` left on (Pythia8's default), the event
record shows proper gluon-emission branching off the b/bbar before
hadronization, as expected.

`ISR = off` was checked the same way, and unlike FSR this one didn't reveal
a hidden dependency: with `ISR = on`, Pythia8 adds a genuine extra
initial-state radiation photon (visible in the event record, status `-43`,
radiated directly off one of the incoming leptons by Pythia8's own spacelike
shower) on top of the energy redistribution WHIZARD's `isr_handler` already
applied to the beam momenta — real double-counted radiation. With
`ISR = off`, that extra photon doesn't appear and nothing else changes; ISR
only concerns the initial state, so there's no FSR-style gating issue here.

> **Caveat: the ISR photon itself is invisible downstream, as a side
> effect of the `?keep_beams` crash fix, not a deliberate physics choice.**
> WHIZARD's `?isr_handler` (`$isr_handler_mode = "recoil"`) still generates
> a real ISR photon per beam internally and correctly recoils the visible
> system against it — checked directly on generated events: the mu+ mu- H
> system's total energy varies event-by-event (~235.5-239.7 GeV instead of
> a fixed 240) and sometimes carries non-zero net transverse momentum
> (e.g. 0.14 GeV), exactly the signature of a real recoil against a missing
> photon. But the WHIZARD manual classifies these radiated ISR photons as
> "beam remnants" (`?keep_remnants` docs: *"for ISR and/or beamstrahlung
> spectra, the radiated photons are considered as beam remnants"*), and
> remnants are gated by the same `?keep_beams` flag that had to be set to
> `false` to fix the Step 2 crash. So the photon itself is never written
> into the event record — confirmed structurally too: the old
> `?keep_beams = true` events had explicit outgoing photon lines; the
> fixed `?keep_beams = false` events don't. For this tutorial's actual
> measurements (mu mu recoil mass, H -> b b dijet mass) this doesn't
> matter, since both only depend on the visible mu/mu/b/bbar kinematics,
> which already correctly reflect the ISR-induced energy loss and recoil.
> It does mean there's no possibility of ever seeing a reconstructed ISR
> photon downstream in `Sim/ee`/`Analysis` — that option is gone as an
> unavoidable consequence of the crash fix, not a deliberate simplification.

Steering script [`pythia_mumuH.py`](pythia_mumuH.py), adapted from `k4Gen`'s
own
[`options/pythia.py`](https://github.com/key4hep/k4Gen/blob/main/k4Gen/options/pythia.py)
example — swap in the LHE-reading card above and write out EDM4hep rather
than plain HepMC (`HepMCFileWriter`'s own docstring says it's for debugging,
not for actual event storage). Beamspot vertex/time smearing is done here,
via the Gaudi `GaussSmearVertex` tool wired into `GenAlg`, using the same
FCC-ee IDEA beamspot values as `p8_ee_default.cmd`'s `Beams:sigmaVertex*`
settings — not via Pythia8's own `Beams:allowVertexSpread`, which would
apply it a second time on top of this:

```python
from Gaudi.Configuration import *
from GaudiKernel import SystemOfUnits as units
from edm4hep import labels as e4_labels

from Configurables import EventDataSvc
from k4FWCore import ApplicationMgr, IOSvc
ApplicationMgr().EvtSel = 'NONE'
ApplicationMgr().EvtMax = 1000
ApplicationMgr().ExtSvc += ["RndmGenSvc", EventDataSvc("EventDataSvc")]

# Beamspot vertex/time smearing (FCC-ee IDEA values, from FCC-config's
# p8_ee_default.cmd Beams:sigmaVertex{X,Y,Z}/sigmaTime). Done here via the
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
hadronized, H -> b b decayed event record.

> **Status: fixed — Step 2 now runs cleanly.** Actually ran the full chain
> against the real Key4hep stack (`/cvmfs/sw.hsf.org/key4hep/setup.sh`,
> WHIZARD 3.1.5, Pythia8 8.315). Step 1: `whizard mumuH.sin` gives
> sigma ~6.8 fb, matching the known sigma(ee->ZH)*BR(Z->mumu) ~ 200 fb *
> 3.37% ~ 6.7 fb at 240 GeV. Step 2 (`k4run pythia_mumuH.py`) initially
> crashed on the first event with:
> ```
> Pythia8              FATAL Standard std::exception is caught in sysExecute
> Pythia8              ERROR vector::_M_range_check: __n (which is 9) >= this->size() (which is 9)
> ```
> A `gdb` backtrace (`catch throw`) traced this to
> `Pythia8::PartonLevel::resonanceShowers()` ->
> `Pythia8::Particle::iBotCopyId()`, inside Pythia8's own machinery for
> decaying+showering a resonance (the Higgs) found mid-event. A zero-Gaudi
> standalone C++ reproducer (`Pythia pythia; pythia.readFile(...);
> pythia.init(); pythia.next();`) hit the identical crash, ruling out the
> 2026-08-19 meeting's "needs to be run as Gaudi functionals" lead — this
> was never a Gaudi/k4Gen issue.
>
> **Root cause, found via a warning comment on a sibling FCC-config card**
> ([`wzp6_ee_mumuH_ecm240.sin`](https://github.com/HEP-FCC/FCC-config/blob/winter2023/FCCee/Generator/Whizard/v3.0.3/wzp6_ee_mumuH_ecm240.sin)
> has `?keep_beams = true # do not use this option, makes Pythia crash`,
> left in place but unheeded in that card since it only ever exercises the
> internal PYTHIA6 path): our `mumuH.sin` had `?keep_beams = true` too. A
> clean retest (the very first attempt to test this flag turned out to be
> unreliable, from a contaminated debugging script, and wrongly seemed to
> rule it out) confirms `?keep_beams = false` fixes it completely — a full
> 1000-event run now completes with a single non-fatal
> "energy-momentum not quite conserved" warning and produces a valid
> `mumuH_Hbb.root` (`MCParticles` collection, 102 particles in the first
> event, fully hadronized). `mumuH.sin` no longer sets `?keep_beams` at
> all, relying on its default of `false` (see the Environment/Step 1
> section above).
>
> For the record, before finding the real cause, these were also tried and
> made no difference on their own (the actual fix was always `?keep_beams`):
> `PartonLevel:FSR` on vs off, `LesHouches:matchInOut` on vs off,
> `PartonLevel:earlyResDec = on`, LHEF version 2.0 vs 3.0, stripping
> WHIZARD's `<weights>` `sqme_prc` block, forcing H -> b b vs leaving the
> decay unforced, and forcing H completely stable (`25:mayDecay = off`).
>
> One earlier claim in this callout was wrong and is corrected here: an
> initial test seemed to show the crash was specific to particle ID 25
> (Higgs) as the LHE resonance, based on a WHIZARD LHE with a Z boson in
> H's place reading in cleanly — but that Z-boson test card never had
> `?keep_beams = true` set in the first place, so it wasn't a like-for-like
> comparison. Redone properly (identical card, only H swapped for Z,
> `?keep_beams = true` kept in both): the Z version crashes identically to
> the H version. So the crash is generic to `?keep_beams = true` plus any
> downstream resonance decay, exactly matching the (unheeded) FCC-config
> warning comment, not something Higgs-specific.

> **Tested at 10,000-event scale, found and fixed a second, scale-dependent
> issue.** A 1,000-event run only ever showed one non-fatal warning, but at
> 10,000 events a handful (~3 in 10,000) hit a Pythia8-level failure
> (energy-momentum check) that retrying doesn't recover from — it's the
> same event failing deterministically every time, not a transient issue.
> Without any fix, Gaudi's default per-algorithm `ErrorMax = 1` means even
> one such event aborts the *entire* run (job exits with an error, most
> events lost) — this never shows up at 1,000 events, only at scale. Fixed
> by setting `pythia8gen.ErrorMax = 20` in `pythia_mumuH.py`, so a handful
> of individually-unrecoverable events get skipped rather than ending the
> job. Verified: a clean 10,000/10,000-event run with this set.

> **Confirmed handoff to `Sim/ee`:** this stage hands off an EDM4hep ROOT
> file with an `MCParticles` collection, not a HepMC file and not a combined
> Pythia8+Delphes run. Checked `key4hep/k4SimDelphes`: its Gaudi component
> `k4SimDelphesAlg` reads a generic `edm4hep::MCParticleCollection` (data
> path `"GenParticles"`) — its own example steering script feeds it from a
> particle gun, not Pythia8, proving it doesn't care how that collection was
> produced. `DelphesPythia8_EDM4HEP` (which runs Pythia8 internally) is a
> separate, alternative standalone entry point in the same repo, not the
> only way in. So `Sim/ee` should use `k4SimDelphesAlg` via `k4run`, reading
> the `MCParticles` collection from `mumuH_Hbb.root` produced here — the
> Gen/Sim split as designed is correct.

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

The golden card's internal PYTHIA6 shower/hadronization step
(`$ps_PYTHIA_PYGIVE` in
[`wzp6_ee_mumuH_Hbb_ecm240.sin`](https://github.com/HEP-FCC/FCC-config/blob/winter2023/FCCee/Generator/Whizard/v3.0.3/wzp6_ee_mumuH_Hbb_ecm240.sin))
sets several physics parameters that have **not** been ported to
`mumuH_Hbb.cmd`, because PYTHIA6 parameter names don't map mechanically onto
Pythia8 settings and doing this properly needs someone to work out the
correct Pythia8-native equivalents (or confirm Pythia8 defaults are close
enough for a teaching sample):

- **Higgs mass and width** — the golden card sets `PMAS(25,1)=125.` and
  `PMAS(25,2)=0.4143E-02` (4.143 MeV) explicitly. `mumuH_Hbb.cmd` doesn't
  set `25:m0` / `25:mWidth`, so Pythia8's own defaults apply instead.
- **Hadronization / fragmentation tune** — the golden card carries a full
  set of Lund string parameters (`PARJ(1,2,3,4,11-17,21,41,42,54,55)`,
  `MSTJ(11)`, `MSTP(3)`). None of this has been translated into a Pythia8
  tune; Pythia8 defaults are used instead.
- **Bose-Einstein correlations** — the golden card turns these on with a
  specific tune (`MSTP(151)=1`, `PARP(151-154)`). Not enabled in
  `mumuH_Hbb.cmd` (off by Pythia8 default).
- **Long-lived particle stability treatment** — the golden card sets
  `MSTJ(22)=4` with `PARJ(73)=2250`, `PARJ(74)=2500`, controlling which
  particles get left stable (for the detector to handle) based on decay
  length. Not addressed in `mumuH_Hbb.cmd`; this could matter for how
  Delphes sees long-lived particles like K_S/Lambda downstream.

## What's next

The showered, H -> b b decayed sample (`mumuH_Hbb.root`) is the input to
Delphes fast simulation with the FCC-ee IDEA card — see `Sim/ee`.
