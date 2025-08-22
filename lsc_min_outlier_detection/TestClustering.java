import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.util.StringTokenizer;

public class TestClustering{
	
	public static void main(String[] args)
	{
		//command line arguments for printing
		//only outliers, only normal points, all points
		int outputFlag = 0;
		boolean lof=false,lsc=false,nn=false;
		int lofthreshhold=-1,lscthreshhold=-1,nnthreshhold=-1;
		boolean boolLofThreshhold=false,boolNNThreshhold=false,boolLscThreshhold=false;
		String fileName = null;
		int numEntries;
		
		//expect the first command-line argument to be file name;
		fileName = args[0];
		
		//second command line argument should be number of records to be read from file
		numEntries = Integer.parseInt(args[1]);
		if(numEntries<=0)
		{
			System.out.println("No records to be read...exiting");
			System.exit(-1);
		}
		
		for(int i=1;i<args.length;i++)
		{
			if(args[i].contains("-lof"))
			{
				lof=true;
				if(args[i].contains("="))
				{
					boolLofThreshhold = true;
					String[] ts = args[i].split("=");
					lofthreshhold = Integer.parseInt(ts[1]);
				}

			}
			else if(args[i].contains("-lsc"))
			{
				lsc=true;
				if(args[i].contains("="))
				{
					boolLscThreshhold = true;
					String[] ts = args[i].split("=");
					lscthreshhold = Integer.parseInt(ts[1]);
				}

			}
			else if(args[i].contains("-nn"))
			{
				nn=true;
				if(args[i].contains("="))
				{
					boolNNThreshhold = true;
					String[] ts = args[i].split("=");
					nnthreshhold = Integer.parseInt(ts[1]);
				}
			}
			if(args[i].trim().equals("o"))
			{
				//System.out.println("o");
				outputFlag = Defines.OUTLIERS;
			}
			else if(args[i].trim().equals("n"))
			{
				//System.out.println("a");
				outputFlag = Defines.NORMAL;
			}
			else
			{
				//System.out.println("a");
				outputFlag = Defines.ALL;
			}
			
		}
		
		DataSet mySet = new DataSet();
		BufferedReader br = null;
		try {
			br = new BufferedReader(new FileReader(fileName));
			//System.out.println("opened file");
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			System.out.println("Could not open data file..exiting");
			System.exit(-1);
			//e.printStackTrace();
		}
		
		String s;
		int fileLines = 0;
		try{
			while((s = br.readLine()) != null && fileLines<numEntries)
			{
				if(s.charAt(0)!='*'){
					DataPoint tmp = new DataPoint();
					StringTokenizer st = new StringTokenizer(s);
					
					//tmp.addAttribute(st.nextToken().trim());						//timestamp
					tmp.setTimeStamp(st.nextToken().trim());
					
					tmp.addAttribute(Integer.parseInt(st.nextToken().trim()));		//count-src
					
					//tmp.addAttribute(st.nextToken().trim());						//src-ip
					tmp.setSrcIP(st.nextToken().trim());
					
					//tmp.addAttribute(Integer.parseInt(st.nextToken().trim()));		//count-dest
					
					//tmp.addAttribute(Integer.parseInt(st.nextToken().trim()));	//dest-ip											//dest-ip
					//tmp.setDestIP(st.nextToken().trim());
					
					tmp.addAttribute(Integer.parseInt(st.nextToken().trim()));		//count-anyport-src
					st.nextToken();													//anypor-src-ip
					
					mySet.addDataPoint(tmp);
					
				}
				else
				{}
				fileLines++;
			}
		}catch(Exception ex){
			ex.printStackTrace();
		}
		if(lsc){
			LSCMine testLSC = new LSCMine(mySet, outputFlag, lscthreshhold);
			//allow garbage collection
			testLSC = null;
		}
		if(lof){
			LOF testLOF = new LOF(mySet, outputFlag, lofthreshhold);
			//allow garbage collection
			testLOF = null;
		}
		if(nn){
			NN testNN = new NN(mySet, outputFlag, nnthreshhold);
		}
	}
}