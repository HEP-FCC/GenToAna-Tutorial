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

[`mumuH_Hbb.cmd`](mumuH_Hbb.cmd) in this directory is based on
[`FCC-config`'s `p8_ee_default.cmd`](https://github.com/HEP-FCC/FCC-config/blob/winter2023/FCCee/Generator/Pythia8/p8_ee_default.cmd)
(`winter2023` branch) — the actual card FCC-config uses to read WHIZARD LHE
output into Pythia8 — with H -> b b decay-forcing added on top. Note
`PartonLevel:ISR/FSR = off`: WHIZARD's `isr_handler` in Step 1 already
generated the initial-state radiation, so leaving Pythia8's own parton-level
ISR/FSR on would double-count it:

```
! Read in the WHIZARD LHEf file
Beams:frameType = 4
Beams:LHEF = mumuH.lhe
Beams:setProductionScalesFromLHEF = off
Beams:allowMomentumSpread = off

! ISR/FSR already handled by WHIZARD's isr_handler in Step 1 - keep off here
! to avoid double-counting radiation in Pythia8's parton-level shower
PartonLevel:ISR = off
PartonLevel:FSR = off

Check:epTolErr = 1e-1
LesHouches:matchInOut = off

! Force H -> b b
25:onMode  = off
25:onIfAny = 5
```

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

## Open TODOs

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
