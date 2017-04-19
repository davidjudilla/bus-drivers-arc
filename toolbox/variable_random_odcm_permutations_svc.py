import arcpy
import os
import k_function_helper
import k_function_timer

from arcpy import env

# ArcMap caching prevention.
k_function_helper = reload(k_function_helper)
k_function_timer  = reload(k_function_timer)

from k_function_helper import KFunctionHelper
from k_function_timer  import KFunctionTimer

class VariableRandomODCMPermutationsSvc:
  ###
  # Initialize the service (stateless).
  ###
  def __init__(self):
    self.kfHelper = KFunctionHelper()

  ###
  # Generate the ODCM permutations.
  # @param analysisType Either Global Analysis or Cross Analysis.
  # @param srcPoints The source points.
  # @param destPoints The destination points.  Ignored if analysisType is GLOBAL.
  # @param networkDataset The network dataset to use for the ODCMs.
  # @param snapDist The snap distance for points that are not directly on the network.
  # @param cutoff The cutoff distance.  Ignored if None.
  # @param outLoc The full path to a database.  The ODCM data will be written here.
  # @param outFC The name of the feature class in outLoc where the ODCM data will be written.
  # @param numPerms The number of permutations (string representation).
  # @param outCoordSys The coordinate system to project the points into (optional).
  # @param numPointsFieldName The optional name of a field in the network dataset's edge source
  #        from which the number of random points should be derived.
  # @param messages A messages instances with addMessage() implemented (for debug output).
  # @param callback A callback function(odDists, iteration) called on each iteration
  #        with the current OD cost matrix.
  ###
  def generateODCMPermutations(self, analysisType, srcPoints, destPoints,
    networkDataset, snapDist, cutoff, outLoc, outFC, numPerms, outCoordSys,
    numPointsFieldName, lengthFieldName, messages, callback = None):
    # Default no-op for the callback.
    if callback is None:
      callback = lambda odDists, iteration: None

    # For global analysis the destination points are the same as the source points
    # (e.g. destPoints is ignored).
    if analysisType == "GLOBAL" or destPoints is None:
      destPoints = srcPoints

    # Count the number of crashes (there may be fewer points in the ODCM, but it's the total
    # number of crashes that is needed).
    numDests = self.kfHelper.countNumberOfFeatures(os.path.join(outLoc, destPoints))
    messages.addMessage("Number of crashes: {0}".format(numDests))

    # Make the observed ODCM and calculate the distance between each set of
    # points.  If a cross analysis is selected, find the distance between the
    # source and destination points.  Otherwise there is only one set of points
    odDists = self._calculateDistances(networkDataset, srcPoints, destPoints, snapDist, cutoff, lengthFieldName, messages)
    self._writeODCMData(odDists, outLoc, outFC, 0)
    callback(odDists, 0)
    messages.addMessage("Iteration 0 (observed) complete.")

    # Generate the OD Cost matrix permutations.
    kfTimer = KFunctionTimer(numPerms)
    for i in range(1, numPerms + 1):
      if numPointsFieldName:
        randPoints = self.kfHelper.generateRandomPoints(networkDataset, outCoordSys, None, numPointsFieldName)
      else:
        randPoints = self.kfHelper.generateRandomPoints(networkDataset, outCoordSys, numDests, None)

      # See the note above: Either find the distance from the source points to the random points,
      # or the distance between the random points.
      if analysisType == "CROSS":
        odDists = self._calculateDistances(networkDataset, srcPoints, randPoints, snapDist, cutoff, lengthFieldName)
      else:
        odDists = self._calculateDistances(networkDataset, randPoints, randPoints, snapDist, cutoff, lengthFieldName)
      self._writeODCMData(odDists, outLoc, outFC, i)
      callback(odDists, i)

      # Clean up the random points table.
      arcpy.Delete_management(randPoints)

      # Show the progress.
      kfTimer.increment()
      messages.addMessage("Iteration {0} complete.  Elapsed time: {1}s.  ETA: {2}s.".format(
        i, kfTimer.getElapsedTime(), kfTimer.getETA()))

  ###
  # Calculate the distances between each set of points using an OD Cost Matrix.
  # @param networkDataset A network dataset which the points are on.
  # @param srcPoints The source points to calculate distances from.
  # @param destPoints The destination points to calculate distances to.
  # @param snapDist If a point is not directly on the network, it will be
  #        snapped to the nearset line if it is within this threshold.
  # @param cutoff The cutoff distance for the ODCM (optional).
  ###
  def _calculateDistances(self, networkDataset, srcPoints, destPoints, snapDist, cutoff, lengthFieldName, messages):
    # This is the current map, which should be an OSM base map.
    curMapDoc = arcpy.mapping.MapDocument("CURRENT")

    # Get the data from from the map (see the DataFrame object of arcpy).
    dataFrame = arcpy.mapping.ListDataFrames(curMapDoc, "Layers")[0]

    # Create the cost matrix.
    costMatResult = arcpy.na.MakeODCostMatrixLayer(networkDataset, "TEMP_ODCM_NETWORK_K", "Length", cutoff)
    odcmLayer     = costMatResult.getOutput(0)

    # The OD Cost Matrix layer will have Origins and Destinations layers.  Get
    # a reference to each of these.
    odcmSublayers   = arcpy.na.GetNAClassNames(odcmLayer)
    odcmOriginLayer = odcmSublayers["Origins"]
    odcmDestLayer   = odcmSublayers["Destinations"]
    originDescription = arcpy.Describe(odcmOriginLayer)
    srcRows = [row for row in arcpy.SearchCursor(srcPoints)]
    messages.addMessage("originDesc {0}".format(originDescription.children));
    messages.addMessage("origin field_names {0}".format([f.name for f in arcpy.ListFields(srcPoints)]))
    messages.addMessage("row 1: {0}".format(srcRows[0].getValue(lengthFieldName)))

    # Add the origins and destinations to the ODCM.
    arcpy.na.AddLocations(odcmLayer, odcmOriginLayer, srcPoints,  "", snapDist)
    arcpy.na.AddLocations(odcmLayer, odcmDestLayer,   destPoints, "", snapDist)

    # Solve the matrix.
    arcpy.na.Solve(odcmLayer)

    # Show the ODCM layer (it must be showing to open th ODLines sub layer below).
    #arcpy.mapping.AddLayer(dataFrame, odcmLayer, "TOP")
    #arcpy.RefreshTOC()

    # Get the "Lines" layer, which has the distance between each point.
    odcmLines = arcpy.mapping.ListLayers(odcmLayer, odcmSublayers["ODLines"])[0]

    # This array will hold all the OD distances.
    odDists = []

    if srcPoints == destPoints:
      # If the source points and destination points are the same, exclude the
      # distance from the point to itself.
      where = """{0} <> {1}""".format(
        arcpy.AddFieldDelimiters(odcmLines, "originID"),
        arcpy.AddFieldDelimiters(odcmLines, "destinationID"))
    else:
      where = ""

    with arcpy.da.SearchCursor(
      in_table=odcmLines,
      field_names=["Total_Length", "originID", "destinationID"],
      where_clause=where) as cursor:

      for row in cursor:
        odDists.append({"Total_Length": row[0]/srcRows[row[1]-1].getValue(lengthFieldName), "OriginID": row[1], "DestinationID": row[2]})

    return odDists
  
  ###
  # Write the ODCM data to a table.
  # @param odDists An array of raw ODCM data.
  # @param outLoc The location of a database.
  # @param outFC The feature class name, in outLoc, to write the data to.
  # @param iteration The iteration number (0 is observed).
  ###
  def _writeODCMData(self, odDists, outLoc, outFC, iteration):
    # This is the full path to the output feature class.
    outFCFullPath = os.path.join(outLoc, outFC)

    if iteration == 0:
      # Create the output table.
      arcpy.CreateTable_management(outLoc, outFC)
      arcpy.AddField_management(outFCFullPath, "Iteration_Number", "LONG")
      arcpy.AddField_management(outFCFullPath, "OriginID",         "LONG")
      arcpy.AddField_management(outFCFullPath, "DestinationID",    "LONG")
      arcpy.AddField_management(outFCFullPath, "Total_Length",     "DOUBLE")

    with arcpy.da.InsertCursor(outFCFullPath,
      ["Iteration_Number", "OriginID", "DestinationID", "Total_Length"]) as cursor:
      for odDist in odDists:
        cursor.insertRow([iteration, odDist["OriginID"], odDist["DestinationID"], odDist["Total_Length"]])
