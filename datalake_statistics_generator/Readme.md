# Analyzing File Statistics for an Azure Data Lake Store
## Part 1
### Overview
The purpose of this series of articles is to explore a motivating example that will pull together the use of multiple Azure Big Data technologies to derive some interesting insights about our application and the data that it processes.

In Part 1 we will look at connecting to our Azure Data Lake Store (ADLS) instance, extracting the metadata about our files and storing that data for later analysis. In Part 2 we will look at querying and visualizing that data.

We will assume that we have an Azure Data Lake Store that gets data from multiple "source" systems. Each source system has one or more "feeds" that are dropped into our Data Lake at periodic intervals. Each time the feed is processed, it drops its files in a new folder with a time stamp to indicate the processing time.

We would like to calculate some aggregate statistics for each feed and source such as the number of files and the average file size.

To accomplish this, we will use the following:
* Azure Data Lake Store - Specifically, the file system client library will provide information about the files in our Data Lake. Reference documentation for the Python file system client library can be found [here](https://docs.microsoft.com/en-us/azure/data-lake-store/data-lake-store-data-operations-python). This article will not cover how to use an ADLS to store the initial set of files.
* HDInsight - Multiple Big Data services and tools are available with HDInsight. For this article, we will use the following:
  * Jupyter - provides an interactive execution environment for code in multiple languages through the web browser
  * Spark (through the PySpark library) - a cluster computing framework for big data processing. 
  * Hive - a framework for data warehousing on top of Hadoop that provides a SQL-like interface for querying. We will use it to persist our statistics for later use.
* Python - a widely used, object oriented programming language
  * Pandas - powerful library for manipulating data in DataFrames
  
### Step 1: Connecting to Our Azure Data Lake
We will import three classes from the python library for azure data lake store:

```python
from azure.datalake.store import core, lib, multithread
```
These libraries will allow us to authenticate to the Azure Data Lake Store service using our Tenant ID, a Service Principal ID and Client Secret. The following code snippet shows how we create a credentialing object and then, in turn use that to create an Azure Data Like file system Client
```python
  adlCreds = lib.auth(tenant_id='TENANT', client_secret='CLIENT_SECRET',
                  client_id='CLIENT_ID', resource = 'https://datalake.azure.net/')
  adl = core.AzureDLFileSystem(adlCreds, store_name='ADLS_STORE')
```
The primary filesystem call we will use is the ls method. With its default invocation, this method returns a list of the files and folders in the given path, for example:
```python
adl.ls("/")
```
Might return a python list that looks like this:
```python
['source1/','source2/','source3/','source4/']
```
If, however, we set the 'detail' parameter equal to True, then we will get back a list for each file or folder that contains multiple properties about each element:
```python
['accessTime', 'aclBit', 'blockSize', 'group', 'length','modificationTime', 'name', 'owner', 'pathSuffix', 'permission','replication', 'type']
```
The length property will be particularly useful for the data that we want to calculate. We have encapsulated the ADLS authentication and the file system calls into two methods which return a pandas data frame or a simple list
```python
def get_adls_file_dataframe(beginning_path):
  """returns a data frame with detailed system information using a adls file system client"""
  adlCreds = lib.auth(tenant_id='TENANT', client_secret='CLIENT_SECRET',
                  client_id='CLIENT_ID', resource = 'https://datalake.azure.net/')
  adl = core.AzureDLFileSystem(adlCreds, store_name='ADLS_STORE')
  return pd.DataFrame(adl.ls(beginning_path,detail=True))

def get_adls_file_list(beginning_path):
    """returns a data frame with detailed system information using a adls file system client"""
    adlCreds = lib.auth(tenant_id='TENANT', client_secret='CLIENT_SECRET',
                    client_id='CLIENT_ID', resource = 'https://datalake.azure.net/')
    adl = core.AzureDLFileSystem(adlCreds, store_name='ADLS_STORE')
    return pd.DataFrame(adl.ls(beginning_path))
```    
We assume a file system structure similar to the following

```<data_source>/<feed_name>/<processing_date_time>/<file_name>```
```
source1
      | - feed1
              | - 2018-07-21
                           | - file1
                           | - file2
              | - 2018-07-22
              | - 2018-07-23
                           | - file1
                           | - file2
                           | - file3                         
      | - feed2
              | - 2018-07-21
                           | - file1              
              | - 2018-07-22
                           | - file1              
              | - 2018-07-23
                           | - file1                         
source2
      | - feed1            
              | - 2018-07-23
                           | - file1              
              | - 2018-07-24
                           | - file1              
              | - 2018-07-25
                           | - file1               
```
### Step 2: Setting up Our Data Store
First let's setup our Hive Table.

```python
def create_stats_schema():
    fields = [StructField("SourceName", StringType(), True),
              StructField("FeedName", StringType(), True),
              StructField("ETL", StringType(), True),
              StructField("FileSize", IntegerType(), True),
              StructField("FileName", StringType(), True),
             ]
    schema = StructType(fields)
    my_new_df = spark.createDataFrame(spark.sparkContext.emptyRDD(), schema)
    my_new_df.write.partitionBy('SourceName','FeedName').saveAsTable("temp_data_lake_statistics")
    return
```
In the code above, we are defining a python function that creates a Spark Data Frame and then saves it as a Hive Table. We specify the list of fields in the table, using the `StructField` function. Then we specify the schema of the table using the `StructType` function. The table has five columns: SourceName, FeedName, ETL, FileSize and FileName. Next we create a spark dataframe using `createDataFrame` and finally we write that data frame to persistent storage using `saveAsTable` and specify the desired table name.

In addition, the Hive table is created with partitioning on SourceName and FeedName `partitionBy('SourceName','FeedName')` which will make our analysis queries run much faster.

### Step 3: Getting the Data About Our FileSystem
In this step, we will iterate through each of the sources and feeds in our Data Lake and aggregate statistics for each of the files. We created a set of recursive methods which traverse our directory tree and put the data into a Hive Table for us to analyze later. 

Next we will look at the code for the directory traversal. The first two levels of directory traversal (root and source levels) are pretty standard code and can be viewed in the [source file](https://gist.github.com/hr00/800c57055a28a1be789d48de97e441ff). 

#### Level 1 and 2 of directory traversal (Root and Source)

The code for the root and source level is almost identical:
```python
def process_root(path):
    #print("Process Root {}".format(path))
    current_element_name = get_path_suffix(path)
    sub_elements_df = get_adls_file_dataframe(path)
    if len(sub_elements_df) == 0: return
    for element in sub_elements_df['name']:
        element_df = sub_elements_df[sub_elements_df['name'] == element]
        element_type = element_df['type'].values[0]
        if element_type == 'DIRECTORY':
            process_sources(element)
    return
```
#### Level 3 of directory traversal (Feed)
The code for processing the feed directory is shown below:

```python
def process_feeds(path):
    #print("Process Feed {}".format(path))
    current_element_name = get_path_suffix(path)
    sub_elements_df = get_adls_file_dataframe(path)
    if len(sub_elements_df) == 0: return
    
    # Sample the original data frame that contains ETLs
    sampled_elements_df = sub_elements_df.sample(frac=0.10)
    accum_num_feed_files = spark.sparkContext.accumulator(0)
    feed_file_stats_df = pd.DataFrame(columns=['ETL','FileSize','FileName','SourceName','FeedName'])
    
    for element in sampled_elements_df['name']:
        element_df = sub_elements_df[sub_elements_df['name'] == element]
        element_type = element_df['type'].values[0]
        if element_type == 'DIRECTORY' and accum_num_feed_files.value<15:
            etl_stats_df = process_etls(element,accum_num_feed_files)
            if len(etl_stats_df) > 0:
                feed_file_stats_df = feed_file_stats_df.append(etl_stats_df)
    if len(feed_file_stats_df) > 0:
        df2 = spark.createDataFrame(feed_file_stats_df)
        df2.write.mode("append").insertInto("data_lake_statistics")
    return
```
A few important things to call out in this function above:
##### 1. Sampling
This code ```sampled_elements_df = sub_elements_df.sample(frac=0.10)``` takes the full dataframe of all of the ETLS for this feed and samples it, giving us a smaller dataset with the given percentage of total records (in this case 10%). So if there are 100 ETL dates processed for this feed, we will examine 10 of them.

##### 2. Using an accumulator
This line ```accum_num_feed_files = spark.sparkContext.accumulator(0)``` defines an accumulator which is essentially a global variable that persists across the spark cluster. In this case we will use the accumulator to limit the total number of files that are processed for any given feed. So, for example, if we set the file limit to 15 then we will look through all of the ETL dates in our sampled data frame and continue to add file statistics to our table until we hit that limit. Each time a file is processed, the accumulator is incremented.

##### 3. Appending the feed level data to our Hive table
The file data for multiple ETL dates is aggregated at the feed level `feed_file_stats_df = feed_file_stats_df.append(etl_stats_df)` and inserted to the Hive table at the end of the processing for that feed `df2.write.mode("append").insertInto("data_lake_statistics")`.

#### Level 4 of directory traversal (ETL and Files)
The code for processing at the ETL level is shown below:
```python
def process_etls(path, num_files):
    # This dataframe contains a list of all files processed on that day/time
    sub_elements_df = get_adls_file_dataframe(path)
    
    # Prepare a dataframe to contain the stats for all of the files processed on that day
    etl_stats_df = pd.DataFrame(columns=['ETL','FileSize','FileName','SourceName','FeedName'])
    
    # Error checking -- no files processed
    if len(sub_elements_df) == 0: return etl_stats_df
    
    for element in sub_elements_df['name']:
        element_df = sub_elements_df[sub_elements_df['name'] == element]
        element_type = element_df['type'].values[0]
        element_size = element_df['length'].values[0]
        
        # Check that we want to process this file
        if element_type == 'FILE' and element_size>1000:
            # Add file stats to Hive Table
            # Get all the different parts of the path
            path_parts = element.split("/")
            file_name = path_parts[-1]
            etl_stamp = path_parts[-2]
            feed_name = path_parts[-3]
            source_name = path_parts[-4]
            # Using a dict and adding it to the end of the dataframe is faster than appending a new data frame
            file_info_dict  = {'SourceName':source_name,'FeedName':feed_name,'ETL':etl_stamp,'FileSize':element_size,'FileName':file_name}
            etl_stats_df.loc[len(etl_stats_df)] = file_info_dict
            num_files.add(1)            
    return etl_stats_df
```
A few things to highlight with this last function:
##### 1. Incrementing our accumulator
This accumulator is used in the previous method to control how many files are analyzed. It is incremented in this function by calling `num_files.add(1) `.

##### 2. Filtering out smaller files
Using the following code `if element_type == 'FILE' and element_size>1000:`, we are filtering out some files smaller than 1KB which are typically used by systems like Azure Data Factory (ADF) to track processing and ingestion.

### Conclusion
In Part 1 of the Article we have covered connecting to our Azure Data Lake Store, retrieving statistics about our set of files and storing those statistics for later analysis. In Part 2, we will look at querying and analyzing the metadata that we have collected.
