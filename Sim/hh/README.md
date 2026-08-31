## Running the Delphes fast simulation with Gaudi for FCC-hh

Now translate what you learned in the FCC-ee Sim tutorial to run the Delphes fast simulation for FCC-hh. The steering file structure is exactly the same as before — the same `podioevent.input`, `delphesalg.DelphesCard`, `delphesalg.DelphesOutputSettings`, `delphesalg.GenParticles.Path`, and `out.filename` parameters you already filled in for FCC-ee — you just need to point them at the right FCC-hh files this time, and use the showered output you produced in the previous step as input.

### Task: Run the FCC-hh fast simulation

> <details open>
> <summary><strong>❓ Question:</strong></summary>
> <br>
> Write a Gaudi steering script to run the Delphes fast simulation on your showered LHE events, using the FCC-hh scenario II detector card.
> </details>

> <details><summary><strong>💡 Hint: finding the Delphes card</strong></summary>
> <br>
> Just like for the IDEA card, the FCC-hh cards come pre-installed with the Key4hep software stack. Look inside <code>$DELPHES_DIR</code> for the available FCC-hh cards, and pick the scenario II one.
> </details>

> <details><summary><strong>💡 Hint: finding the EDM4hep output config</strong></summary>
> <br>
> A baseline EDM4hep output configuration is provided for you — you don't need to write one from scratch. It lives at <code>$K4SIMDELPHES/edm4hep_output_config.tcl</code>.
> </details>

> <details><summary><strong>✅ Solution</strong></summary>
> <br>
>
> ```bash
> k4run solutions/delphes_ggHHbbyy_fcchh_scenarioII.py
> ```
> </details>

If you have time and are interested to learn more about FCC-hh in particular, take a look at the Delphes card for this scenario and compared to the IDEA for FCC-ee detector design. What differences can you spot? 

A reference detector concept for FCC-hh is modelled in this card, which you can see visualized below:

![FCC-hh reference detector concept](https://hep-fcc.github.io/FCChhPhysicsPerformance/images/CDR_detector_concept.png)
*Figure: FCC-hh reference detector concept. Image credit: M. Selvaggi.*

Try to answer the following questions:

> <details open>
> <summary><strong>❓ Questions:</strong></summary>
> <br>
>
> 1. In which η range are we reconstructing muon tracks?
> 2. With which algorithm is the main jet collection (the one used downstream for tagging) built?
> 3. What is the minimum pT of a reconstructed jet?
> 4. Which flavour tagging working points do we define?
> 5. What is the flavour tagging efficiency for a b-jet within |η| < 4.0 and a pT of 250 GeV?
> 6. What is the maximum photon identification efficiency?
>
> <details><summary><strong>✅ Solutions:</strong></summary>
> <br>
>
> 1. Muon tracks are reconstructed up to |η| < 6, cf. l250.
> 2. The main jet collection — the one fed into `JetEnergyScale` and used for flavour tagging downstream — is `FastJetFinder04`: anti-kt (`JetAlgorithm 6`) with R = 0.4, cf. l680-687 and l961f.
> 3. Jets with pT > 25 GeV are reconstructed, l698.
> 4. Three working points — Loose, Medium, Tight — are defined for each of b-tagging, c-tagging, and tau-tagging, cf. l1151, l1202, l1254 (b), l1306, l1340, l1375 (c), and l1411, l1452, l1493 (tau).
> 5. At the medium working point, the b-tagging efficiency in this bin is 83%, cf. l1214.
> 6. The maximum photon identification efficiency is in the bin |η| ≤ 2.5, pT > 10 GeV, and it's around 90% (0.95 × 0.95), cf. l991 and l1002.
>
> </details></details>