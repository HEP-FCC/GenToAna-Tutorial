! Based on FCC-config's p8_ee_default.cmd (winter2023 campaign), the actual
! card used to read WHIZARD LHE output into Pythia8, plus H -> b b
! decay-forcing on top. Vertex/time smearing is done separately in the
! Gaudi steering script (pythia_mumuH.py), not here.

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

! No extra long-lived-particle or Bose-Einstein settings here - see
! Gen/ee/README.md's Open TODOs for why: the golden card's MSTJ(22)=4 is
! a geometric (detector-cylinder) decay-vertex cutoff, not a proper-
! lifetime one, and Pythia8's default (off) already matches its practical
! outcome for K_S0/Lambda at these energies. Bose-Einstein correlations
! (golden card's MSTP(151)=1) deliberately left off too - see the same
! section for why.
