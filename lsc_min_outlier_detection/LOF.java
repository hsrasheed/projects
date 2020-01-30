import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;

public class LOF{

	ArrayList<Double> kdistances;
	ArrayList<ArrayList<DataPoint>> kdistanceNeighborhood;
	ArrayList<ArrayList<Double>> kdnDistances;
	ArrayList<ArrayList<Double>> reachabilityDistances;
	double[] localOutlierFactor;
	double[][] distances;
	double[] reachabilityDensity;
	long startTime;
	//int[][] reachabilityDistances;
	
	ArrayList<DataPoint> dataSet;
	BufferedWriter bw;
	boolean nonoutlieroutput = false;
	boolean outlieroutput = false;
	
	public LOF(DataSet set, int outputFlag, int threshhold)
	{
		startTime = System.nanoTime();
		dataSet = set.getDataSet();
		
		try {
			bw = new BufferedWriter(new FileWriter("LOF_Output", false));
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		kdistances = new ArrayList<Double>();
		kdistanceNeighborhood = new ArrayList<ArrayList<DataPoint>>();
		kdnDistances = new ArrayList<ArrayList<Double>>();
		reachabilityDistances = new ArrayList<ArrayList<Double>>();
		localOutlierFactor = new double[dataSet.size()];
		distances = new double[dataSet.size()][dataSet.size()];
		reachabilityDensity = new double[dataSet.size()];
		//reachabilityDistances = new int[dataSet.size()][dataSet.size()];
		//System.out.println(kdistanceNeighborhood.get(0).size());
		this.kdistanceCalculation();
		this.findkDistanceNeighborhood();
		this.computeReachability();
		this.computeLOF();
		LOFComparator comparator = new LOFComparator();
		Collections.sort(dataSet, comparator);
		
		int firstPt,ptLimit;
		if(outputFlag == Defines.OUTLIERS)
		{
			//System.out.println("F1");
			firstPt = 0;
			ptLimit = dataSet.size()/100;
		}
		else if(outputFlag == Defines.NORMAL)
		{
			//System.out.println("F2");
			firstPt = dataSet.size()/100;
			ptLimit = dataSet.size();
		}
		else
		{
			//System.out.println("F3");
			firstPt = 0;
			ptLimit = dataSet.size();
		}
		
		long finishTime = System.nanoTime();
		Log("Execution Time: "+(finishTime-startTime));
		Log("LOF\tSrc IP\t\t\tTimestamp");
		for(int i=0;i<dataSet.size();i++)
		{
			if(dataSet.get(i).localOutlierFactor>threshhold && (outputFlag == Defines.OUTLIERS||outputFlag == Defines.ALL))
			{
				if(this.outlieroutput == false && threshhold !=-1)
				{
					Log("*****OUTLIERS*****");
					this.outlieroutput = true;
				}
				Log(dataSet.get(i).print(Defines.LOF));
			}
			if(dataSet.get(i).localOutlierFactor<threshhold && (outputFlag == Defines.NORMAL||outputFlag == Defines.ALL))
			{
				if(this.nonoutlieroutput == false)
				{
					Log("*****NON-OUTLIERS*****");
					this.nonoutlieroutput = true;
				}
				Log(dataSet.get(i).print(Defines.LOF));
			}
			if(dataSet.get(i).localOutlierFactor<threshhold && (outputFlag == Defines.OUTLIERS))
			{
				break;
			}
		}
        try {
			bw.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
	}
	
    public synchronized void Log(String message)
    {
       try
       {
          bw.write(message+"\n");
       }
           catch(Exception ex)
          {ex.printStackTrace();}
    }
	
	/*
	 * Step1: Computing kdistance of p:
	 i. First, compute the distances of all objects from P1 using a distance function. 
	 ii. Next, select the first 2 distinct minimum distances from P1. All distances from P1 are ordered and
	 the first 2 minimum distinct distances are chosen (i.e., Min(P1P2 = 4, P1P3 = 3, P1P4 = 7)).
	 iii. Finally, the maximum of the first 2 minimum distinct distances is selected as kdistance of P1.
	 Thus, kdistance(P1) = max(3, 4), hence, kdistance(P1) = 4. The kdistances of the remaining objects
	 are similarly obtained.
	 */
	public void kdistanceCalculation()
	{

		for(int i=0;i<dataSet.size();i++)
		{
			double firstMin=-1;
			double secondMin=-1;
			DataPoint currentPoint = dataSet.get(i);
			for(int j=0;j<dataSet.size();j++)
			{
				if(j!=i)
				{
					DataPoint ptToTest = dataSet.get(j);
					double distance = currentPoint.distanceTo(ptToTest);
					distances[i][j] = distance;
					if(firstMin== -1 || distance<firstMin)
					{
						firstMin = distance;
					}
					else if(secondMin == -1 || distance < secondMin)
					{
						secondMin = distance;
					}
				}
				else
				{
					distances[i][j] = 99999;
				}
			}
			Double kd = new Double(Math.max(firstMin, secondMin));
			//System.out.println("DP "+i+" kdistance: "+kd);
			kdistances.add(i, kd);
			dataSet.get(i).kdistance = kd;
		}
	}
	
	/*
	 * Step 2: Finding kdistance neighborhood of p
	 The kdistance neighborhood of p denoted (Nk(p)), contains every object with distance not greater than
	 kdistance(p). The rationale for computing the kdistance neighborhood is to find the nearest neighbors
	 of each object. For instance, kdistance neighborhood of P1 contains P2 and P3 since kdistance (P1) is 4
	 and the distances of P2 and P3 from P1 are each not more than 4 (i.e., P1P2 = 4, P1P3 = 3)
	 */
	public void findkDistanceNeighborhood()
	{

		for(int i=0;i<dataSet.size();i++)
		{
			ArrayList<DataPoint> myNeighborhood = new ArrayList<DataPoint>();
			ArrayList<Double> myNeighborDistances = new ArrayList<Double>();
			double kdist = kdistances.get(i);
			for(int k=0;k<distances.length;k++)
			{
				if(distances[i][k] <= kdist && i!=k)
				{
					myNeighborhood.add(dataSet.get(k));
					myNeighborDistances.add(distances[i][k]);
				}
			}
			this.kdistanceNeighborhood.add(myNeighborhood);
			this.kdnDistances.add(myNeighborDistances);
		}
	}
	
	
	/*
	 * Step 3: Computing reachability distance of p
	 The reachability distance of an object p with respect to object o is the distance(p, o) or kdistance(o)
	 whichever is larger (reachdistk(p,o) = max{kdistance(o), distance(p,o)). The objective is to ensure that
	 all the objects within a neighborhood are homogeneous. In addition, LOF stabilizes when the objects
	 within a neighborhood are uniform even if MinPts (k) changes. The fluctuations in the reachability
	 distances can be controlled by choosing large values for k [4]. The reachability distance of P1 is
	 computed as follows: First, identify kdistance neighborhood of P1 (i.e., Nk(P1) = (P2, P3)). The
	 reachability distance of P1 is computed with respect to P2 and P3 since they constitute the neighbors of
	 P1.
	 For P2 within the neighborhood of P1: reachdistk(P1, P2) = max(kdistance(P2), distance((P1,P2)) = max
	 (5,4) = 5. Since kdistance(P2) = 5 and distance(P1,P2) = 4
	 For P3 within the neighborhood of P1: reachdistk(P1,P3) = max{kdistance(P3), distance(P1,P3)} =
	 max (5, 3) = 5. Hence, reachdistk(P1,o) = (5, 5), which is the combination of reachability distances of
	 the neighbors of P1.
	 */
	public void computeReachability()
	{
		for(int i=0;i<dataSet.size();i++)
		{
			double localrdsum = 0;

			ArrayList<Double> myNeighborDistances = kdnDistances.get(i);
			ArrayList<DataPoint> myNeighbors = this.kdistanceNeighborhood.get(i);
			int neighborhoodSize = myNeighborDistances.size();

			for(int j=0;j<neighborhoodSize;j++)
			{
				double rd = Math.max(myNeighborDistances.get(j).intValue(), myNeighbors.get(j).kdistance);
				localrdsum += rd;
			}
			
			/*
			 * Step 4: Computing the local reachability density of p
			 */			
			double reach = 1/(localrdsum/neighborhoodSize);
			dataSet.get(i).reachabilityDensity = reach;
		}
	}
	
	/*
	 * Step 5: Local outlier factor of p
	 The local outlier factor is a ratio that determines whether or not an object is an outlier with respect to
	 its neighborhood. The local outlier factor of an object p denoted LOFk(p) is the average of the ratios of
	 local reachability density of p and that of p’s knearest neighbors.
	 */
	public void computeLOF()
	{
		for(int i=0;i<dataSet.size();i++)
		{
			int neighborhoodSize = this.kdistanceNeighborhood.get(i).size();
			ArrayList<DataPoint> myNeighbors = this.kdistanceNeighborhood.get(i);
			double lrdSum = 0.0;
			for(int j=0;j<neighborhoodSize;j++)
			{
				//lrdSum += myNeighbors.get(j).reachabilityDensity;
				lrdSum += (myNeighbors.get(j).reachabilityDensity)/(dataSet.get(i).reachabilityDensity);
			}
			double tempLOF = lrdSum/neighborhoodSize;
			this.localOutlierFactor[i] = tempLOF;
			dataSet.get(i).localOutlierFactor = tempLOF;
		}
	}
	
}