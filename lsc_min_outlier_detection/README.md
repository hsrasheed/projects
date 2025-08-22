# Data Mining for Intrusion Detection

# Implementation of LSC-Mine Data Mining Algorithm for outlier detection

# Course project for Graduate Data Mining Course @ the University of Florida

Team Members (in alphabetical order):

* Aamir Ansari
* Dileep Perchani
* Hassan Rasheed
* Sachin Sanap

* the "sample" folder contains output files for our algorithms executed with the threshhold of 5 for all algorithms

	```bash
	java -Xmx400M TestClustering TcpData.txt 6000 -lof=5 -nn=5 -lsc=5 a
	```

* the "data" folder contains SQL Server 200 stored procedures and the original data set from the DARPA website (see data/README.txt for more details)

Included in this jar file are the following java files:

| File Name | Description |
| --- | ---|
| NN.java  | our implementation of the Nearest Neighbor Algorithm this file writes its output to NN_Output  |
| NNComparator.java  | a class used to sort points based on the nearest neigbor outlier	criteria |
| LOF.java  | our implementation of the Local Outlier Factor Algorithm this file writes its output to LOF_Output  |
|  LOFComparator.java | a class used to sort points based on the local outlier	factor criteria  |
| LSCMine.java  | our implementation of the Local Sparsity Coefficient Algorithm	this file writes its output to LSC_Output  |
| LSCComparator.java  | a class used to sort points based on the local sparsity coefficient	criteria  |
| TestClustering.java	  | a driver class that will execute NN, LOF and LSCMine |

## TestClustering usage

TestClustering can be started with the following arguments: 

```bash
javac TestClustering <Data File Name> <number of records> -<algorithm>(=<threshhold>) (o|a|n) 
```

* () denotes optional items
* algorithm can be one or more of: nn, lof, or lsc
* the threshold is the value below which the algorithm will consider the point a non-outlier if no threshold is specified, then all of the points will merely be output in sorted order
* the next parameter is the number of records to read from the file
* the o or a arguments allow the user to specify that they want
	* o: only outliers
	* a: all points
	* n: non-outlier points
* if none of these three are input, then the algorithms will just output all of the points

Examples:
```bash
java TestClustering TcpData.txt 4000 -lof=20 -nn=15 -lsc=80 a
java TestClustering OtherData	-lof o
java TestClustering MoreData	-lsc -nn=10 n
```

Other files in the jar:

* MAKEFILE a makefile that will compile the java source code, and execute TestClustering with default arguments
* TcpData.txt Our test data set -- the product of some data preprocessing on one of	the DARPA data sets.
				
NOTE: depending on the default settings for the environment java is executed in, it may
be necessary to specify a '-Xmx' argument to the java virtual machine to increase heap
space.