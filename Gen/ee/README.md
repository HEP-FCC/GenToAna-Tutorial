# FCC-ee: Event generation

In this tutorial section we will illustrate how to generate events using
Key4hep software stack and FCC infrastructure build around it. MC generator
WHIZARD generates the hard process $e^{+}e^{-} \rightarrow \mu^{+} \mu^{-} H$,
then Pythia8 showers, hadronizes, and decays $H \rightarrow b \bar{b}$.


## Environment setup

Everything needed (WHIZARD, Pythia8, the Key4hep/Gaudi tools) comes from the
[Key4hep](https://key4hep.github.io/key4hep-doc/) stack, which is a shared
software stack for generation, simulation, reconstruction, and analysis,
developed jointly across several future-collider projects (FCC, EIC, CEPC, ILC)
so they don't each maintain their own separate framework:

```bash
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2026-04-08
```

This tutorial is pinned to the `2026-04-08` release, to see all available
stacks use plain `-r` parameter. This tutorial should also work in the latest
Key4hep stack which you can get by running:
```bash
source /cvmfs/sw.hsf.org/key4hep/setup.sh
```

> Notes:
> 1. Key4hep only supports Bash shell at the moment.
>
> 2. Apart from AlmaLinux 9, Key4hep stack also supports Ubuntu 24.04 and/or
>    26.04.
>
> 3. There is also `/cvmfs/fcc.cern.ch/sw/latest/setup.sh` setup script, which
>    provides the same Key4hep stack plus FCC-specific tools on top.

Key4hep bundles also other $e^{+}e^{-}$ capable event generators, not just
WHIZARD (a multi-particle matrix-element generator with automated NLO
capabilities) and Pythia8 (general-purpose parton shower, hadronization, and
decay generator, also capable of generating simple hard processes directly):
also Herwig 7 (general-purpose, with its own angular-ordered shower and cluster
hadronization model), Sherpa (general-purpose, known for automated multi-jet
merging), KKMCee (precision QED processes like Bhabha scattering and muon
pairs), MadGraph5_aMC@NLO (automated LO/NLO matrix-element generator across many
SM/BSM processes), and EvtGen (heavy-flavour hadron decays).

WHIZARD is used for this signal process because it computes the full $e^{+}e^{-}
\rightarrow \mu^{+} \mu^{-} H$ matrix element directly, with correct
multi-particle kinematics and spin correlations — other generators are better
suited to other processes (e.g. KKMCee for high-precision QED benchmarks).


## Step 1: WHIZARD - hard process

Check whether WHIZARD is available (and, via its path, that the right stack
release was sourced) and see its version:

```bash
which whizard
whizard --version
```

WHIZARD has no complete, supported interface to Pythia8 — only to the
legacy PYTHIA6 (see the
[WHIZARD manual](https://whizard.hepforge.org/manual.pdf)). So this step
only generates the hard process and writes it out as LHEf file format;
showering, hadronization, and the $H \rightarrow b \bar{b}$ decay all happen
as an explicit separate step in Pythia8 (Step 2 below), rather than inside
WHIZARD itself.

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

# Configure the precision of matrix element integration
integrate (mumuH) { iterations = 10:100000:"gw", 5:200000:"" }
# Faster, lower-precision alternative for quick iteration/testing:
# integrate (mumuH) { iterations = 3:2000:"gw" }

# Generate a few more events than Step 2 actually reads (EvtMax = 10000
# there), to make sure it has enough events despite a few failures.
n_events = 10020

# Select which output format and its version to use
$lhef_version  = "3.0"
sample_format  = lhef
simulate (mumuH) { $sample = "mumuH" }
```

Run it in its own directory, as WHIZARD produces a lot of additional helper
files:

```bash
mkdir -p test_whizard/mumuH && cd test_whizard/mumuH
cp ../../mumuH.sin .
whizard mumuH.sin
```

This produces `mumuH.lhe`.

> **Note:** WHIZARD also computes and prints the process cross-section
> during the `integrate` step above — look for the `Integral[fb]`/
> `Error[fb]` columns in the last combined row of the iteration table
> (also echoed in the generated `mumuH.log` file). This is the
> cross-section for the exact final state computed here
> ($e^{+}e^{-} \rightarrow \mu^{+} \mu^{-} H$), not the total $ZH$
> production cross-section — it already includes the
> $Z \rightarrow \mu^{+} \mu^{-}$ branching fraction (~3.37%).

Two settings are deliberately left out rather than pinned explicitly,
relying on their WHIZARD defaults:

> Notes:
> 1. Higgs mass `mH` is not set, because WHIZARD's `SM` model already defaults
>    it to 125 GeV (`parameter mH = 125` in `SM.mdl`).
> 2. We do not keep beam and beam remnants particles, as writing the original
>    beam particles into the LHE record as extra entries breaks reading the
>    file into Pythia8 downstream, see
>    [WHIZARD manual](https://whizard.hepforge.org/manual.pdf).

<details open>
<summary><strong>❓ Question:</strong></summary>

WHIZARD generates $e^{+}e^{-} \rightarrow \mu^{+} \mu^{-} H$ directly. Why
not $e^{+}e^{-} \rightarrow Z H$ with $Z \rightarrow \mu^{+} \mu^{-}$
instead — isn't the final state identical?

<details>
<summary><strong>✅ Answer:</strong></summary>

WHIZARD computes the complete matrix element for the exact final state
directly, rather than treating it as production ($e^{+}e^{-} \rightarrow Z
H$) followed by a separate, on-shell $Z \rightarrow \mu^{+} \mu^{-}$
decay. WHIZARD does support that factorized "cascade decay" mode too, and
it can retain full spin correlations between production and decay, but it
still restricts the intermediate boson to being on-shell, discarding the
true Breit-Wigner off-shell tails and any other diagrams contributing to
the same final state that don't proceed through that resonance ([WHIZARD
reference paper](https://arxiv.org/abs/0708.4233), Section 6.6). At
$\sqrt{s} = 240$ GeV there's only about 24 GeV of phase space left over the
$H + Z$ mass threshold, so the $Z$'s few-GeV width has a non-negligible
effect on the exact lineshape.

</details>
</details>


## Step 2: Pythia8 - shower, hadronize, decay $H \rightarrow b \bar{b}$

Key4hep tooling doesn't provide Pythia8 as a bare standalone binary, instead
it wraps it into a [Gaudi](https://gitlab.cern.ch/gaudi/Gaudi) algorithm. Gaudi
is a component-based software framework (originally from LHCb/ATLAS, now widely
reused across HEP) that Key4hep is built on. Gaudi programs are assembled from
Algorithms, Tools, and Services wired together in a Python "steering
script"; `k4run` is Key4hep's command-line tool for running these scripts.

> Notes:
> 1. To get a list of all available commandline arguments which one can use to
>    adjust the steering script use:
>    ```bash
>    k4run steering_script.py --help
>    ```
> 2. Gaudi components of the Key4hep ecosystem are spread through many
>    packages, here we primarily use the Gaudi components from
>    [`key4hep/k4Gen`](https://github.com/key4hep/k4Gen) (`PythiaInterface` +
>    `GenAlg`).
> 3. To check that a steering script is valid without actually running the
>    job (parses the config, wires up components, but generates no events),
>    use:
>    ```bash
>    k4run steering_script.py --dry-run
>    ```

`PythiaInterface` reads a `.cmd` card, which can point at an external LHEf
file. The card to decay the Higgs into $b\bar{b}$ pair, hadronizes and does the
showering looks like this [`mumuH_Hbb.cmd`](mumuH_Hbb.cmd):

```
! Reads the WHIZARD LHEf output from Step 1 and forces H -> b b. Vertex/time
! smearing is done separately in the Gaudi steering script
! (pythia_gen.py), not here.

! Read in the WHIZARD LHEf file
Beams:frameType = 4
Beams:LHEF = mumuH.lhe
Beams:setProductionScalesFromLHEF = off
Beams:allowMomentumSpread = off

! Keep initial state radiation off.
PartonLevel:ISR = off

Check:epTolErr = 1e-1
LesHouches:matchInOut = off

! Force H -> b b
25:onMode  = off
25:onIfAny = 5
```

<details open>
<summary><strong>❓ Question:</strong></summary>

The card sets `PartonLevel:ISR = off` but leaves `PartonLevel:FSR` on
(Pythia8's default). Shouldn't initial- and final-state radiation be
treated the same way?

<details>
<summary><strong>✅ Answer:</strong></summary>

Since we turn on WHIZARD's `isr_handler` in Step 1. It already applied the
initial-state radiation, as an energy redistribution on the beam momenta, so
Pythia8's own initial-state shower would double-count it if left on. FSR is
different: the LHE file from Step 1 has the Higgs *undecayed*, and Pythia8's
final-state shower is what both decays $H \rightarrow b \bar{b}$ and showers the
resulting $b/\bar{b}$ before hadronization. Turn it off and the $b/\bar{b}$ go
straight into string fragmentation with zero shower.

</details>
</details>

Steering script [`pythia_gen.py`](pythia_gen.py) reads the card above. No
HepMC file is ever written to disk here: `GenAlg` writes the
Pythia8-generated event into Gaudi's in-memory transient event store and
`HepMCToEDMConverter` immediately reads it from there and converts it, within
the same job, to [EDM4hep](https://github.com/key4hep/EDM4hep) — the only thing
actually written to disk is the final EDM4hep ROOT file.
EDM4hep is Key4hep's common Event Data Model: a shared, columnar data
format (built on [Podio](https://github.com/AIDASoft/podio)) for storing
particles, hits, tracks, and reconstructed objects, so that generation,
simulation, reconstruction, and analysis stages can all read and write the
same files instead of each using their own custom format — it's what lets
[`Sim/ee`](../../Sim/ee/README.md) and `Analysis` consume this stage's output
directly.

A physical on-disk HepMC3 file could instead be produced via `k4Gen`'s
`HepMCFileWriter`, useful for debugging, but isn't used in this flow.
Beamspot vertex/time smearing is applied via the Gaudi `GaussSmearVertex` tool
wired into `GenAlg`, rather than Pythia8's own `Beams:allowVertexSpread`, which
would apply it a second time on top of this.

This script is also reused as-is for the WW/ZZ background samples in
[`solutions/backgrounds.md`](solutions/backgrounds.md) — the card and output filename are its
only two process-specific lines, both overridable at the command line
(shown below), so one script covers every sample generated this way:

```python
from Gaudi.Configuration import *
from GaudiKernel import SystemOfUnits as units
from edm4hep import labels as e4_labels

from Configurables import EventDataSvc
from k4FWCore import ApplicationMgr, IOSvc
ApplicationMgr().EvtSel = 'NONE'
ApplicationMgr().EvtMax = 10000
ApplicationMgr().ExtSvc += ["RndmGenSvc", EventDataSvc("EventDataSvc")]

# Writes the EventHeader collection (run/event number) expected by
# downstream tools.
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

# Default: the mumuH_Hbb signal card. Can be overridden via k4run's CLI
# property overrides, no file edits needed:
#   k4run pythia_gen.py --Pythia8.PythiaInterface.pythiacard=<card>.cmd
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
# means a single such event aborts the whole run. ErrorMax = 20 lets a
# handful be skipped instead.
pythia8gen.ErrorMax = 20
ApplicationMgr().TopAlg += [pythia8gen]

from Configurables import HepMCToEDMConverter
hepmc_converter = HepMCToEDMConverter()
hepmc_converter.hepmc.Path = "hepmc"
hepmc_converter.hepmcStatusList = []
hepmc_converter.GenParticles.Path = e4_labels.MCParticles
ApplicationMgr().TopAlg += [hepmc_converter]

iosvc = IOSvc()
# Output location can be overridden via:
#   k4run pythia_gen.py --IOSvc.Output=<output>.root
iosvc.Output = "mumuH_Hbb.root"
```

<details open>
<summary><strong>❓ Question:</strong></summary>

The script sets `pythia8gen.ErrorMax = 20`. What do you think would happen
at this stage's actual sample size (10,000 events) if this were left at
Gaudi's default, `ErrorMax = 1`?

<details>
<summary><strong>✅ Answer:</strong></summary>

A small fraction of events (roughly 1 in a few thousand) hit a Pythia8-level
failure that retrying doesn't recover from — for example an energy-momentum
conservation check. With `ErrorMax = 1`, a single such event aborts the *entire*
run, not just that one event. Raising `ErrorMax` lets Gaudi skip a handful of
individually-unrecoverable events and keep going instead.

</details>
</details>

> **Note:** Gaudi itself flags `ErrorMax` as `[[deprecated]]` (a warning
> appears at run time), but as of this Key4hep release there's no
> replacement — the property is still fully functional under the hood, so
> this tutorial keeps using it as-is until a better alternative exists.

Copy both files next to the LHEf file produced in Step 1 and run:

```bash
cp ../../mumuH_Hbb.cmd ../../pythia_gen.py .
k4run pythia_gen.py
```

This produces `mumuH_Hbb.root`, an EDM4hep file with the showered,
hadronized, $H \rightarrow b \bar{b}$ decayed event record, in an
`MCParticles` collection.

[`Sim/ee`](../../Sim/ee/README.md) consumes this file's `MCParticles` collection directly via
`k4SimDelphesAlg` from
[`key4hep/k4SimDelphes`](https://github.com/key4hep/k4SimDelphes), which takes
a generic `edm4hep::MCParticleCollection` as input, independent of how it was
produced.


## Side task: background samples

The two largest backgrounds to the mumuH signal, $e^{+}e^{-} \rightarrow WW$ and
$e^{+}e^{-} \rightarrow ZZ$, can optionally be generated the same way as Step 2
— reusing `pythia_gen.py` with a different card, no WHIZARD step needed since
Pythia8 generates these hard processes itself. See
[`solutions/backgrounds.md`](solutions/backgrounds.md) for the walkthrough; the
cards themselves are also in [`solutions/`](solutions) folder.

## What's next

The showered, $H \rightarrow b \bar{b}$ decayed sample (`mumuH_Hbb.root`) is the
input to Delphes parametrized fast simulation with the FCC-ee IDEA card — see
[`Sim/ee`](../../Sim/ee/README.md).

To graphically explore the relationships between the `MCParticles` in this
output (parent/child links, decay trees), see the
[eedE (EDM4hep Event Data Explorer) tutorial](https://hep-fcc.github.io/fcc-tutorials/main/2-gen-and-fastsim/2-4-eedE/README.html).


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
- [WHIZARD reference paper](https://arxiv.org/abs/0708.4233) (Kilian, Ohl,
  Reuter — describes cascade decays vs. complete matrix elements, and spin
  correlations, in Section 6.6).
- [Pythia8 manual](https://pythia.org/manuals/pythia8315/Welcome.html)
  (v8.315, matching the version in the Key4hep stack used here).
