## Showering the LHE events with Gaudi (FCC-hh)

Now translate what you learned in the FCC-ee tutorial to shower and simulate FCC-hh events yourself. We start one step later than the very beginning of the chain: rather than generating the hard process from scratch, you're given a provided LHE file already containing $gg\to HH$ events at parton level, and pick up from the showering step onward. We follow the same showering + Delphes chain you already built for FCC-ee. Since we specifically want the $b\bar{b}\gamma\gamma$ final state, we also need to force each Higgs to decay via a different channel.

### Task 0: Inspect the LHE file directly

An LHE file is just a plain text file (it's XML-based), so you don't need any special tool to look at it — a simple `less`, `head`, or `grep` will do. You can find the tester file provided for this tutorial in 

```
/eos/project/f/fccsw-web/www/tutorials/gen-to-ana/bnl-cern-2026/gen/pw_pp_ggHH/ggHH_events_000068811.lhe
```

> <details open>
> <summary><strong>❓ Question:</strong></summary>
> <br>
> Open the provided LHE file directly and find: how many events does it contain, at what center-of-mass energy was it generated, and with which generator?
> </details>

> <details><summary><strong>💡 Hint</strong></summary>
> <br>
> Look near the top of the file, inside the header block — generator information and run parameters are typically recorded there as comments or in an init block, before the actual event records begin.
> </details>

### Task 1: Shower the LHE file with Gaudi

Write your own Gaudi steering script to shower this LHE file with `Pythia8` and produce an `EDM4hep` output file by translating what you already did in the FCC-ee Gen part of this tutorial.

You can either write your own Pythia8 `.cmd` card from scratch, or use the one provided in `solutions/`. Either way, your card needs to do two things beyond the usual settings: tell `Pythia8` to read from the LHE file rather than generating its own hard process, and force the two Higgs bosons to decay exclusively into bb and gamma-gamma — one each, not both the same way.

> <details open>
> <summary><strong>❓ Question:</strong></summary>
> <br>
> Adapt your Gaudi steering script from the FCC-ee tutorial to shower the provided LHE file, and configure the Pythia8 card (your own, or the provided one) to exclusively select H to bb, H to gamma-gamma decays.
> </details>

> <details><summary><strong>💡 Hint</strong></summary>
> <br>
> Simply enabling both the bb and gamma-gamma Higgs decay channels isn't enough on its own — with two Higgs bosons in the event, each one can independently decay either way, so you'd also get HH to bbbb and HH to gamma-gamma-gamma-gamma events mixed in. To force exactly one Higgs to decay each way, you need Pythia8's resonance decay filtering machinery (<code>ResonanceDecayFilter</code>), which lets you specify the exact combined set of decay products you want across all matching resonances in the event, rather than just enabling channels per-particle.
> <br><br>
> Showering the full LHE file can take a while — feel free to restrict yourself to 1000 events or fewer while testing.
> </details>

> <details><summary><strong>✅ Solution</strong></summary>
> <br>
>
> ```bash
> k4run solutions/fcchh_bbyy_pythia.py -n 1000
> ```
> </details>