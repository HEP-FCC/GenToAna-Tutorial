! Based on FCC-config's p8_ee_default.cmd (winter2023 campaign), the actual
! card used to read WHIZARD LHE output into Pythia8, plus H -> b b
! decay-forcing on top. Vertex/time smearing is done separately in the
! Gaudi steering script (pythia_mumuH.py), not here.

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
