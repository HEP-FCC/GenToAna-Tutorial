#Input directory where the files produced at the pre-selection level are
inputDir  = "path"

# Output path
outputDir  = "path"

processList = {
    'process':{}, #output file from analysis_stage1.py
}

#Link to the dictonary that contains all the cross section informations etc...
procDict = "path"
#Note the numbeOfEvents and sumOfWeights are placeholders that get overwritten with the correct values in the samples

#How to add a process that is not in the official dictionary:
# Look up the values in the fcc physics events database! 
# procDictAdd={"pwp8_pp_hh_5f_hhbbyy": {"numberOfEvents": VALUE, "sumOfWeights": VALUE, "crossSection": VALUE, "kfactor": VALUE, "matchingEfficiency": VALUE}}

# Expected integrated luminosity
intLumi = VALUE  # pb-1

# Whether to scale to expected integrated luminosity
doScale = True

#Number of CPUs to use
nCPUS = 2

#produces ROOT TTrees, default is False
doTree = True

saveTabular = True

# Optional: Use weighted events
do_weighted = True 

# Dictionary of the list of cuts. The key is the name of the selection that will be added to the output file
# Add the cuts definining the signal region here, i.e. select appropriate windows in the di-photon and di-jet mass
cutList = {
            "sel0_example":"1 == 1",
            }

# Dictionary for the output variable/histograms. The key is the name of the variable in the output files. "name" is the name of the variable in the input file, "title" is the x-axis label of the histogram, "bin" the number of bins of the histogram, "xmin" the minimum x-axis value and "xmax" the maximum x-axis value.
histoList = {
  # plot histograms 
}