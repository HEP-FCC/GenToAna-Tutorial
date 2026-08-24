! Reads the WHIZARD LHE output from Step 1 and forces H -> b b. Vertex/time
! smearing is done separately in the Gaudi steering script
! (pythia_mumuH.py), not here.

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
