## FCC-hh: $gg\to HH\to b\bar{b}\gamma\gamma$ analysis example

Now translate what you learned in the FCC-ee tutorial to build a FCC-hh analysis from scratch. We want to study di-Higgs production in the $b\bar{b}\gamma\gamma$ channel — one of the key channels for measuring the Higgs self-coupling, since the $HH$ production rate is directly sensitive to it.

Like the FCC-ee analysis, this follows a staged pipeline, and you'll implement all three stages yourself:
- **Stage 1** (`analysis_stage1.py`) — object selection, preselection, and filtering down to the relevant branches, producing skimmed ntuples.
- **Final** (`analysis_final.py`) — add process metadata (cross sections, luminosity scaling), define the signal region via a set of cuts, and produce histograms.
- **Plots** (`analysis_plots.py`) — produce the final comparison plots across your defined selections.

Think about which objects you'd need to select, and which observables you'd want to build, in order to eventually measure the signal strength of this process. Skeletons for all three stages are provided, with comments outlining what to implement. Fill them in and run each in turn:
```bash
fccanalysis run analysis_stage1.py
fccanalysis final analysis_final.py
fccanalysis plots analysis_plots.py
```

> <details><summary><strong>💡 Hint</strong></summary>
> <br>
> Look at the <code>AnalysisFCChh</code> analyser for helper functions to sort collections by pT and to build/merge particle pairs.
> </details>

> <details><summary><strong>✅ Solution</strong></summary>
> <br>
>
> ```bash
> fccanalysis run solutions/analysis_stage1.py
> fccanalysis final solutions/analysis_final.py
> fccanalysis plots solutions/analysis_plots.py
> ```
> </details>
>
>

If you have more time, you can think about which backgrounds would be relevant in the $b\bar{b}\gamma\gamma$ analysis and try to find the centrally produced samples for them in order to include them in the analysis here, since the example solutions only analyse the signal process. Or you can move on to the more advanced task below. 

### Optional advanced task: Measure b-tagging efficiency and compare to the card

The Delphes card's `BTagging` module doesn't actually simulate b-tagging. It applies a parametrized efficiency formula, tagging each jet with a probability drawn from that formula based on its true flavour, $p_T$, and $\eta$. In this task asks we want to extract that efficiency back out of the simulated sample, and check that it matches what the card declared.

**Steps:**
1. Find the `BTagging` module in the FCC-hh scenario II card, and note down its `EfficiencyFormula` for b-jets (PDG code 5) at the working point you're using (loose/medium/tight — see the bit convention from earlier).
2. In your Stage 1 analysis, gen-match your jets to true b-quarks. Look for a helper function in the `AnalysisFCChh` analyser for this, you can check its header for something along the lines of a reco-gen-matching function.
3. For each $p_T$ bin, compute:
   - **Denominator**: number of jets gen-matched to a true b-quark (regardless of whether they got tagged).
   - **Numerator**: the subset of those that *also* pass the b-tag requirement at your chosen working point.
   - **Efficiency** = numerator / denominator, with a binomial uncertainty (this is exactly what `ROOT.TEfficiency` computes for you, as used in `plot_tag_eff.py`).
4. Overlay your measured efficiency-vs-$p_T$ curve against the formula from step 1 — do they agree?

> <details><summary><strong>💡 Hint</strong></summary>
> <br>
> A helper plotting script (<code>plot_tag_eff.py</code>) is provided. You'll mainly need to add the gen-matching step in your Stage 1 analysis to produce the branches it expects.
> </details>

> <details><summary><strong>✅ Solution</strong></summary>
> <br>
>
> ```bash
> fccanalysis run solutions/analysis_stage1_tagEff.py
> python solutions/plot_tag_eff.py -i outputs/FCChh/ggHH_bbyy/nosel/pwp8_pp_hh_5f_hhbbyy.root -o outputs/plots_tag_eff
> ```
> </details>