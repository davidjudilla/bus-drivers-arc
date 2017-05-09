from network_k_calculation import NetworkKCalculation
import numpy as np
print(np)

class LocalKCalculation(NetworkKCalculation):
  ###
  # Initialize the calculator.
  # @param netLen The length of the network.
  # @param numPoints The total number of points in the observed data.
  # @param odDists An array of origins and destinations from an OD cost
  #        matrix.  Each should have keys Total_Length, OriginID, DestinationID.
  # @param begDist The distance to begin calculating (the first distance band).
  # @param distInc The amount to increment each distance band.
  # @param numBands The number of distance bands (optional).
  ###
  def __init__(self, netLen, numPoints, odDists, begDist, distInc, numBands, numOrigins, messages):
    self._netLen    = netLen
    self._numPoints = numPoints
    self._odDists   = sorted(odDists, key=lambda odDist: odDist["OriginID"])
    self._begDist   = begDist
    self._distInc   = distInc
    self._numBands  = numBands
    self._numOrigins= numOrigins
    self.messages = messages

    # If the user doesn't specify the number of distance bands then calculate it.
    if self._numBands is None:
      maxLen         = self._odDists[-1]["Total_Length"]
      self._numBands = int(math.ceil((maxLen - self._begDist) / self._distInc + 1))

    # Calculate the overall point-network density.
    self._pnDensity = self.calculatePointNetworkDensity()

    # Count the points in each distance band.
    self._distBands = self.countDistanceBands()

    # Calculate the network k values.
    # self.calculateNetworkK()

  # Count the number of points in each distance band.
  def countDistanceBands(self):
    allOriginDistBands = []
    startDist = self.getBeginningDistance()
    numBands  = self.getNumberOfDistanceBands()
    odDists   = self.getDistances()
    numOrigins= self._numOrigins
    
    # Split odDists by OriginID, where each OriginID has its own array of dictionaries
    if (len(odDists) < 1):
      return allOriginDistBands
      
    keys = odDists[0].keys()
    odDistsTuples = np.array([tuple(row.values()) for row in odDists])
    originIdIndex = keys.index("OriginID")
    lengthIndex = keys.index("Total_Length")
    originArrays = np.split(odDistsTuples, np.where( np.diff( odDistsTuples[ :,originIdIndex ] ))[0]+1)
    originArrays = [sorted(arr.tolist(), key=lambda odDist: odDist[lengthIndex]) for arr in originArrays]

    # Now that we have an array for each origin and each array is 
    # sorted by Total_Length we can use identical code to Network K Calculation
    for originArr in originArrays:
      initDistBandCounts = [0 for x in range(0, numBands)]
      originDistBands = {"originId": int(originArr[0][originIdIndex]), "distBands": initDistBandCounts}

      numDists = len(originArr)
      currRowCnt = 0
      distBandIndex = 0
      currBandLen = startDist
      distBands = originDistBands["distBands"]

      for bandNum in range(0, numBands):
        currDistBandCnt = distBands[bandNum]

        if distBands[bandNum-1] is not None:
          currDistBandCnt = distBands[bandNum-1]       

        endDist = currBandLen + self.getDistanceIncrement()

        while currRowCnt < numDists and originArr[currRowCnt][lengthIndex] < endDist:
          if originArr[currRowCnt][lengthIndex] >= currBandLen:
            currDistBandCnt += 1
          currRowCnt += 1
        currBandLen += self.getDistanceIncrement()
        distBands[bandNum] = currDistBandCnt

      allOriginDistBands.append(originDistBands)
    # self.messages.addMessage(allOriginDistBands)
    return allOriginDistBands