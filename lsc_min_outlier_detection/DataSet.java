import java.util.ArrayList;

public class DataSet{
	ArrayList<DataPoint> dataPoints;
	int pointID;
	public DataSet()
	{
		dataPoints = new ArrayList<DataPoint>();
		pointID = 0;
	}
	
	public void addDataPoint(DataPoint pt)
	{
		pt.ID = pointID;
		pointID++;
		dataPoints.add(pt);
	}
	
	public ArrayList<DataPoint> getDataSet(){return dataPoints;}
}