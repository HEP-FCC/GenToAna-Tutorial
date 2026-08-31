'''
Analysis example for FCC-hh, using gg->HH->bbyy di-Higgs production events 
'''
from argparse import ArgumentParser


# Mandatory: Analysis class where the user defines the operations on the
# dataframe.
class Analysis():
    '''
    Di-Higgs analysis in bbyy.
    '''
    def __init__(self, cmdline_args):
        parser = ArgumentParser(
            description='Additional analysis arguments',
            usage='Provide additional arguments after analysis script path')
        # parser.add_argument('--bjet-pt', default='10.', type=float,
        #                     help='Minimal pT of the selected b-jets.')
        # Parse additional arguments not known to the FCCAnalyses parsers
        # All command line arguments know to fccanalysis are provided in the
        # `cmdline_arg` dictionary.
        self.ana_args, _ = parser.parse_known_args(cmdline_args['remaining'])

        # Mandatory: List of processes to run over
        self.process_list = {
            # # Add your processes like this: 
            ## '<name of process>':{'fraction':<fraction of events to run over>, 'chunks':<number of chunks to split the output into>, 'output':<name of the output file> }, 
            # # - <name of process> needs to correspond either the name of the input .root file, or the name of a directory containing root files 
            # # If you want to process only part of the events, split the output into chunks or give a different name to the output use the optional arguments
            # # or leave blank to use defaults = run the full statistics in one output file named the same as the process:
            'process': {},
        }

        # Mandatory: Input directory where to find the samples, or a production tag when running over the centrally produced
        # samples (this points to the yaml files for getting sample statistics)
        self.input_dir = 'path'

        # Optional: output directory, default is local running directory
        self.output_dir = 'path'

        # Optional: analysisName, default is ''
        self.analysis_name = 'FCC-hh bbyy analysis'

        # Optional: number of threads to run on, default is 1
        # self.n_threads = 4

        # Optional: running on HTCondor, default is False
        # self.run_batch = False

        # Optional: Use weighted events
        self.do_weighted = True 

        # Optional: read the input files with podio::DataSource 
        self.use_data_source = False # explicitly use old way in this version 

        # Optional: test file that is used if you run with the --test argument (fccanalysis run ./examples/FCChh/ggHH_bbyy/analysis_stage1.py --test)
        # Hint: If you were not able to produce your own FCC-hh fast sim output, you can use the file provided here
        self.test_file = 'root://eospublic.cern.ch//eos/experiment/fcc/hh/' \
                         'tutorials/edm4hep_tutorial_data/' \
                         'pwp8_pp_hh_5f_hhbbyy.root'


    # Mandatory: analyzers function to define the analysis graph, please make
    # sure you return the dataframe, in this example it is dframe2
    def analyzers(self, dframe):
        '''
        Analysis graph.
        '''

        dframe2 = (
            dframe

            ########################################### DEFINITION OF VARIABLES ########################################### 


            ########################################### PHOTONS ########################################### 

            # Access photon collection from EDM4hep 
            # Apply object-level cuts, select only pT > 30 GeV and |eta| < 4 

            # Store: number of photons; energy, pT, eta and phi of the leading and subleading photon

            # Build H(yy) candidate by getting the merged 4vector of the 2 leading photons
            # Hint: You can look into the AnalysisFCChh analyser for helper functions to build particle pairs

            ########################################### JETS ########################################### 

            # Same as above for the b-jets, use the medium working point

            ########################################### APPLY PRE-SELECTION ########################################### 
            # Require at least two b-jets and two photons as pre-selection

        )
        return dframe2

    # Mandatory: output function, please make sure you return the branch list
    # as a python list
    def output(self):
        '''
        Output variables which will be saved to output root file.
        '''
        branch_list = [
        ]
        return branch_list
