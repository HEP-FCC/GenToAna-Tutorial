from Gaudi.Configuration import *
from Configurables import k4DataSvc, PodioInput, PodioOutput
from k4FWCore import ApplicationMgr

# Uses the deprecated PodioInput/PodioOutput/k4DataSvc (not IOSvc) - see
# Gen/ee/README.md's Status callout for why: k4SimDelphesAlg crashes with
# IOSvc on the pinned -r 2026-04-08 release, but works with this older,
# still-functional path. Switch to IOSvc (see delphes_mumuH_iosvc.py) once
# the pinned release moves past k4simdelphes v00-08.
podioevent = k4DataSvc("EventDataSvc")
podioevent.input = "/eos/project/f/fccsw-web/www/tutorials/gen-to-ana/bnl-cern-2026/gen/wzp8_ee_mumuH_Hbb_ecm240/wzp8_ee_mumuH_Hbb_ecm240.edm4hep.root"

inp = PodioInput("InputReader")
inp.collections = ["MCParticles", "EventHeader"]

from Configurables import k4SimDelphesAlg
delphesalg = k4SimDelphesAlg()
delphesalg.DelphesCard = "./solutions/delphes_card_IDEA_allMuons.tcl"
delphesalg.DelphesOutputSettings = "./solutions/edm4hep_IDEA_allMuons.tcl"
delphesalg.GenParticles.Path = "MCParticles"

out = PodioOutput("OutputWriter")
out.filename = "mumuH_delphes_IDEA_allMuons.edm4hep.root"
out.outputCommands = ["keep *"]

ApplicationMgr(TopAlg=[inp, delphesalg, out],
               EvtSel="NONE",
               EvtMax=-1,
               ExtSvc=[podioevent],
               OutputLevel=INFO)
