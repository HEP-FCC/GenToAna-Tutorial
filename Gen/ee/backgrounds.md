# Gen - FCC-ee: Side task - generating the two largest backgrounds

The two largest Standard Model backgrounds to the mumuH signal are
e+e- -> WW and e+e- -> ZZ (diboson) production. Unlike the signal, these
don't need WHIZARD: Pythia8 can generate the hard process itself directly,
so this is a single Pythia8 step with no LHE file involved at all.

Both reuse the signal's [`pythia_gen.py`](pythia_gen.py) steering script
as-is — only the card and output filename change, and both are overridable
at the command line via `k4run`'s property overrides, so no file edits or
extra scripts are needed.

## WW

[`p8_ee_WW_ecm240.cmd`](p8_ee_WW_ecm240.cmd) turns on Pythia8's own
`WeakDoubleBoson:ffbar2WW` process at 240 GeV. Vertex/time smearing is
*not* done in the card (its own `Beams:allowVertexSpread` is left off);
`pythia_gen.py` applies the same Gaudi `GaussSmearVertex` tool and FCC-ee
IDEA values used for the signal instead — so smearing is consistent across
signal and backgrounds, rather than each card using its own values (see
the note below on what those original per-card values were).

```bash
mkdir -p test_whizard/WW && cd test_whizard/WW
cp ../../p8_ee_WW_ecm240.cmd ../../pythia_gen.py .
k4run pythia_gen.py --Pythia8.PythiaInterface.pythiacard=p8_ee_WW_ecm240.cmd --IOSvc.Output=WW.root
```

This produces `WW.root`, an EDM4hep file with 1000 W+W- events (real
`MCParticles`, e.g. semileptonic and hadronic W decays).

## ZZ

[`p8_ee_ZZ_ecm240.cmd`](p8_ee_ZZ_ecm240.cmd) is the same idea, turning on
`WeakDoubleBoson:ffbar2gmZgmZ` instead (the general neutral electroweak
diboson process — dominated by ZZ away from resonance, but also including
some gamma*/Z interference, hence the setting name):

```bash
mkdir -p test_whizard/ZZ && cd test_whizard/ZZ
cp ../../p8_ee_ZZ_ecm240.cmd ../../pythia_gen.py .
k4run pythia_gen.py --Pythia8.PythiaInterface.pythiacard=p8_ee_ZZ_ecm240.cmd --IOSvc.Output=ZZ.root
```

This produces `ZZ.root`, 1000 ZZ events.

## Note on beamspot values

The original FCC-config cards' own vertex-smearing values
(`Beams:sigmaVertexX = 9.80e-3`, `sigmaVertexY = 25.4e-6`,
`sigmaVertexZ = 0.64`, all mm) differ from the ones used for the signal
(`xVertexSigma = 5.96e-3`, `yVertexSigma = 23.8e-6`, `zVertexSigma = 0.397`,
mm) — a real inconsistency between these reference cards in FCC-config
itself. Resolved here by dropping each card's own smearing and using the
signal's values everywhere via the Gaudi tool instead, rather than picking
one of two inconsistent per-process values arbitrarily.

## References

- WW card: [`p8_ee_WW_ecm240.cmd`](https://github.com/HEP-FCC/FCC-config/blob/winter2023/FCCee/Generator/Pythia8/p8_ee_WW_ecm240.cmd)
  (`FCC-config`, `winter2023` branch).
- ZZ card: [`p8_ee_ZZ_ecm240.cmd`](https://github.com/HEP-FCC/FCC-config/blob/winter2023/FCCee/Generator/Pythia8/p8_ee_ZZ_ecm240.cmd)
  (`FCC-config`, `winter2023` branch).
