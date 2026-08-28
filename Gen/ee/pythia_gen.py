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
