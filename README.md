# GenToAna Tutorial

FCC tutorial covering the full chain from event **Gen**eration through
Fast/Parametric **S**imulation (Delphes) to physics **Ana**lysis.

## Physics case

- **FCC-ee (full path):** e+e- -> mu mu H, H -> b b (WHIZARD + Pythia + Delphes IDEA card),
  analysed as Z(-> mu mu) H with a recoil-mass measurement and a H -> bb dijet mass.
- **FCC-hh (shorter, advanced transfer):** HH -> b b gamma gamma, reusing the FCC-ee
  material with less hand-holding, extending the physics objects covered to photons.

## Structure

Each stage has its own top-level directory, split by collider, with a
solutions subfolder nested inside each collider's folder:

```
Gen/
  ee/            FCC-ee generation (WHIZARD -> HEPMC) and showering/decay (Pythia)
    solutions/   Worked solution, for offline use
  hh/            FCC-hh generation, starting from existing LHE
    solutions/
Sim/
  ee/            Delphes fast simulation, FCC-ee IDEA card
    solutions/
  hh/            Delphes fast simulation, FCC-hh card
    solutions/
Analysis/
  ee/            Stage1 (tagger + ntuple production) and Stage2 (selections/plots) for FCC-ee
    solutions/
  hh/            Stage1/Stage2 for FCC-hh
    solutions/
```

## Format

Each section is introduced with brief slides, then students work through the
markdown material directly in this repo (VSCode + extensions recommended for an
all-in-one setup). Students present their solutions; reference solutions are
also provided here for offline use.

## Branches

Specific schools/dates are tracked as branches or tags off `main`.

## Status

Scaffolding stage — material to be filled in per stage. See internal planning
notes for owners and open questions (samples to regenerate, possible `combine`
fit as an optional extension, tagger material, Z-Builder update).
