import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.util.StringTokenizer;

public class TestClustering2{
	
	public static void main(String[] args)
	{
		//command line arguments for printing
		//only outliers, only normal points, all points
		int outputFlag = 0;
		boolean lof=false,lsc=false,nn=false;
		int lofthreshhold=0,lscthreshhold=0,nnthreshhold=0;
		
		for(int i=0;i<args.length;i++)
		{
			if(args[i].contains("-lof"))
			{
				lof=true;
				String[] ts = args[i].split("=");
				lofthreshhold = Integer.parseInt(ts[1]);
			}
			else if(args[i].contains("-lsc"))
			{
				lsc=true;
				String[] ts = args[i].split("=");
				lscthreshhold = Integer.parseInt(ts[1]);
			}
			else if(args[i].contains("-nn"))
			{
				nn=true;
				String[] ts = args[i].split("=");
				nnthreshhold = Integer.parseInt(ts[1]);
			}
			if(args[i].trim().equals("o"))
			{
				//System.out.println("o");
				outputFlag = Defines.OUTLIERS;
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
			br = new BufferedReader(new FileReader("TcpData.txt"));
			//System.out.println("opened file");
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
        
        String s;
        int fileLines = 0;
        try{
        	while((s = br.readLine()) != null && fileLines<5000)
        	{
        		if(s.charAt(0)!='*'){
        		DataPoint tmp = new DataPoint();
        		StringTokenizer st = new StringTokenizer(s);
        		
        		//tmp.addAttribute(st.nextToken().trim());						//timestamp
        		tmp.setTimeStamp(st.nextToken().trim());
        		
        		tmp.addAttribute(Integer.parseInt(st.nextToken().trim()));		//count-src
        		
        		//tmp.addAttribute(st.nextToken().trim());						//src-ip
        		tmp.setSrcIP(st.nextToken().trim());
        		
        		tmp.addAttribute(Integer.parseInt(st.nextToken().trim()));		//count-dest
        		
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
		if(lof){
		LOF testLOF = new LOF(mySet, outputFlag, lofthreshhold);
		testLOF = null;
		}
		if(lsc){
		LSCMine testLSC = new LSCMine(mySet, outputFlag, lscthreshhold);
		testLSC = null;
		}
		if(nn){
		NN testNN = new NN(mySet, outputFlag, nnthreshhold);
		}
	}
}