# Gen - FCC-ee

WHIZARD generates the hard process e+e- -> mu+ mu- H, then Pythia8 showers,
hadronizes, and decays H -> b b. See the callout below for why the process
is e+e- -> mu+ mu- H and not e+e- -> Z H.

## Environment setup

Everything needed (WHIZARD, Pythia8, the Key4hep/Gaudi tools) comes from the
[Key4hep](https://key4hep.github.io/key4hep-doc/) stack — a shared software
stack for generation, simulation, reconstruction, and analysis, developed
jointly across several future-collider projects (FCC, CEPC, ILC, EIC) so
they don't each maintain their own separate framework:

```bash
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2026-04-08
```

This tutorial is pinned to the `2026-04-08` release rather than the
rolling `latest-opt` build, since the next Key4hep release isn't expected
to be ready in time.

Key4hep only supports bash for this — there's no `.csh`/`.tcsh` variant of
`setup.sh`. If your login shell is csh/tcsh, start a nested bash session
first (just run `bash`) and source the setup script inside that instead;
your original csh session is unaffected (no subshell can modify its
parent's environment) and stays there until you `exit` the bash session.

(`/cvmfs/fcc.cern.ch/sw/latest/setup.sh` provides the same Key4hep stack
plus FCC-specific tools on top.)

Key4hep bundles several e+e- event generators, not just WHIZARD and
Pythia8: also Herwig3, Sherpa, KKMCee (precision QED processes like Bhabha
scattering and muon pairs), MadGraph5_aMC@NLO, and EvtGen (heavy-flavour
hadron decays). WHIZARD is used for this signal process because it computes
the full e+e- -> mu mu H matrix element directly, with correct multi-particle
kinematics and spin correlations — other generators are better suited to
other processes (e.g. KKMCee for high-precision QED benchmarks).

## Step 1: WHIZARD - hard process

Check WHIZARD is available (and, via its path, that the right stack
release was sourced) and see its version:

```bash
which whizard
whizard --version
```

WHIZARD has no complete, supported interface to Pythia8 — only to the
legacy PYTHIA6 (see the
[WHIZARD manual](https://whizard.hepforge.org/manual.pdf)). So this step
only generates the hard process and writes it out as LHEf;
showering, hadronization, and the H -> b b decay all happen as an explicit
separate step in Pythia8 (Step 2 below), rather than inside WHIZARD itself.

The card, [`mumuH.sin`](mumuH.sin):

```
model = SM

# Center of mass energy
sqrts = 240 GeV

process mumuH = e1, E1 => e2, E2, H

beams = e1, E1 => gaussian => isr

# Beam energy spread (sigma, as a fraction of nominal beam energy) - not
# the same as beam-spot (vertex position) smearing, which is done later
# in Step 2's Pythia8 steering script.
gaussian_spread1 = 0.185%
gaussian_spread2 = 0.185%

?isr_handler      = true
$isr_handler_mode = "recoil"
isr_alpha         = 0.0072993
isr_mass          = 0.000511

# Production-quality precision. This dominates the whole run time
# regardless of n_events below (it's the cost of building the phase-space
# integration grids, done once, not per event) - about 90s here, vs ~7s
# for the faster, lower-precision alternative below.
integrate (mumuH) { iterations = 10:100000:"gw", 5:200000:"" }
# Faster, lower-precision alternative for quick iteration/testing:
# integrate (mumuH) { iterations = 3:2000:"gw" }

# Generate a few more events than Step 2 actually reads (EvtMax = 1000
# there): Pythia8's LHEF reader silently returns empty events for the
# last handful of records when the file's event count exactly matches
# EvtMax, since its retry-on-failure logic (Main:timesAllowErrors) just
# keeps hitting end-of-file. A small margin avoids ever reaching that
# boundary.
n_events = 1010

$lhef_version  = "3.0"
sample_format  = lhef
simulate (mumuH) { $sample = "mumuH" }
```

Run it in its own directory:

```bash
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
  reading the file into Pythia8 downstream — the
  [WHIZARD manual](https://whizard.hepforge.org/manual.pdf) explicitly
  warns against this. `?keep_remnants` only has any effect when
  `?keep_beams = true`, so it's inert either way here.

<details open>
<summary><strong>❓ Question:</strong></summary>

WHIZARD generates e+e- -> mu+ mu- H directly. Why not e+e- -> Z H with
Z -> mu mu instead — isn't the final state identical?

<details>
<summary><strong>✅ Answer:</strong></summary>

The final state looks the same, but the generator-level parent history
doesn't: in the mu mu H process the two muons' parent particles are the
incoming e+/e-, not a Z boson. This matters downstream once students
truth-match particles in the Analysis stage — don't be surprised the
muons have no Z parent in the event record.

</details>
</details>

## Step 2: Pythia8 - shower, hadronize, decay H -> b b

FCC-ee tooling doesn't call Pythia8 as a bare standalone binary — it goes
through [Gaudi](https://gitlab.cern.ch/gaudi/Gaudi), the component-based
software framework (originally from LHCb/ATLAS, now widely reused across
HEP) that Key4hep is built on. Gaudi programs are assembled from
Algorithms, Tools, and Services wired together in a Python "steering
script"; `k4run` is Key4hep's command-line tool for running these scripts.
Here that means the Gaudi components in
[`key4hep/k4Gen`](https://github.com/key4hep/k4Gen) (`PythiaInterface` +
`GenAlg`) — the same framework used later for Delphes in `Sim/ee`.
(`Analysis`, further downstream, uses
[FCCAnalyses](https://github.com/HEP-FCC/FCCAnalyses) instead, run via its
own `fccanalysis` command rather than `k4run`/Gaudi — it connects to this
chain only via the shared EDM4hep file format, not the framework.)
`PythiaInterface` reads a `.cmd` card, which can point at an external LHE
file, as in `k4Gen`'s own
[`data/Pythia_LHEinput.cmd`](https://github.com/key4hep/k4Gen/blob/main/k4Gen/data/Pythia_LHEinput.cmd)
example.

The card, [`mumuH_Hbb.cmd`](mumuH_Hbb.cmd):

```
! Reads the WHIZARD LHE output from Step 1 and forces H -> b b. Vertex/time
! smearing is done separately in the Gaudi steering script
! (pythia_gen.py), not here.

! Read in the WHIZARD LHEf file
Beams:frameType = 4
Beams:LHEF = mumuH.lhe
Beams:setProductionScalesFromLHEF = off
Beams:allowMomentumSpread = off

! ISR already handled by WHIZARD's isr_handler in Step 1 - keep off here to
! avoid double-counting radiation. FSR stays on (Pythia8 default): per the
! Pythia8 manual's PartonLevel:FSRinResonances flag, this is what actually
! showers the H -> b b decay products before hadronization - with it off,
! b/bbar go straight into string fragmentation with zero shower.
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

<details open>
<summary><strong>❓ Question:</strong></summary>

The card sets `PartonLevel:ISR = off` but leaves `PartonLevel:FSR` on
(Pythia8's default). Shouldn't initial- and final-state radiation be
treated the same way?

<details>
<summary><strong>✅ Answer:</strong></summary>

No — they solve different problems here. WHIZARD's `isr_handler` in
Step 1 already applied the initial-state radiation, as an energy
redistribution on the beam momenta, so Pythia8's own initial-state
shower would double-count it if left on. FSR is different: the LHE
file from Step 1 has the Higgs *undecayed*, and Pythia8's final-state
shower is what both decays H -> b b and showers the resulting b/bbar
before hadronization. Turn it off and the b/bbar go straight into
string fragmentation with zero shower.

</details>
</details>

> **The ISR photon isn't present in the output.** WHIZARD's ISR treatment
> correctly reduces the visible mu mu H system's kinematics to reflect the
> radiated energy (its total energy varies event-by-event, roughly
> 235.5-239.7 GeV instead of a fixed 240, with occasional non-zero net
> transverse momentum), but the radiated photon itself is classified by
> the [WHIZARD manual](https://whizard.hepforge.org/manual.pdf) as a
> beam remnant and — with `?keep_beams = false` — isn't written into the
> event record. This doesn't affect this tutorial's two
> measurements (mu mu recoil mass, H -> b b dijet mass — both driven by
> the visible mu/mu/b/bbar kinematics, which already reflect the
> ISR-induced recoil), but it does mean there's no possibility of
> reconstructing an ISR photon downstream in `Sim/ee`/`Analysis`.

Steering script [`pythia_gen.py`](pythia_gen.py), adapted from
`k4Gen`'s own
[`options/pythia.py`](https://github.com/key4hep/k4Gen/blob/main/k4Gen/options/pythia.py)
example — reads the card above and writes
[EDM4hep](https://github.com/key4hep/EDM4hep) rather than plain HepMC.
EDM4hep is Key4hep's common Event Data Model: a shared, columnar data
format (built on [Podio](https://github.com/AIDASoft/podio)) for storing
particles, hits, tracks, and reconstructed objects, so that generation,
simulation, reconstruction, and analysis stages can all read and write the
same files instead of each using their own custom format — it's what lets
`Sim/ee` and `Analysis` consume this stage's output directly. Plain HepMC
is used only for debugging (`HepMCFileWriter`'s own docstring says so, not
event storage). Beamspot vertex/time smearing is applied via the Gaudi
`GaussSmearVertex` tool wired into `GenAlg`, rather than Pythia8's own
`Beams:allowVertexSpread`, which would apply it a second time on top of
this. This script is also reused as-is for the WW/ZZ background samples in
[`backgrounds.md`](backgrounds.md) — the card and output filename are its
only two process-specific lines, both overridable at the command line
(shown below), so one script covers every sample generated this way:

```python
from Gaudi.Configuration import *
from GaudiKernel import SystemOfUnits as units
from edm4hep import labels as e4_labels

from Configurables import EventDataSvc
from k4FWCore import ApplicationMgr, IOSvc
ApplicationMgr().EvtSel = 'NONE'
ApplicationMgr().EvtMax = 1000
ApplicationMgr().ExtSvc += ["RndmGenSvc", EventDataSvc("EventDataSvc")]

# Writes the EventHeader collection (run/event number) expected by
# downstream tools - without it, readers just skip it with a warning, but
# it's cheap to provide and some tools (e.g. Sim/ee's legacy PodioInput)
# look for it.
from Configurables import EventHeaderCreator
eventHeaderCreator = EventHeaderCreator("eventHeaderCreator")
ApplicationMgr().TopAlg += [eventHeaderCreator]

# Beamspot vertex/time smearing (FCC-ee IDEA values), applied consistently
# to every sample generated with this script, via the Gaudi
# VertexSmearingTool rather than each Pythia8 card's own
# Beams:allowVertexSpread (which would either double-apply it, for cards
# that also set their own, or not apply it at all, for cards that don't).
from Configurables import GaussSmearVertex
smeartool = GaussSmearVertex()
smeartool.xVertexSigma = 5.96e-3 * units.mm
smeartool.yVertexSigma = 23.8e-6 * units.mm
smeartool.zVertexSigma = 0.397 * units.mm
smeartool.tVertexSigma = 10.89 * units.mm

# Default: the mumuH_Hbb signal card/output. Override both for other
# samples (e.g. the WW/ZZ backgrounds in backgrounds.md) via k4run's CLI
# property overrides, no file edits needed:
#   k4run pythia_gen.py --Pythia8.PythiaInterface.pythiacard=<card>.cmd \
#                        --IOSvc.Output=<output>.root
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

<details open>
<summary><strong>❓ Question:</strong></summary>

The script sets `pythia8gen.ErrorMax = 20`. What do you think happens if
this were left at Gaudi's default, `ErrorMax = 1`, when generating a
large sample — say 10,000 events?

<details>
<summary><strong>✅ Answer:</strong></summary>

A small fraction of events (roughly 1 in a few thousand) hit a
Pythia8-level failure that retrying doesn't recover from — for example
an energy-momentum conservation check. With `ErrorMax = 1`, a single
such event aborts the *entire* run, not just that one event. A quick
1,000-event test run usually won't hit this at all, which is exactly
why it's easy to miss — the problem only shows up once you actually
generate a realistic number of events. Raising `ErrorMax` lets Gaudi
skip a handful of individually-unrecoverable events and keep going
instead.

</details>
</details>

Copy both files next to the LHE file produced in Step 1 and run:

```bash
cp ../../mumuH_Hbb.cmd ../../pythia_gen.py .
k4run pythia_gen.py
```

This produces `mumuH_Hbb.root`, an EDM4hep file with the showered,
hadronized, H -> b b decayed event record, in an `MCParticles` collection.

`Sim/ee` consumes this file's `MCParticles` collection directly via
`k4SimDelphesAlg` from
[`key4hep/k4SimDelphes`](https://github.com/key4hep/k4SimDelphes) — that
component takes a generic `edm4hep::MCParticleCollection` as input,
independent of how it was produced.

## References

- WHIZARD card this stage's `mumuH.sin` is adapted from:
  [`wzp6_ee_mumuH_Hbb_ecm240.sin`](https://github.com/HEP-FCC/FCC-config/blob/winter2023/FCCee/Generator/Whizard/v3.0.3/wzp6_ee_mumuH_Hbb_ecm240.sin)
  (`FCC-config`, `winter2023` branch — production campaigns live on their
  own branch, not on `main`).
- Pythia8 card this stage's `mumuH_Hbb.cmd` is adapted from:
  [`p8_ee_default.cmd`](https://github.com/HEP-FCC/FCC-config/blob/winter2023/FCCee/Generator/Pythia8/p8_ee_default.cmd)
  (`FCC-config`, `winter2023` branch).
- [WHIZARD manual](https://whizard.hepforge.org/manual.pdf) (covers up to
  v3.4.3).
- [Pythia8 manual](https://pythia.org/manuals/pythia8315/Welcome.html)
  (v8.315, matching the version in the Key4hep stack used here).

## What's next

The showered, H -> b b decayed sample (`mumuH_Hbb.root`) is the input to
Delphes fast simulation with the FCC-ee IDEA card — see `Sim/ee`.

See [`TODO.md`](TODO.md) for open items not yet resolved in this stage,
and [`backgrounds.md`](backgrounds.md) for an optional side task
generating the two largest backgrounds (WW, ZZ).
