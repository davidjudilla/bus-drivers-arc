# Senior Project Notes

## 4 Major Tools implemented from the last senior project team 
- `Crash Radius Density`
- `Crash Network Density`
- `Network K Analysis`
- `Cross K Function` - Analyzes between multiple (2) points rather than the one
	- How points cluster relative to another point, so do crashes cluster around a bridge

`Crash Analysis Toolbox.pyt` - the python code that defines the tool box

`Crash Analysis Toolbox.Tool.pyt.xml` - the xml file that contains the metadata + item descriptions of the toolbox.

Toolbox loaded in through `Crash Analysis Toolbox.py`
Looks like the only finalized tools are
- `Crash Network Density`
- `Crash Radius Density`
- `Create Random Points on a Network Dataset`
- `Cross K Function`
- `Global K Function`
- `Network Dataset Length`
- `Random ODCM Permutations`

The general idea for the tools is that a dataset is loaded and when one of the tools are executed a prompt comes up in ArcGIS, which will ask for parameters which could be a networkDataset, crash points, etc.

Use this coordinate system when plotting points in ArcGIS: **World WGS 1984**

**Notes on Geodatabases**

`Geodatabase -> Feature Datasets -> Feature Classes`

Feature Classes in out case are made up of shape files, which contain points for car crashes

**Unimplemented features**
- Variable Distance K Function
- Outputting table columns showing how many points fall within distance bands

##Questions (1/30/16)

Availability outside of office hours

    Answer: Available T/Th/F most days, but email ahead. M/W find during office hours.

How do the current tools work together?

- Crash Network/Radius Density are used to visually see correlations in arcgis
- Random point dataset can be used to compare
- Cross/Global K function are used to find points that are clustered, dispersed, or just plain random
    - Outputs a table/dataset that can be used in the network k function

How are the feature datasets created with the current data?
    
    Answer: There was a datset we didn't have. Looks like the previous group didn't put it up on github because it's about half a gig
Is the cross k function a local k function?

    Answer: No, but there is a local cross k function, which finds the distance from *one* origin point to all destination points

## Why are K Functions useful?
Global k function shows us that there is clustering, dispersion, or if points are completely random, thus raising the question of why are points clustering.

So we use the Cross K Function to find what causes the clustering.

Global Cross K Function is made up the sum of all Cross K Functions.

A geodatabase is similar to Microsofts Access database

## In Place Toolbox Description
- ####Crash Network Density
    - **Summary**
        - The CrashNetworkDensity tool creates a network using an existing dataset of crashes (as coordinates) as well as the Open Street Map Network (view Syntax). 
    - **Usage**
        - An existing Feature Dataset must exist to use this tool. 
        - Once a feature dataset exists, the CrashNetworkDensity tool can be used on this dataset to create a network with the Open Street Map Network. 
- ####Crash Radius Density
    - **Summary**
        - Creates a bounding circle with a user defined radius around crashes (as coordinates), allowing a user to view how many crashes cluster within the user defined radius of a given crash point. 
    - **Usage**
        - An existing feature dataset must exist in order to use the CrashRadiusDensity tool.
        - The tool can then be run by inputing a feature dataset as well as the radius for each of the crash points. 
- ####Create Random Points on a Network Dataset
    - **Summary**
        - Creates a specified number of points randomly on a network dataset as a feature class. 
    - **Usage**
        - See parameters for Required and Optional Fields. 
        - Outputs a series of random points on a network dataset. 
- ####Cross K Function
    - **Summary**
        - The Cross K Function tool that allows the user to find crash clustering and dispersion at different distance bands using Dr. Ghazan Khan’s modified version of the Ripley’s K Function. For a given set of crash points, this function determines deviations from spatial homogeneity at different distances along a road network.
        - Cross-K analysis, is comprised of local statistics at individual crash locations to identify individual crashes as part of a statistically significant clustered (hotspot), dispersed (coldspot), or random point pattern. The methods under the crash cluster analysis category were developed based on the principles of the K-Function method in network space.
    - **Usage**
        - See parameters for description for Required and Optional inputs. 
        - Outputs a table and a database of raw data which is used to generate the Network K Function.
- ####Global K Function
    - **Summary**
        - The Global K Function tool allows the user to find crash clustering and dispersion at different distance bands. 
        - The “Global” analysis type calculates the global statistic to identify the presence or absence of a systematic process, the magnitude, and the extent of spatial patterns in crash data.
    - **Usage**
        - See parameters for description for Required and Optional inputs.
        - Outputs a table of raw data which is used to generate the Network K Function.
- ####Network Dataset Length
    - **Summary**
        - Calculates the length of a network dataset 
    - **Usage**
        - There is no usage for this tool.
- ####Random ODCM Permutations
    - **Summary**
        - Generates OD Cost Matrices with observed data and a complementary set of random point permutations.
        - The tool can take a long time to run based on the number of permutations the tool is set to run for. 
    - **Usage**
        - Before using, a requirement is that the user needs to know which type of analysis to do Global K-Function vs. Cross K-Function Analysis. 
        - See parameters for description of Required and Optional inputs. 
         
### Questions (2/6/16):
New Bridge Points
Dissertation
Generate Network Dataset

ODCM - Distance from origin to distance

### Random Point Generation
Gives us our expected dataset to compare with the observed dataset.

We'd run K Function analyis on both datasets and generate upper and lower bounds using standard deviations. Points that fall within the bounds are indeed random, *but points that fall above the upper bound show us that there is potential clustering*
Uniform - Self Explantory
Non-Uniform - 

### Variable Distance X (Cross) K Function
Last Feature to implement. The question is how are we able to compare crashes on a curved road relative to other curved roads? Not all curved roads have the same length, so with the Variable Distance X K Function we question how far, proportionally, does a crash happen on a curved road. 25% of the way through the curve? 50%? 75%? Etc. 

### Non-Uniform Point Generation
Nonuniform determined by the amount of cars and the length of the segment
	Check dissertation ch 5 nonuniform

### Overview:
If we have 699 points, then our Global K Function raw data will have 699^2 entries. 

We generate random points with a uniform/nonuniform distribution to create an expected dataset. We use a confidence interval to determine the upper and lower bounds which we can compare with the observed data to determine whether crashes are clustered, dispersed, or random relative to each other


## What we did last week (2/13/16)
Figure out how to use previous groups work 

Get needed data set from Dr. K 

Found out how to plot points and show buffers using `Analysis->Proximity->Multiple Ring Buffer tools`

Generated table of planar distances betwee points using `Analysis->Proximity->Generate Near Table Tool`	

Needed to generate distance table using the network dataset so we researched and found out about the network analysis tools

- Used `Analysis->Make ODCM	Layer`
    - Used in tandem with `Add Locations` and `Solve Tools`
- Now need to validate that table

Checking previous groups random points on network dataset
	- Seems good to go. Need to check if 'Use Data field for point generation' works properly
		- Right click on Feature class in network dataset (ex. '139N') -> Properties -> SHAPE_length. This may be what we use for the data field

#### Get ramped up on the arcpy library. Look at Global K tool and use [this](http://desktop.arcgis.com/en/arcmap/10.3/analyze/arcpy/what-is-arcpy-.htm) as a reference
