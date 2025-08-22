import java.util.ArrayList;

public class DataPoint{
	
	ArrayList<String> stringAttributes;
	ArrayList<Integer> integerAttributes;
	double reachabilityDensity;
	double localOutlierFactor;
	double localSparsityRatio;
	double localSparsityCoefficient;
	double kdistance;
	double lsrNeighborRatio;
	boolean lscCandidate;
	double neighborhoodSize;
	double neighborhoodDistanceTotal;
	double pruningFactor;
	int ID;
	private String srcIP;
	private String destIP;
	private String timeStamp;
	
	//TWO Options:
	/*
	 * 1 - Initialize all attributes in the constructor
	 * 
	 * 2 - use a setAttribute(Object val) that
	 */
	
	public DataPoint()
	{
		stringAttributes = new ArrayList<String>();
		integerAttributes = new ArrayList<Integer>();
		reachabilityDensity = 0;
		lscCandidate = true;
	}
	
	public void setSrcIP(String ip)
	{
		this.srcIP = ip;
		this.addAttribute(ip);
	}
	
	public void setDestIP(String ip)
	{
		this.destIP = ip;
		this.addAttribute(ip);
	}
	
	public void setTimeStamp(String stamp)
	{
		this.timeStamp = stamp;
		this.addAttribute(stamp);
	}
	
	public ArrayList<String> getStringAttributes()
	{
		return stringAttributes;
	}
	
	public ArrayList<Integer> getIntegerAttributes()
	{
		return integerAttributes;
	}
	
	public void addAttribute(String value)
	{
		stringAttributes.add(value);
	}
	
	public void addAttribute(int value)
	{
		integerAttributes.add(new Integer(value));
	}
	
	public String toString()
	{
		StringBuilder sb = new StringBuilder();
		sb.append('\n');
		sb.append("Source IP: "+this.srcIP+'\n');
		for(int i=0;i<stringAttributes.size();i++)
		{
			if(i!=0)
			{sb.append(" | ");}
			sb.append(stringAttributes.get(i));
		}
		sb.append('\n');
		for(int i=0;i<integerAttributes.size();i++)
		{
			if(i!=0)
			{sb.append(" | ");}
			sb.append(integerAttributes.get(i));
		}
		sb.append('\n');
		sb.append("lsr: "+this.localSparsityRatio+" lsc: "+this.localSparsityCoefficient+" rd: "+this.reachabilityDensity+" lof: "+this.localOutlierFactor);
		sb.append('\n');
		sb.append("lscCandidate: "+this.lscCandidate+" kdistance: "+this.kdistance +" lsr ratio sum: "+ this.lsrNeighborRatio);
		sb.append('\n');
		sb.append("ns:"+this.neighborhoodSize+"ndt:"+this.neighborhoodDistanceTotal+"pruning factor: "+this.pruningFactor);
		sb.append('\n');
		//sb.append("******" + '\n');
		return sb.toString();
	}
	
	public String print(int outputFlag)
	{
		StringBuilder sb = new StringBuilder();
		//sb.append('\n');
		//sb.append('\n');
		if(outputFlag == Defines.LOF)//LOF
		{
			sb.append((int)this.localOutlierFactor+"\t");
		}
		else if(outputFlag == Defines.LSC)//LSC
		{
			sb.append((int)this.localSparsityCoefficient+"\t");
		}
		else if(outputFlag == Defines.NN)//NN
		{
			sb.append((int)this.kdistance+"\t");
		}
		sb.append(this.srcIP+'\t');
		//sb.append(this.destIP+'\t');
		sb.append(this.timeStamp+'\t');
		//sb.append("******" + '\n');
		return sb.toString();
	}

	public double distanceTo(DataPoint otherPoint)
	{
		ArrayList<String> otherPointStrings = otherPoint.getStringAttributes();
		ArrayList<Integer> otherPointInts = otherPoint.getIntegerAttributes();
		
		double distance = 0;
		
		for(int j=0;j<otherPointStrings.size();j++)
		{
			if(otherPointStrings.get(j).compareTo(stringAttributes.get(j)) != 0)
			{
				distance++;
			}
		}
		
		for(int k=0;k<otherPointInts.size();k++)
		{
			distance += Math.pow(otherPointInts.get(k).intValue()-integerAttributes.get(k).intValue(),2);
		}
		return Math.sqrt(distance);
	}
}