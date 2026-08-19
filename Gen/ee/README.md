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
?keep_beams    = true
?keep_remnants = true

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

[`mumuH_Hbb.cmd`](mumuH_Hbb.cmd) in this directory combines that LHE-reading
pattern with the H -> b b decay-forcing settings from
[`FCC-config`'s `p8_ee_H_Hbb_ecm125.cmd`](https://github.com/HEP-FCC/FCC-config/blob/main/FCCee/Generator/Pythia8/p8_ee_H_Hbb_ecm125.cmd):

```
! Read in the WHIZARD LHEf file
Beams:frameType = 4
Beams:LHEF = mumuH.lhe

! Force H -> b b
25:onMode  = off
25:onIfAny = 5
```

Steering script [`pythia_mumuH.py`](pythia_mumuH.py), adapted from `k4Gen`'s
own
[`options/pythia.py`](https://github.com/key4hep/k4Gen/blob/main/k4Gen/options/pythia.py)
example — swap in the LHE-reading card above and write out EDM4hep rather
than plain HepMC (`HepMCFileWriter`'s own docstring says it's for debugging,
not for actual event storage):

```python
from Gaudi.Configuration import *
from edm4hep import labels as e4_labels

from Configurables import EventDataSvc
from k4FWCore import ApplicationMgr, IOSvc
ApplicationMgr().EvtSel = 'NONE'
ApplicationMgr().EvtMax = 1000
ApplicationMgr().ExtSvc += ["RndmGenSvc", EventDataSvc("EventDataSvc")]

from Configurables import PythiaInterface
pythia8gentool = PythiaInterface()
pythia8gentool.pythiacard = "mumuH_Hbb.cmd"

from Configurables import GenAlg
pythia8gen = GenAlg("Pythia8")
pythia8gen.SignalProvider = pythia8gentool
pythia8gen.hepmc.Path = "hepmc"
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

## What's next

The showered, H -> b b decayed sample (`mumuH_Hbb.root`) is the input to
Delphes fast simulation with the FCC-ee IDEA card — see `Sim/ee`.
