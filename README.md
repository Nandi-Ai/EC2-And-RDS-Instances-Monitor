<a ><img src="https://futurumresearch.com/wp-content/uploads/2020/01/aws-logo.png" width=300 height=200 title="AWS" alt="aws"></a>
<a ><img src="https://www.logimic.org/wp-content/uploads/2020/05/600px-AWS_Lambda_logo.svg_.png" width=200 height=200 title="AWS" alt="aws"></a>

# EC2 and RDS Instances status monitor by Lambda



## Description

Lambda function to monitor EC2 and RDS instances information

- The function goes over all regions that exist in the AWS account

- In each region goes over all EC2 and RDS instances and checks what the statuses of each of the instances are

- While further information is checked from dynamoDB of what the changes have been since the last information test done
 
- At the end of the tests function will send Email with the information via AWS SNS service 

- Now the new instances information will be stored in dynamoDB 

- All of which can be run using the CloudWatch service as scheduled

### Clone

- Clone this repository `git clone git@github.com:Nandi-Ai/EC2-And-RDS-Instances-Monitor.git`

## Services that this Lambda use

> Lambda

> IAM

> CloudWatch

> DynamoDB

> SNS



## Start working
> You should create all those services on the same region

**IAM roles**
> Add roles for allow Lambda function use services
- Go to roles tab in IAM service at AWS
- Click on `Create role`
- Choose Lambda on `Choose a use case` and Click on `Next Permissions`
- Search and check | `AmazonEC2FullAccess` | `AmazonSNSFullAccess` | `AmazonRDSReadOnlyAccess` |  `AmazonDynamoDBFullAccess` | 
- Click on `Next`, Fill role name and click on `Create role`

**SNS**
> Create SNS topic and subscription for send Email with the information
- Go to topics tab in SNS service at AWS
- Click on `Create topic`
- Fill topic name
- Fill display name - This is the title on the Email that will sent
- Click on `Create topic`
- Click on the topic that you created before
- Click on `Create subscription`
- Choose on Protocol `Email`
- Fill on Endpoint the Email that you want to use
- Click on `Create subscription`
- After that you need to accept this subscription on your mail box

**DynamoDB**
> Store the previous results on table and retrieve those results on comparing data
- Go to tables tab in dynamoDB service at AWS
- Click on `Create table`
- Fill Table name with `EC2Check` (Must be this name)
- Fill Primary key with `timestamp` (Must be this key) 
- Choose on Primary key type `Number`
- Click on `Create`
- Repeat on this section one more time and fill table name with `RdsCheck`  
- In the end you should have 2 table - `EC2Check` & `RdsCheck`  




**Lambda**
> Run a Python script that executes the whole process

*Now you need to add layers of python modules*

- Go to Layers tab in Lambda service at AWS
- Click on `Create layer`
- Fill Name with `datatime` 
- Click on `Upload`
- Choose `datatime.zip` that you've cloned from this repository
- Choose on Compatible runtimes `Python 3.6`
- Click on `Create`
- Repeat on this section one more time and choose `jsondiff.zip` and fill name `jsondiff`





*Now you got the python modules that you needs - you can create Lambda function*

- Go to Functions tab in Lambda service at AWS
- Click on `Create function`
- Fill Function name
- Choose on runtime `Python 3.6`
- Choose on Permissions `Use an existing role` 
- Choose on Existing role the role that you created on the IAM section 
- Click on `Create function`


*Now you created Lambda function - you can configure this function*

- Click on `Layers`
- Click on `Add a layer`
- Add `jsondiff` & `datatime` 
- Click on `Edit` on Basic settings
- Increment Memory to `2560MB` as much as the Memory is low the function run more slowly
- Change Timeout to 2 min (if Memory is under 2560MB increment the time)

*Now you configured Lambda function - you can copy the code into Function code*

- Copy code from `MonitorEC2AndRDSInstancesStatus.py` and paste in Function code 
- Add on `sendEmailBySNS` function to `TargetArn` variable the arn of the SNS topic that you've created before
- Add on `lambda_handler` function to `account` variable the right account name
- Click on `Save`
- Now you can test your function by click on `Test`
- You should receive Email with the results from the function



**CloudWatch**
> Run the Lambda code as scheduled
- Go to Rules tab in CloudWatch service at AWS
- Click on `Create rule`
- Choose on Event Source `Schedule`
- Fill on Fixed rate of the number that you want and choose `Minutes | Hours | Days`
- Click on `Add target` at Targets
- Choose `Lambda function`
- Choose the function that you created before
- Click on `Configure details`
- Fill Name 
- Click on `Create rule`






## License
- Copyright 2020 © Nandi