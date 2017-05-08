import arcpy
import os
import network_k_calculation
import network_k_analysis
import k_function_helper
import random_odcm_permutations_svc

from arcpy import env

# ArcMap caching prevention.
network_k_calculation        = reload(network_k_calculation)
network_k_analysis           = reload(network_k_analysis)
k_function_helper            = reload(k_function_helper)
random_odcm_permutations_svc = reload(random_odcm_permutations_svc)

from network_k_calculation        import NetworkKCalculation
from network_k_analysis           import NetworkKAnalysis
from k_function_helper            import KFunctionHelper
from random_odcm_permutations_svc import RandomODCMPermutationsSvc

class LocalKFunctionSvc(object):
  ###
  # Initialize the service (stateless).
  ###
  def __init__(self):
    self.kfHelper = KFunctionHelper()

  ###
  # Create a cutoff distance for the ODCM permutations if possible.
  # @param numBands The number of distance bands (if available).
  # @param distInc The distance increment between each band.
  # @oparam begDist The beginning distance.
  ###
  def getCutoff(self, numBands, distInc, begDist):
    if numBands is not None:
      return numBands * distInc + begDist
    else:
      return None

  ###
  # Write the raw analysis data.
  ###
  def writeRawAnalysisData(self, outNetKLoc, outRawFCName, netKCalculations, begDist, distInc, numBands):
    # Write the distance bands to a table.  The 0th iteration is the observed
    # data.  Subsequent iterations are the uniform point data.
    outRawFCFullPath = os.path.join(outNetKLoc, outRawFCName)
    arcpy.CreateTable_management(outNetKLoc, outRawFCName)

    fields = ["Iteration_Number", "OriginId"]
    arcpy.AddField_management(outRawFCFullPath, "Iteration_Number", "LONG")
    arcpy.AddField_management(outRawFCFullPath, "OriginId",         "LONG")

    cutoff = int(self.getCutoff(numBands, distInc, begDist) + distInc)
    # for x in range(int(begDist), cutoff, int(distInc)):
    for x in range(0, numBands):
      distBand = int(begDist + (x * distInc))
      arcpy.AddField_management(outRawFCFullPath, "LD{0}".format(distBand), "DOUBLE")
      fields.append("LD{0}".format(distBand))

    cursor = arcpy.da.InsertCursor(outRawFCFullPath, fields)
    for netKNum in range(0, len(netKCalculations)):
        for origin in netKCalculations[netKNum]:
          row = [netKNum, origin["originId"]]
          for bandCount in origin["distBands"]:
            row.append(bandCount)

          cursor.insertRow(row)

    # with arcpy.da.InsertCursor(outRawFCFullPath,
    #   ["Iteration_Number", "Distance_Band", "Point_Count", "K_Function"]) as cursor:
    #   for netKNum in range(0, len(netKCalculations)):
    #     for distBand in netKCalculations[netKNum]:
    #       cursor.insertRow([netKNum, distBand["distanceBand"], distBand["count"], distBand["KFunction"]])

  ###
  # Perform the summary analysis and write the summary data.
  ###
  def writeAnalysisSummaryData(self, numPerms, netKCalculations, outNetKLoc, outAnlFCName):
    # Analyze the network k results (generate plottable output).
    # No confidence intervals are computed if there are no random permutations.
    if numPerms != 0:
      netKAn_95 = NetworkKAnalysis(.95, netKCalculations)
      netKAn_90 = NetworkKAnalysis(.90, netKCalculations)

    # Write the analysis data to a table.
    outAnlFCFullPath = os.path.join(outNetKLoc, outAnlFCName)
    arcpy.CreateTable_management(outNetKLoc, outAnlFCName)
    arcpy.AddField_management(outAnlFCFullPath, "Description",   "TEXT")
    arcpy.AddField_management(outAnlFCFullPath, "Distance_Band", "DOUBLE")
    arcpy.AddField_management(outAnlFCFullPath, "Point_Count",   "DOUBLE")
    arcpy.AddField_management(outAnlFCFullPath, "K_Function",    "DOUBLE")

    with arcpy.da.InsertCursor(outAnlFCFullPath,
      ["Description", "Distance_Band", "Point_Count", "K_Function"]) as cursor:
      self._writeAnalysis(cursor, netKCalculations[0], "Observed")

      if numPerms != 0:
        self._writeAnalysis(cursor, netKAn_95.getLowerConfidenceEnvelope(), "2.5% Lower Bound")
        self._writeAnalysis(cursor, netKAn_95.getUpperConfidenceEnvelope(), "2.5% Upper Bound")
        self._writeAnalysis(cursor, netKAn_90.getLowerConfidenceEnvelope(), "5% Lower Bound")
        self._writeAnalysis(cursor, netKAn_90.getUpperConfidenceEnvelope(), "5% Upper Bound")

  # Write the analysis data in distBands using cursor.
  def _writeAnalysis(self, cursor, distBands, description):
    for distBand in distBands:
      cursor.insertRow([description, distBand["distanceBand"], distBand["count"], distBand["KFunction"]])
