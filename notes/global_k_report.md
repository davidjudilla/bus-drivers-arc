#Global K Function (Previous Group)

### Execute() code:
```python
  def execute(self, parameters, messages):
    points             = parameters[0].valueAsText
    networkDataset     = parameters[1].valueAsText
    numBands           = parameters[2].value
    begDist            = parameters[3].value
    distInc            = parameters[4].value
    snapDist           = parameters[5].value
    outNetKLoc         = parameters[6].valueAsText
    outRawODCMFCName   = parameters[7].valueAsText
    outRawFCName       = parameters[8].valueAsText
    outAnlFCName       = parameters[9].valueAsText
    numPermsDesc       = parameters[10].valueAsText
    numPerms           = self.kfHelper.getPermutationSelection()[numPermsDesc]
    outCoordSys        = parameters[11].value
    numPointsFieldName = parameters[12].value
    ndDesc             = arcpy.Describe(networkDataset)
    gkfSvc             = GlobalKFunctionSvc()

    # Refer to the note in the NetworkDatasetLength tool.
    if outCoordSys is None:
      outCoordSys = ndDesc.spatialReference

    messages.addMessage("\nOrigin points: {0}".format(points))
    messages.addMessage("Network dataset: {0}".format(networkDataset))
    messages.addMessage("Number of distance bands: {0}".format(numBands))
    messages.addMessage("Beginning distance: {0}".format(begDist))
    messages.addMessage("Distance increment: {0}".format(distInc))
    messages.addMessage("Snap distance: {0}".format(snapDist))
    messages.addMessage("Output location (database path): {0}".format(outNetKLoc))
    messages.addMessage("Raw ODCM data table: {0}".format(outRawODCMFCName))
    messages.addMessage("Raw global-K data table (raw analysis data): {0}".format(outRawFCName))
    messages.addMessage("Global-K summary data (plottable data): {0}".format(outAnlFCName))
    messages.addMessage("Number of random permutations: {0}".format(numPerms))
    messages.addMessage("Network dataset length projected coordinate system: {0}".format(outCoordSys.name))
    messages.addMessage("Number of Points Field Name: {0}\n".format(numPointsFieldName))

    # Calculate the length of the network.
    networkLength = self.kfHelper.calculateLength(networkDataset, outCoordSys)
    messages.addMessage("Total network length: {0}".format(networkLength))

    # Count the number of crashes.
    numPoints = self.kfHelper.countNumberOfFeatures(os.path.join(outNetKLoc, points))

    # Set up a cutoff length for the ODCM data if possible.  (Optimization.)
    cutoff = gkfSvc.getCutoff(numBands, distInc, begDist)

    # The results of all the calculations end up here.
    netKCalculations = []

    # Use a mutable container for the number of bands so that the below callback
    # can write to it.  The "nonlocal" keyword not available in Python 2.x.
    numBandsCont = [numBands]

    # Callback function that does the Network K calculation on an OD cost matrix.    
    def doNetKCalc(odDists, iteration):
      # Do the actual network k-function calculation.
      netKCalc = NetworkKCalculation(networkLength, numPoints, odDists, begDist, distInc, numBandsCont[0])
      netKCalculations.append(netKCalc.getDistanceBands())

      # If the user did not specifiy a number of distance bands explicitly,
      # store the number of bands.  It's computed from the observed data.
      if numBandsCont[0] is None:
        numBandsCont[0] = netKCalc.getNumberOfDistanceBands()

    # Generate the ODCM permutations, including the ODCM for the observed data.
    # doNetKCalc is called on each iteration.
    randODCMPermSvc = RandomODCMPermutationsSvc()
    randODCMPermSvc.generateODCMPermutations("Global Analysis",
      points, points, networkDataset, snapDist, cutoff, outNetKLoc,
      outRawODCMFCName, numPerms, outCoordSys, numPointsFieldName, messages, doNetKCalc)

    # Store the raw analysis data.
    messages.addMessage("Writing raw analysis data.")
    gkfSvc.writeRawAnalysisData(outNetKLoc, outRawFCName, netKCalculations)

    # Analyze the data and store the results.
    messages.addMessage("Analyzing data.")
    gkfSvc.writeAnalysisSummaryData(numPerms, netKCalculations, outNetKLoc, outAnlFCName)

```
## Okay, Lets Break It Down
Most of this is self explanatory up until 
```python
    # Generate the ODCM permutations, including the ODCM for the observed data.
    # doNetKCalc is called on each iteration.
    randODCMPermSvc = RandomODCMPermutationsSvc()
    randODCMPermSvc.generateODCMPermutations("Global Analysis",
      points, points, networkDataset, snapDist, cutoff, outNetKLoc,
      outRawODCMFCName, numPerms, outCoordSys, numPointsFieldName, messages, doNetKCalc)
```
`randODCMPermSvc.generateODCMPermutations` takes in origin/destination points, as well as the network dataset to calculate the distances between all the points, using `RandomODCMPermutationsSvc._calculateDistances()`, then writes then to the output file location. After that the callback is invoked. The callback being 
```
# Callback function that does the Network K calculation on an OD cost matrix.    
    def doNetKCalc(odDists, iteration):
      # Do the actual network k-function calculation.
      netKCalc = NetworkKCalculation(networkLength, numPoints, odDists, begDist, distInc, numBandsCont[0])
      netKCalculations.append(netKCalc.getDistanceBands())

      # If the user did not specifiy a number of distance bands explicitly,
      # store the number of bands.  It's computed from the observed data.
      if numBandsCont[0] is None:
        numBandsCont[0] = netKCalc.getNumberOfDistanceBands()
```
I'll be looking more into NetworkKCalculation's soon (2/21/16)

Where `Permutations` comes into play here when we tell the toolbox prompt that we want more than 0 permutations. Permutations are just creating a random data points on the network dataset by using `kfHelper.generateRandomPoints`, which just uses the `NetworkDatasetRandomPoints` tool from the previous group. 




## Global vs Cross K Function Code
Global's origin points are the same as it's destination points, whereas Cross K's is the origin and destination points inputted from the toolbox prompt

**Method Declaration**
```
def generateODCMPermutations(self, analysisType, 
	srcPoints, destPoints, networkDataset, snapDist, cutoff, outLoc,
	outFC, numPerms, outCoordSys, numPointsFieldName, messages, callback = None):
```
**Global**
```python
randODCMPermSvc.generateODCMPermutations("Global Analysis",
      points, points, networkDataset, snapDist, cutoff, outNetKLoc,
      outRawODCMFCName, numPerms, outCoordSys, numPointsFieldName, messages, doNetKCalc)
```

**Cross**
```
randODCMPermSvc.generateODCMPermutations("Cross Analysis",
      srcPoints, destPoints, networkDataset, snapDist, cutoff, outNetKLoc,
      outRawODCMFCName, numPerms, outCoordSys, numPointsFieldName, messages, doNetKCalc)

```
**Note:** `(points, points)` vs `(srcPoints, destPoints)`
