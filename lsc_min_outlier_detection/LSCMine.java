import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;

public class LSCMine
{
	ArrayList<Double> kdistances;
	ArrayList<ArrayList<DataPoint>> kdistanceNeighborhood;
	ArrayList<ArrayList<Double>> kdnDistances;
	ArrayList<ArrayList<Double>> reachabilityDistances;
	double[][] distances;
	double[] localSparsityRatio;
	//double[] neighborhoodDistanceTotal; 
	ArrayList<DataPoint> dataSet;
	//double globalPruningFactor;
	int allNeighborhoodSizes;
	BufferedWriter bw;
	boolean nonoutlieroutput = false;
	boolean outlieroutput = false;
	long startTime;
	
	
	public LSCMine(DataSet set, int outputFlag, int threshhold)
	{
		try {
			bw = new BufferedWriter(new FileWriter("LSC_Output", false));
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		startTime = System.nanoTime();
		dataSet = set.getDataSet();
		kdistances = new ArrayList<Double>();
		kdnDistances = new ArrayList<ArrayList<Double>>();
		kdistanceNeighborhood = new ArrayList<ArrayList<DataPoint>>();
		distances = new double[dataSet.size()][dataSet.size()];
		localSparsityRatio = new double[dataSet.size()];
		//neighborhoodDistanceTotal = new double[dataSet.size()];
		
		this.kdistanceCalculation();
		this.findkDistanceNeighborhood();
		this.computePruningFactor2();
		this.findCandidates();
		this.computeLocalSparsityCoefficient();
		LSCComparator lsccomparator = new LSCComparator();
		Collections.sort(dataSet, lsccomparator);
		
		int firstPt,ptLimit;
		
		if(outputFlag == Defines.OUTLIERS)
		{
			firstPt = 0;
			ptLimit = dataSet.size()/100;
		}
		else if(outputFlag == Defines.NORMAL)
		{
			firstPt = dataSet.size()/100;
			ptLimit = dataSet.size();
		}
		else
		{
			firstPt = 0;
			ptLimit = dataSet.size();
		}
		//System.out.println("1:"+firstPt+" 2:"+ptLimit);
		long finishTime = System.nanoTime();
		Log("Execution Time: "+(finishTime-startTime));
		Log("LSC\tSrc IP\t\t\tTimestamp");
		for(int i=0;i<dataSet.size();i++)
		{
			if(dataSet.get(i).localSparsityCoefficient>threshhold && (outputFlag == Defines.OUTLIERS||outputFlag == Defines.ALL))
			{
				if(this.outlieroutput == false && threshhold !=-1)
				{
					Log("*****OUTLIERS*****");
					this.outlieroutput = true;
				}
				Log(dataSet.get(i).print(Defines.LSC));
			}
			if(dataSet.get(i).localSparsityCoefficient<threshhold && (outputFlag == Defines.NORMAL||outputFlag == Defines.ALL))
			{
				if(this.nonoutlieroutput == false)
				{
					Log("*****NON-OUTLIERS*****");
					this.nonoutlieroutput = true;
				}
				Log(dataSet.get(i).print(Defines.LSC));
			}
			else if(dataSet.get(i).localSparsityCoefficient<threshhold && (outputFlag == Defines.OUTLIERS))
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
	 * Step1: Compute kdistances
	 * Step2: Find kdistance neighborhood
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
					if(firstMin == -1 || distance<firstMin)
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
			kdistances.add(i, new Double(Math.max(firstMin, secondMin)));
			
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
		
		for(int i=0;i<distances.length;i++)
		{
			ArrayList<DataPoint> myNeighborhood = new ArrayList<DataPoint>();
			ArrayList<Double> myNeighborDistances = new ArrayList<Double>();
			double myNeighborDistanceTotal = 0;
			double kdist = kdistances.get(i);
			for(int k=0;k<distances.length;k++)
			{
				if(distances[i][k] <= kdist && i!=k)
				{
					myNeighborhood.add(dataSet.get(k));
					myNeighborDistances.add(distances[i][k]);
					myNeighborDistanceTotal += distances[i][k];
				}
			}
			this.kdistanceNeighborhood.add(myNeighborhood);
			this.kdnDistances.add(myNeighborDistances);
			/*
			 * Step3: Compute local sparsity ration of each object
			 */
			this.localSparsityRatio[i] = myNeighborhood.size()/myNeighborDistanceTotal;
			dataSet.get(i).localSparsityRatio = localSparsityRatio[i];
			//this.neighborhoodDistanceTotal[i] = myNeighborDistanceTotal;
			dataSet.get(i).neighborhoodSize = myNeighborhood.size();
			dataSet.get(i).neighborhoodDistanceTotal = myNeighborDistanceTotal;
		}
	}
	/*
	 * Step4: Compute the pruning factor of each object
	 */
	public void computePruningFactor()
	{
		double sumNeighborhoodSizes = 0;
		int setSize = dataSet.size();
		for(int i=0;i<setSize;i++)
		{
			ArrayList<DataPoint> tmpNeighborhood = new ArrayList<DataPoint>();
			tmpNeighborhood = kdistanceNeighborhood.get(i);
			sumNeighborhoodSizes += tmpNeighborhood.size();
		}
		
		double sumNeigborhoodDistances = 0;
		for(int j=0;j<setSize;j++)
		{
			//sumNeigborhoodDistances += neighborhoodDistanceTotal[j];
		}
		//globalPruningFactor = sumNeighborhoodSizes/sumNeigborhoodDistances;
		//System.out.println("Pruning Factor: "+globalPruningFactor);
	}
	
	public void computePruningFactor2()
	{
		int setSize = dataSet.size();
		for(int i=0;i<setSize;i++)
		{
			double sumNeighborhoodSizes = 0.0;
			double sumNeighborhoodDistances = 0.0;
			double pf = 0.0;
			ArrayList<DataPoint> myNeighborhood = this.kdistanceNeighborhood.get(i);
			for(int j=0;j<myNeighborhood.size();j++)
			{
				sumNeighborhoodSizes += myNeighborhood.get(j).neighborhoodSize;
				sumNeighborhoodDistances += myNeighborhood.get(j).neighborhoodDistanceTotal;
			}			
			//sumNeighborhoodSizes += dataSet.get(i).neighborhoodSize;
			//sumNeighborhoodDistances += dataSet.get(i).neighborhoodDistanceTotal;
			pf = sumNeighborhoodSizes/sumNeighborhoodDistances;
			dataSet.get(i).pruningFactor = pf;
		}
	}
	/*
	 * Step5: Obtain the candidate set
	 */
	public void findCandidates()
	{
		for(int i=0;i<dataSet.size();i++)
		{	DataPoint tmpPt = dataSet.get(i);
		if(tmpPt.localSparsityRatio>=dataSet.get(i).pruningFactor)
		{
			dataSet.get(i).lscCandidate = false;
		}
		}
	}
	
	/*
	 * Step6: Compute LSC using candidate set
	 */
	public void computeLocalSparsityCoefficient()
	{
		int setSize = dataSet.size();
		
		for(int i=0;i<setSize;i++)
		{
			//We should get some speed up by only doing lsc calc.
			//for suspected outliers
			if(dataSet.get(i).lscCandidate){
				int neighborhoodSize = this.kdistanceNeighborhood.get(i).size();
				ArrayList<DataPoint> myNeighborhood = this.kdistanceNeighborhood.get(i);
				double sumRatios = 0.0;
				for(int j=0;j<myNeighborhood.size();j++)
				{				
					sumRatios += (myNeighborhood.get(j).localSparsityRatio)/(dataSet.get(i).localSparsityRatio);
				}
				if(i > 290)
				{
					System.out.print("");
				}
				dataSet.get(i).lsrNeighborRatio = sumRatios;
				double lsc = sumRatios/neighborhoodSize;
				dataSet.get(i).localSparsityCoefficient = lsc;
			}
		}
	}
	
	/*
	 * Step7: Rank outliers as those with highest local sparsity coefficients
	 */
	//just output instead
}