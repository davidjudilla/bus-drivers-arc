from network_k_calculation import NetworkKCalculation

class VariableDistanceKCalculation(NetworkKCalculation):
  # Initialize the calculator.
  # @param netLen The length of the network.
  # @param numPoints The total number of points in the observed data.
  # @param odDists An array of origins and destinations from an OD cost
  #        matrix.  Each should have keys Total_Length, OriginID, DestinationID.
  # @param begDist The distance to begin calculating (the first distance band).
  # @param distInc The amount to increment each distance band.
  # @param numBands The number of distance bands (optional).
  ###
  def __init__(self, netLen, numPoints, odDists, begDist, distInc, numBands):
    self._netLen    = netLen
    self._numPoints = numPoints
    self._odDists   = sorted(odDists, key=lambda odDist: odDist["Ratio"])
    self._begDist   = begDist
    self._distInc   = distInc
    self._numBands  = numBands

    # If the user doesn't specify the number of distance bands then calculate it.
    if self._numBands is None:
      maxLen         = self._odDists[-1]["Total_Length"]
      self._numBands = int(math.ceil((maxLen - self._begDist) / self._distInc + 1))

    # Calculate the overall point-network density.
    self._pnDensity = self.calculatePointNetworkDensity()

    # Count the points in each distance band.
    self._distBands = self.countDistanceBands()

    # Calculate the network k values.
    self.calculateNetworkK()

  # Count the number of points in each distance band.
  def countDistanceBands(self):
    distBands = []
    startDist = self.getBeginningDistance()
    numBands  = self.getNumberOfDistanceBands()
    odDists   = self.getDistances()
    numDists  = len(odDists)
    distNum   = 0
    
    # Go through all the distance bands.
    for bandNum in range(0, numBands):
      distBands.append({"distanceBand": startDist, "count": 0})
      distBand = distBands[-1]

      # Increase the count of points in the current distance band until either
      # the current distance is exceeded or the last point is reached.  Note
      # that the distances are ordered by Total_Length.
      endDist = startDist + self.getDistanceIncrement()

      while distNum < numDists and odDists[distNum]["Ratio"] < endDist:
        # The user may have specified a start distance, and there may be distances between
        # points that are smaller than the user-defined start dist.  Don't count these.
        # For example, if the user specifies a start distance of 200M, and there is a
        # crash 30M from a bridge then it's not in the first distance band and
        # is not counted.
        if odDists[distNum]["Ratio"] >= startDist:
          distBand["count"] += 1
        distNum += 1
      startDist += self.getDistanceIncrement()

    return distBands
