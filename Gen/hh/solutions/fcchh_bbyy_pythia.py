"""
Pythia8 showering, starting from an LHE file, integrated in the Key4hep framework.
Reads the LHE-level hard process, showers it with Pythia8 (using a card that
also handles the Higgs decays), and writes the result out in EDM4hep format.
"""

import os
from GaudiKernel import SystemOfUnits as units
from Gaudi.Configuration import *
from edm4hep import labels as e4_labels

from Configurables import EventDataSvc
from k4FWCore import ApplicationMgr, IOSvc
ApplicationMgr().EvtSel = 'NONE'
ApplicationMgr().EvtMax = -1  # -1 = process all events in the LHE file
ApplicationMgr().OutputLevel = INFO
ApplicationMgr().ExtSvc += ["RndmGenSvc", EventDataSvc("EventDataSvc")]

from Configurables import EventHeaderCreator
eventHeaderCreator = EventHeaderCreator(
    "eventHeaderCreator", runNumber=42, eventNumberOffset=0
)
ApplicationMgr().TopAlg += [eventHeaderCreator]

from Configurables import PythiaInterface
pythia8gentool = PythiaInterface()
# Your Pythia card, handling both the LHE input and the Higgs decays.
# Make sure it contains the LHE-reading directives:
#   Beams:frameType = 4
#   Beams:setProductionScalesFromLHEF = off
#   Beams:LHEF = <path to your .lhe file>
pythia8gentool.pythiacard = "tester_pwp8_pp_hh_5f_hhbbyy.cmd"
pythia8gentool.doEvtGenDecays = False
pythia8gentool.printPythiaStatistics = False
pythia8gentool.pythiaExtraSettings = [""]

from Configurables import GenAlg
pythia8gen = GenAlg("Pythia8")
pythia8gen.SignalProvider = pythia8gentool
pythia8gen.hepmc.Path = "hepmc"
ApplicationMgr().TopAlg += [pythia8gen]

from Configurables import HepMCToEDMConverter
hepmc_converter = HepMCToEDMConverter()
hepmc_converter.hepmc.Path = "hepmc"
hepmc_converter.hepmcStatusList = []  # convert particles with all statuses
hepmc_converter.GenParticles.Path = e4_labels.MCParticles
ApplicationMgr().TopAlg += [hepmc_converter]

from Configurables import GenParticleFilter
genfilter = GenParticleFilter("StableParticles")
genfilter.accept = [1]
genfilter.GenParticles.Path = e4_labels.MCParticles
genfilter.GenParticlesFiltered.Path = "MCParticlesStable"
ApplicationMgr().TopAlg += [genfilter]

iosvc = IOSvc()
iosvc.Output = "showered_events.root"
iosvc.outputCommands = ["keep *"]