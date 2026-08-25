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
- `inp.collections` defines the list of collections we want to read from our input. Given that we have only run generation & showering so far, these are simply the generator level particles written out py `Pythia8`. You can take a look at the content of your produced file with `podio-dump <your_edm4hep_events.root>` to see what collection name you need to fill in here. 

Next, we load and configure the Delphes algorithm we want to run. In particular we use `k4SimDelphes`, this is an implementation of Delphes in the key4hep environment that directly converts the output to `EDM4HEP`. If you are interested, you can find more information about it <HERE> (ADD SOME LINKS TO SOURCE CODE OR DOC?). In terms of settings to fill in we have here:
- `delphesalg.DelphesCard` specifies which Delphes card we want to use. A Delphes card is a plain-text `(.tcl)` configuration file that defines a specific detector's parametrized response — its geometry, resolutions, and reconstruction efficiencies. Because that parametrization lives entirely in the card, swapping in a different one lets you simulate a different detector from the same generator-level input easily, which is the real strength of the fast-sim approach. We will use the baseline FCC-ee IDEA detector card. It comes pre-installed with the `key4hep` software stack, and you can find the main card under: `$DELPHES_DIR/cards/delphes_card_IDEA.tcl`
There are many other cards, for different (future) colliders and detectors in `$DELPHES_DIR/cards/`, which you can also view in your browser on [on github](https://github.com/delphes/delphes/tree/master/cards). 
- `delphesalg.DelphesOutputSettings` here we need to set the path to another config file defining which collections we want to store in our output `EDM4HEP` output file and what their names are. You can use the `edm4hep_IDEA.tcl` baseline configuration provided in this directory. 
- `delphesalg.GenParticles.Path` tells Delphes what the collection of generator level particles to send through the detector response simulation is, use the same name here as for the input collection. 

Finally, we define the following for our output: 
- `out.filename` is simply the name of your output file, you can pick it freely but remember to explicitly include the `.root` file format ending.

<!-- **Task: Complete the steering file and run the Delphes fast simulation with the IDEA detector parametrization.**

<details>
  <summary>Solution</summary>

  ```k4run solutions/delphes_IDEA_mumuH_allColl.py```
  
</details> -->

### Task :
> <details open>
> <summary><strong>❓ Question:</strong></summary>
> <br>
> Complete the steering file and run the Delphes fast simulation with the IDEA detector parametrization.
>

> 
> <details><summary><strong> ✅ Solutions: </strong></summary>
> <br> 
> ```k4run solutions/delphes_IDEA_mumuH_allColl.py```
>
>
> </details></details>
<br>


You should see `Delphes` starting up and summarizing its setup, for example: 

```
[....] 
** INFO: adding module        TruthVertexFinder        TruthVertexFinder        
** INFO: adding module        ParticlePropagator       ParticlePropagator       
** INFO: adding module        Efficiency               ChargedHadronTrackingEfficiency
** INFO: adding module        Efficiency               ElectronTrackingEfficiency
** INFO: adding module        Efficiency               MuonTrackingEfficiency   
** INFO: adding module        Merger                   TrackMergerPre           
** INFO: adding module        TrackCovariance          TrackSmearing  
[....]          
```

It will then process the 10k events you produced, which will take a few minutes. While it runs, you can read ahead into the next part where we take a step back to understand what we are processing here exactly.

## Understanding the Delphes parametrization 
Next, lets look at the `Delphes` card to see how the fast simulation works. For the FCC-ee IDEA scenario, we are modelling a detector layout of a vertex detector and drift chamber (inner tracking), followed by dual-readout electromagnetic and hadronic calorimeters, as well as a separate muon system embedded in the return yoke, which provides efficient muon identification and rejection of hadronic fakes. Parametrizations in bins of the pseudorapidity &eta; and the transverse momentum pT are used to model the response across the different regions of the detector. Roughly, the fast simulation proceeds in the following main steps:

- We start from all *stable particles*, as in particles that are written out by `Pythia` as outgoing particles, that do not further decay, at generator level. These are named `Delphes/allParticles` within the card and are the direct input to several Delphes modules:
  - The `BeamSpotSmearing` module gives the option to apply a spatial and temporal Gaussian offset to the collision vertices to mimic   the finite size of the beam spot, if this step is not yet done in the generation. With the standard IDEA setup we rely on here, `Pythia` has already taken care of this, so all the values here are set to zero, disabling the additional correction. 
  - Following this if the beam spot correction is applied, the `TruthVertexFinder` recalculates the truth primary vertex in the event. 

- Next, we model the path of all particles through the tracking system in the following way:
  -  The generator level particles are passed to the `ParticlePropagator` module, which propagates them through the magnetic field of the inner trackers. Neutral particles are propagated in a straight line, while charged particles are deflected on a heliocoidal trajectory - in each case the trajectory is modelled upto the point where the particle enters the calorimeter. Here, the magnetic field strength and coverage of the field (= radius of the inner tracker) are user-defined properties, that depend on the detector scenario we want to study. For the neutral particles, we just need this step to determine the position at which they enter the calorimeter, so we can pick them up in the simulation of the calorimeter response and are therefore done with him here. For charged particles, we continue modeling the tracker response. 
  - First we apply the `TrackingEfficiency` modules for the different particle types, this contains the probability of the track for a particle to be reconstructed in bins of the transverse momentum and pseudorapidity. This is the reason why we needed to do the above simple propagation through the magnetic field first, because this tells us exactly which bin a given particle is in to determine the tracking efficiency. 
  - Next, we perform a more complete - but still fast-simulation, parametrization based - modelling of the track, its hits and its resolution using the `TrackCovariance` module. TODO FILL THIS IN PROPERLY. INCLUDE ALSO PID (CLUSTERCOUNTING, TOF EXPLANATION). END WITH PICKING UP BOTH NEUTRALS AND CHARGED AGAIN AT THE CALOS FOR NEXT STEP 

- For simulating the calorimeter response, a segmentation in &eta; and &phi; is given in the `Calorimeter` module, and it is assumed that each particle deposits its energy into one of such segments (then called a tower). This module also specifies which fraction of a particle's energy is deposited in the electromagnetic and hadronic calorimeter. The energy deposits in the electromagnetic and hadronic calorimeters are then smeared independently, following parametrizations in energy and pseudo-rapidity, as defined in the card. 

- *Particle-flow* objects are then built from the tracks and calorimeter towers, forming our physics objects.  IS THIS TRUE? ADD MORE INFO

- *Identification efficiency* parametrizations are defined for objects of interest such as photons, muons and electrons, for example in the `PhotonEfficiency` module. These efficiencies are applied on top of the tracking efficiencies. Furthermore, for these objects an isolation variable (named `PTRatioMax` in the card) is defined in e.g. `ElectronIsolation`. 

- The last block of the card, the `TreeWriter` module, shows you which objects are propagated to Delphes output level. Note that this doesn't mean we will have them in our `.root` file that we created above, as there is still one step in our simulation chain, which is the conversion from `Delphes` output to `EDM4HEP` events. 

### Task 1 : Understanding the Delphes card 
Look through the Delphes card and try to answer the following questions with the help of the guide above: 

> <details open>
> <summary><strong>❓Questions :</strong></summary>
> <br>
> 

> 
> <details><summary><strong> ✅ Solutions: </strong></summary>
> <br> 
> This is the answer
>
>
> </details></details>
<br>

### Task 2 : Changing the PID settings 
TO DO ! COME UP WITH TASK ! MAYBE AN OPTIONAL TASK GIVEN THE TIME? 


## Understanding edm4hep datamodel collections




