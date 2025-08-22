import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.rmi.RemoteException;

public class Logger {
	
	private BufferedWriter bw;
	
	public Logger()
	{
		try{
		BufferedWriter bw = new BufferedWriter(new FileWriter("c:\\lof_lsc_output", true));
		}catch(Exception ex){}
	}
	public synchronized void Log(String message){
		// TODO Auto-generated method stub
        try
        {
           //System.out.println(message);
           bw.write(message+"\n");
           bw.flush();
        }
        catch(IOException ex)
        {}
	}
}
