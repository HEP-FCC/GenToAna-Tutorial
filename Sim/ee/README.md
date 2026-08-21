# Sim - FCC-ee
<!-- source /cvmfs/sw.hsf.org/key4hep/setup.sh -->

<!-- Delphes fast simulation using the IDEA card, run on the Pythia-showered
HEPMC output from `Gen/ee`. -->

In this part of the tutorial you will learn how to use the common `key4hep` tools for fast, parametrized detector simulation with `Delphes`. ADD LINKS TO MATCHING DOC!
We will use the IDEA detector concept and run on the $ZH$ production events at FCC-ee that you learned how to generate in the previous step. The input files to the simulation are the events after showering and Higgs decay at generation level that you produced, and the output file will contain the same events on reconstruction level. Both files are in `EDM4HEP` format. You will get an overview of how the parametrized detector response simulation works, as well as of the `EDM4HEP` event data model. 

Finally, we will make some simple plots from the `EDM4HEP` we produced. (DO WE KEEP THIS?)

## Running the Delphes fast simulation with Gaudi

Check if you have setup the software stack and the `k4run` executable is available, by running `which k4run`. If this doesn't return a path like `/cvmfs/sw.hsf.org/key4hep/<somewhere>/k4run` please follow the instructions for setting up again (LINK TO BE ADDED).

We will again be using the `Gaudi` approach you learned in the previous part of the tutorial, so we need a steering file to tell it that we want to run Delphes and with which settings. 

A skeleton of such a steering file is provided in `delphes_mumuH_IDEA.py`. You can already take a look into it and try to understand which information we need to fill in in order to make this work yourself. Remember you can use `k4run delphes_mumuH_IDEA.py --help` to get a more detailed description of the config parameters. 

Let us walk-through together the different parameters we have to set in the steering file. 

For the input section we have:
- `podioevent.input` sets the path of the input files, so fill in the location of your output file from the previous step here. 
- `inp.collections` defines the list of collections we want to read from our input. Given that we have only run generation & showering so far, these are simply the the generator level particles written out py `Pythia8`. You can take a look at the content of your produced file with `podio-dump <your_edm4hep_events.root>` to see what collection name you need to fill in here. 

Next, we load and configure the Delphes algorithm we want to run. In particular we use `k4SimDelphesAlg`, this is an implementation of Delphes in the key4hep environment that directly converts the output to `EDM4HEP`. If you are interested, you can find more information about it <HERE> (ADD SOME LINKS TO SOURCE CODE OR DOC?). In terms of settings to fill in we have here:
- `delphesalg.DelphesCard` specifies which Delphes card we want to use. A Delphes card is a plain-text `(.tcl)` configuration file that defines a specific detector's parametrized response — its geometry, resolutions, and reconstruction efficiencies. Because that parametrization lives entirely in the card, swapping in a different one lets you simulate a different detector from the same generator-level input easily, which is the real strength of the fast-sim approach. We will use the baseline FCC-ee IDEA detector card. It comes pre-installed with the `key4hep` software stack, and you can find the main card under: `$DELPHES_DIR/cards/delphes_card_IDEA.tcl`
There are many other cards, for different (future) colliders and detectors in `$DELPHES_DIR/cards/`, which you can also view in your browser on [on github](https://github.com/delphes/delphes/tree/master/cards). 
- `delphesalg.DelphesOutputSettings` here we need to set the path to another config file defining which collections we want to store in our output `EDM4HEP` output file and what their names are. You can use the `edm4hep_IDEA.tcl` baseline configuration provided in this directory. 
- `delphesalg.GenParticles.Path` tells Delphes what the collection of generator level particles to send through the detector response simulation is, use the same name here as for the input collection. 

Finally, we define the following for our output: 
- `out.filename` is simply the name of your output file, set it to something that seems logical to you, for example `events_mumuH_Hbb_Delphes_IDEA.edm4hep.root`. 

## Understanding edm4hep datamodel collections

## Understanding the Delphes parametrization 

<!-- For the usecase of running Delphes fast simulation to produce `EDM4HEP` files, we only need this executable. But you can check which other Delphes utilities are available in your installation by just using the autocomplete functionality, i.e. typing `Delphes` <tab><tab> - this will show you the whole list. They all interface different modules and run with different input/output formats - the names should give you a clue which ones exactly. As mentioned already `DelphesPythia8_EDM4HEP` interfaces `Delphes` and `Pythia8` and outputs `EDM4HEP` files, rather than using the `Delphes` output file format. Another example is `DelphesSTDHEP_EDM4HEP` which uses `STDHEP` as input file format. Here you can really see the strength of having a common software ecosystem like `key4hep` - the same utility is offered for many specific usecases. 

We can check how to actually run the exectuable in question with the help option, for example:

`DelphesPythia8_EDM4HEP -h`

returns

```
Usage: DelphesPythia8config_file output_config_file pythia_card output_file
config_file - configuration file in Tcl format,
output_config_file - configuration file steering the content of the edm4hep output in Tcl format,
pythia_card - Pythia8 configuration file,
output_file - output file in ROOT format.
``` -->

<!-- telling us which input arguments it expects. Let's go through them: -->


- The `output_config_file` file: This file  We will use the standard version which comes with the software stack installation as `$K4SIMDELPHES/edm4hep_output_config.tcl`. 

- The `pythia_card`: As the name says, this is the configuration card for `Pythia`. Here we use the one provided as `PythiaCard/tester_pwp8_pp_hh_5f_hhbbyy.cmd`. It tells `Pythia` to run over the di-Higgs LHE file provided (`LHEInput/lhe_tester_ggHH.lhe`).  #TO UPDATE!

- The `output_file`: This is simply the name of the output file that will be produced, you can pick it freely but remember to explicitly include the `.root` file format ending.

Task: Run the event simulation using the cards and inputs as described above. 

<details>
  <summary>Solution</summary>

  COMMAND TO BE FIGURED OUT
  
</details>

You should see `Pythia` starting up and summarizing its settings, for example: 

TO BE ADDED

Then it will process 10 events, which should be quick. Let's first take a step back to understand what we processed here exactly.

SECTION ABOUT WHAT WE HAVE IN THE PYTHIA CARD HERE NOW TO BE ADDED?

Next, lets look at the `Delphes` card to see how the fast simulation works. For the FCC-ee IDEA scenario, we are modelling a detector layout of a vertex detector and drift chamber (inner tracking), followed by dual-readout electromagnetic and hadronic calorimeters, as well as a separate muon system embedded in the return yoke, which provides efficient muon identification and rejection of hadronic fakes. Parametrizations in bins of the pseudorapidity &eta; and the transverse momentum pT are used to model the response across the different regions of the detector. Roughly, the fast simulation proceeds in the following main steps:

- We start from all *stable particles*, as in particles that are written out by `Pythia` as outgoing particles, that do not further decay, at generator level. These are the input to the `ParticlePropagator` module, which propagates them through the magnetic field of the inner trackers. Neutral particles are propagated in a straight line, while charged particles are deflected on a heliocoidal trajectory - in each case the trajectory is modelled upto the point where the particle enters the calorimeter. Here, the magnetic field strength and coverage of the field (= radius of the inner tracker) are user-defined properties, that depend on the detector scenario we want to study. 