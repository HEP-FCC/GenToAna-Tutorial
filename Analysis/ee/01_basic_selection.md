# Stage 1: reconstructing $e^+e^- \to Z(\mu^+\mu^-)H(b\bar b)$ candidates

This chapter accompanies [`01_basic_selection.py`](01_basic_selection.py).

## Goal of this stage

Stage 1 reads reconstructed EDM4hep events, selects muons, builds a $Z\to\mu^+\mu^-$ candidate, and clusters the remaining particles into two jets. It also runs the flavour tagger and writes the resulting observables to a compact ROOT ntuple with one row per selected event.

The analysis searches for the Higgs signal through two complementary quantities: the invariant mass of the system recoiling against the dimuon candidate and the invariant mass of the two jets assigned to the $H\to b\bar b$ candidate. Both should peak near the Higgs mass for signal events, while relying on different reconstructed parts of the event.

The main data flow is:

```text
reconstructed particles
        |
        +--> select muons --> build Z candidate --> recoil observables
        |
        +--> remove selected muons --> cluster two jets --> flavour tagging --> dijet observables
```

Stage 1 deliberately performs only a loose event selection. You can then inspect the resulting distributions before choosing tighter cuts in the next stage.

## Imports and flavour-tagging model

The script begins with a few standard Python modules and two FCCAnalyses
helpers:

```python
import json
import os
import urllib.request

from addons.FastJet.jetClusteringHelper import ExclusiveJetClusteringHelper
from addons.ONNXRuntime.jetFlavourHelper import JetFlavourHelper
```

`ExclusiveJetClusteringHelper` clusters reconstructed particles into a fixed
number of jets. `JetFlavourHelper` prepares the constituent-level inputs for a
neural network and runs the inference using the provided ONNX model.

The model is identified by a name and two possible locations:

```python
MODEL_NAME = "fccee_flavtagging_edm4hep_wc_v1"
MODEL_URL_DIR = "https://.../winter2023/wc_pt_13_01_2022"
MODEL_EOS_DIR = "/eos/experiment/fcc/ee/jet_flavour_tagging/..."
```


The helper function `get_file_path` first looks for the model on the local
filesystem—normally the CERN EOS path—and otherwise downloads it:

```python
if os.path.exists(filename):
    return os.path.abspath(filename)
urllib.request.urlretrieve(url, os.path.basename(url))
```

This keeps the analysis convenient on LXPlus while still allowing it to run in
an environment without the EOS model directory.

## Configuring the analysis

FCCAnalyses instantiates the `Analysis` class and calls its constructor before
building the event-processing graph:

```python
class Analysis:
    def __init__(self, _):
```


### Input processes

The latest stable release of FCCAnalyses expects the samples in `process_list`:

```python
self.process_list = {
            "wzp8_ee_mumuH_Hbb_ecm240": {
                "fraction": 1.0,
            },
            "p8_ee_ZZ_mumubb_ecm240": {
                "fraction": 1.0,
            },
            "p8_ee_WW_mumu_ecm240": {
                "fraction": 1.0,
            },
        }
```

A fraction of `1.0` requests the full available sample. The stable release used
in this tutorial also accepts process-specific `input_dir`, `chunks`, and
`output` settings, as shown in the commented lines of the script.

### Input, output, and additional C++ functions

```python
self.input_dir = "./inputs/"
self.output_dir = "./outputs/stage1/"
```
`input_dir` specifies the common parent directory containing the input samples. For every process in `self.process_list`, FCCAnalyses looks for ROOT files in a subdirectory named after the process:
```text
<input_dir>/<process_name>/*.root
```
For example, the input files for the process `wzp8_ee_mumuH_Hbb_ecm240` will be expected beneath `./inputs/wzp8_ee_mumuH_Hbb_ecm240/`.

>  ✏️ **Exercise**
>
> Create the `inputs` directory and the nested sample directories expected by FCCAnalyses. Download each ROOT file into its corresponding sample directory.
> Required samples:
>
> - [p8_ee_WW_mumu_ecm240_edm4hep.root](https://fccsw.web.cern.ch/tutorials/gen-to-ana/bnl-cern-2026/delphes/p8_ee_WW_mumu_ecm240/p8_ee_WW_mumu_ecm240.edm4hep.root)
> - [p8_ee_ZZ_mumubb_ecm240_edm4hep.root](https://fccsw.web.cern.ch/tutorials/gen-to-ana/bnl-cern-2026/delphes/p8_ee_ZZ_mumubb_ecm240/p8_ee_ZZ_mumubb_ecm240.edm4hep.root)
> - [wzp8_ee_mumuH_Hbb_ecm240_edm4hep.root](https://fccsw.web.cern.ch/tutorials/gen-to-ana/bnl-cern-2026/delphes/wzp8_ee_mumuH_Hbb_ecm240/wzp8_ee_mumuH_Hbb_ecm240.edm4hep.root)
>
> The name of each sample directory must exactly match its key in `self.process_list`. A correctly prepared input area will have this structure:
> ```text
> inputs/
> ├── p8_ee_WW_mumu_ecm240/
> │   └── p8_ee_WW_mumu_ecm240.edm4hep.root
> ├── p8_ee_ZZ_mumubb_ecm240/
> │   └── p8_ee_ZZ_mumubb_ecm240.edm4hep.root
> └── wzp8_ee_mumuH_Hbb_ecm240/
>     └── wzp8_ee_mumuH_Hbb_ecm240.edm4hep.root
> ```
> Use shell commands such as `mkdir`, `cd`, and `wget` to construct this structure yourself.

<br>

If you managed to produce your own signal sample in the previous tutorial, feel free to modify the `process_list` accordingly to point to it.

```python
self.include_paths = ["functions.h"]
```

`functions.h` supplies the analysis-specific C++ helpers used below, including muon isolation and $Z$-candidate construction. FCCAnalyses passes headers listed in `self.include_paths` to ROOT’s C++ interpreter, which compiles them just in time and makes their functions available inside RDataFrame expressions such as `Define()` and `Filter()`. This allows analysts to implement performance-critical custom operations in C++ while configuring the analysis workflow in Python.

## Preparing the jet helpers
```python
preproc_url = f"{MODEL_URL_DIR}/{MODEL_NAME}.json"
model_url = f"{MODEL_URL_DIR}/{MODEL_NAME}.onnx"
```


To use the pre-trained neural network to infer the flavour of the jets associated with the Higgs decay, we need the correct configuration and model files. The JSON file describes the model inputs, preprocessing, and output score names. The ONNX file contains the trained neural network itself.

The flavour tagger requires a valid mapping from its configured variable names to the names present in actual EDM4hep collections or analysis columns:

```python
collections = {
    "GenParticles": "Particle",
    "PFParticles": "ReconstructedParticlesNoMuons",
    "PFTracks": "EFlowTrack",
    ...
}
```
*Note: If you are extra curious and inspect the input files, you will notice that `ReconstructedParticlesNoMuons` does not exist yet. It is a new column defined later in `analyzers()` after the selected muons are removed.*



In this case, we cluster the particles remaining after muon removal into exactly two jets, corresponding to the $H\to b\bar b$ signal hypothesis. Therefore, we need to configure the `ExclusiveJetClusteringHelper` accordingly.

>  ✏️ **Exercise**
>
> Check the definition of `ExclusiveJetClusteringHelper` in
> `jetClusteringHelper.py` to determine what the two input arguments need to be.
>
> We want to cluster exactly two jets using all reconstructed particles
> except for the two muons.

```python
self.jet_clustering_helper = ExclusiveJetClusteringHelper(
    FILLME, FILLME
)
```


## Building the analysis graph

The `analyzers()` method receives the event `RDataFrame` and returns the final
node of the stage-1 computation graph.
### Short aliases for EDM4hep relation fields

```python
df = df.Alias("Particle0", "_Particle_daughters.index")
df = df.Alias("Particle1", "_Particle_parents.index")
df = df.Alias("RecoMCLink0", "_RecoMCLink_from.index")
df = df.Alias("RecoMCLink1", "_RecoMCLink_to.index")
df = df.Alias("Muon0", "Muon_objIdx.index")
```

At the EDM4hep level, `Particle`, `RecoMCLink`, and `Muon` describe collections
and relations. The aliases provide shorter names for those fields; they do not copy any data. For example, `Muon0` contains indices pointing to reconstructed particles identified as muon candidates by the reconstruction/PID chain.

### Retrieve and preselect muons

The muon indices are used to retrieve the corresponding objects from the full
reconstructed-particle collection:

```python
df = df.Define(
    "muons_all",
    "FCCAnalyses::ReconstructedParticle::get(Muon0, ReconstructedParticles)",
)
```


>  ✏️ **Exercise**
>
> Create a new column called `muons` that stores all muons with total three-momentum $p>20$ GeV. Hint: Look for the method [`sel_p()`](https://hep-fcc.github.io/FCCAnalyses/doc/latest/functions_s.html) to find out how to do this.

```python
df = df.Define(
    "muons",
    "FCCAnalyses::ReconstructedParticle::FILLME(FILLME)(FILLME)",
)
```

We also define columns containing the charges and number of the selected muons:
```python
q_muons  = get_charge(muons)
no_muons = get_n(muons)
```

### Muon isolation and loose event selection

Prompt muons from $Z\to\mu^+\mu^-$ are normally well isolated from other
particles. The script computes a relative cone-isolation value for every
selected muon:

```python
iso_muons = coneIsolation(0.01, 0.5)(muons, ReconstructedParticles)
```

For each muon, the momenta of reconstructed particles in
$0.01 < \Delta R < 0.5$ are summed and divided by the muon momentum. A small
value therefore represents an isolated muon.

`sel_iso` returns a particle collection containing the muons whose isolation
is below 0.25:

```python
muons_sel_iso = sel_iso(0.25)(muons, iso_muons)
```

The event must contain at least one isolated muon and at least one possible
opposite-sign pair:

```python
df = df.Filter("muons_sel_iso.size() > 0")
df = df.Filter(
    "no_muons >= 2 && abs(Sum(q_muons)) < q_muons.size()"
)
```
### Remove the muons before clustering jets

The selected muons are assigned to the leptonic side of the event and must not
also enter the candidate Higgs jets:

```python
ReconstructedParticlesNoMuons = remove(ReconstructedParticles, muons)
```


### Cluster jets and run flavour tagging

The configured helpers now add their columns to the dataframe:

```python
df = self.jet_clustering_helper.define(df)
df = self.jet_flavour_helper.define(df)
df = self.jet_flavour_helper.inference(
    self.weaver_preproc, self.weaver_model, df
)
```

The clustering helper produces the two jet objects, their assigned
constituents, jet kinematics, and `event_njet`. The flavour helper constructs
track- and constituent-level features. `inference` evaluates the neural
network and adds per-jet scores such as `recojet_isB` and `recojet_isC`.

### Build the $Z\to\mu^+\mu^-$ candidate

If an event has more than one opposite-sign muon pair, the script needs a
single candidate. The candidate builder chooses the pair most compatible with
a $Z$ mass of 91.2 GeV and a recoil mass of 125 GeV:

```python
zbuilder_result = resonanceBuilder_mass_recoil(
    91.2, 125, 0.4, 240, false
)(muons, RecoMCLink0, RecoMCLink1,
  ReconstructedParticles, Particle, Particle0, Particle1)
```

The arguments configure:

| Argument | Meaning |
|---|---|
| `91.2` | Target dimuon mass in GeV |
| `125` | Target recoil mass in GeV |
| `0.4` | Relative weight of the recoil-mass term in the pairing score |
| `240` | Centre-of-mass energy in GeV |
| `false` | Use reconstructed rather than MC-matched muon kinematics |

For each opposite-sign pair, the helper evaluates approximately

$$
0.6\,(m_{\mu\mu}-91.2)^2 + 0.4\,(m_{\mathrm{recoil}}-125)^2
$$

and retains the pair with the smallest value. This chooses among candidates;
it does not impose a mass cut or perform a kinematic fit.

The returned vector has three entries:

```text
zbuilder_result[0]  newly constructed composite Z candidate
zbuilder_result[1]  copy of the first selected reconstructed muon
zbuilder_result[2]  copy of the second selected reconstructed muon
```

Because the current analysis only needs the composite candidate, it wraps the
first entry in a one-element reconstructed-particle collection:

```python
zmumu = Vec_rp{zbuilder_result[0]}
```

### Dimuon and recoil observables

FCCAnalyses property functions return vectors because they operate on particle
collections. Since `zmumu` contains exactly one candidate, `[0]` extracts its
scalar mass and momentum:

```python
m_zmumu = get_mass(zmumu)[0]
p_zmumu = get_p(zmumu)[0]
```

At an $e^+e^-$ collider the initial-state four-vector is known. In the
centre-of-mass frame, neglecting radiation,

$$
p_{e^+e^-} = (\sqrt{s},0,0,0).
$$

The four-vector recoiling against the reconstructed $Z$ is

$$
p_{\mathrm{recoil}} = p_{e^+e^-} - p_{\mu\mu}.
$$

Its invariant mass is

$$
m_{\mathrm{recoil}}^2 = E_{\mathrm{recoil}}^2
                         - |\vec p_{\mathrm{recoil}}|^2.
$$

For a correctly reconstructed $e^+e^-\to ZH$ event, the recoiling system is
the Higgs, so this quantity peaks near $m_H\simeq125$ GeV independently of the
particular Higgs decay mode. Detector resolution, initial-state radiation, and
beam-energy effects broaden the peak.

We therefore create a hypothetical recoil particle for each $Z$ candidate and calculate its mass.

```python
recoil_zmumu = recoilBuilder(240)(zmumu)
m_recoil_zmumu = get_mass(recoil_zmumu)[0]
```

### Dijet mass and the event-level $b$-tagging score

To allow for a selection cut on the output of the jet flavour tagger, we combine the inferred $b$-tagging scores of the two reconstructed jets into a single event discriminant.

```python
scoresum_B = recojet_isB[0] + recojet_isB[1]
```

Signal $H\to b\bar b$ events should tend toward larger values because both
jets are expected to be $b$-like.

Finally, the two jet objects are converted into four-vectors and combined:

```python
df = df.Define(
    "p4_jets",
    "JetConstituentsUtils::compute_tlv_jets("
    f"{self.jet_clustering_helper.jets})",
)
df = df.Define(
    "m_jj",
    "JetConstituentsUtils::InvariantMass(p4_jets[0], p4_jets[1])",
)
```

For signal, `m_jj` should peak near the Higgs mass. It complements the recoil
mass:

- `m_recoil_zmumu` uses the known initial state and the reconstructed $Z$;
- `m_jj` uses the reconstructed Higgs decay products directly.

The selected $Z$ candidate does not enter the dijet-mass calculation itself.
The jets are constructed from the full reconstructed-particle collection after
the selected high-momentum muons have been removed.

## Stage-1 output

The final method lists the columns written to the output ntuple:

```python
branch_list = [
            "m_zmumu",
            "p_zmumu",
            "m_recoil_zmumu",
            "m_jj",
            "scoresum_B",
]
branch_list += self.jet_flavour_helper.outputBranches()
```

The explicit variables describe the $Z$, recoil system, and
Higgs-jet candidate. `outputBranches()` adds the neural-network flavour scores
and selected jet properties.

Intermediate columns such as `muons`, `zbuilder_result`, `recoil_zmumu`, and
`p4_jets` are needed to calculate the output variables but are not themselves
written. This is one of the benefits of the staged approach: the large EDM4hep
event is reduced to a compact, analysis-oriented ntuple.

Once you have replaced all `FILLME`s, run the script:
```bash
fccanalysis run 01_basic_selection.py
```
