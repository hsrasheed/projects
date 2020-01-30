Pre-Processing the tcpdump file:
1) Using Ethereal or TcpTrace, you can extract connection information using their options. We used "tcpout.list" file also provided at Darpa Website which is processed using the same procedure. 

To Extract Features:
1) Import the "tcpout.list" file into SQL Server using Import/Export utility of SQL Server. The table should be of the form as given in "tcpdata.sql". (use space as delimiter)
2) Execute the script "ExtractFeatures.sql" to create the stored procedure for extraction of Time Based Features. The output table is "FeatureTable".
3) You can also optionally execute the script "ExtractConnFeatures.sql" to create the stored procedure for extraction of Connection Based Features. The output table is "FeatureConnectons".
4) Export the output tables to text files using space as delimiter and input to the algorithms implemented in Java.