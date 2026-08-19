# Analysis - FCC-ee

Staged FCCAnalyses analysis (from stack, no local compilation) on the
Delphes output from `Sim/ee`.

- **Stage1:** custom analyser header, runs the jet tagger, outputs a flat
  ROOT ntuple.
- **Stage2:** template script — inspect the Stage1 variables, then add
  selections to produce the recoil-mass (mu mu) and m_jj (H -> b b) plots.
