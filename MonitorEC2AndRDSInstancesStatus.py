import json
import boto3
import datetime
import calendar
from jsondiff import diff


def check_jsons_difference(newJsonData, table_name,
                           typeOfCheck):  # This function checks what was the results on the last time check and compare it to the new results
    try:
        stringOfAllData = typeOfCheck + "\n\n"  # All the data will added to this variable and finally it will send to email by sns

        lastItem, flagFirstItem = get_last_item_from_DB(table_name)
        if lastItem["data"] == [] and flagFirstItem:
            return typeOfCheck + "\nFirst time running - From now the data will be compared to the last time check"

        a, b = json.dumps(lastItem["data"], sort_keys=True), json.dumps(newJsonData["data"],
                                                                        sort_keys=True)  # Sort jsons - Last json item & new results json  (a=last time json | b=new json)
        resultFromDiff = json.loads(
            diff(json.loads(a), json.loads(b), dump=True))  # Diff module checks what is the difference between 2 jsons
        if resultFromDiff == {}:  # Nothing changed
            stringOfAllData += "There are the same results from last time"
        a = json.loads(a)
        flagValueUpdated = [False, ""]  # A flag that checks whether there is a change that is an update
        for key in resultFromDiff:

            if key == '$delete' or key == '$insert':

                for index in range(len(resultFromDiff[key])):  # Pass all over the results
                    if key == '$delete':
                        if not flagValueUpdated[0] or flagValueUpdated[1] != key:  # For adding Event: update once
                            stringOfAllData += "Event: Removed Instances" + "\n\n"  # Adding event type if its insert or delete
                            flagValueUpdated[0] = True  # Need to add one time to flag changed
                            flagValueUpdated[1] = key
                        jsonOfChanges = a[resultFromDiff[key][index]]  # Json of changes
                        if typeOfCheck == 'RDS':
                            stringOfAllData += "DB Name:" + jsonOfChanges["db_name"] + " | DB Type:" + jsonOfChanges[
                                "db_type"] + " | DB Engine:" + jsonOfChanges["engine"] + " | DB Region:" + \
                                               jsonOfChanges["region"] + "\n"
                        else:  # EC2
                            stringOfAllData += "Instance Name:" + jsonOfChanges["instance_name"] + " | Instance ID:" + \
                                               jsonOfChanges["instance_id"] + " | Instance Status:" + jsonOfChanges[
                                                   "status"] + " | Instance Region:" + jsonOfChanges["region"] + "\n"

                    elif key == '$insert':
                        if not flagValueUpdated[0] or flagValueUpdated[1] != key:  # For adding Event: update once
                            stringOfAllData += "Event: New Instances" + "\n\n"  # Adding event type if its insert or delete
                            flagValueUpdated[0] = True  # Need to add one time to flag changed
                            flagValueUpdated[1] = key

                        jsonOfChanges = resultFromDiff[key][index][1]  # Json of changes
                        if typeOfCheck == 'RDS':
                            stringOfAllData += "DB Name:" + jsonOfChanges["db_name"] + " | DB Type:" + jsonOfChanges[
                                "db_type"] + " | DB Engine:" + jsonOfChanges["engine"] + " | DB Region:" + \
                                               jsonOfChanges["region"] + "\n"
                        else:  # EC2
                            stringOfAllData += "Instance Name:" + jsonOfChanges["instance_name"] + " | Instance ID:" + \
                                               jsonOfChanges["instance_id"] + " | Instance Status:" + jsonOfChanges[
                                                   "status"] + " | Instance Region:" + jsonOfChanges["region"] + "\n"

            elif key.isdigit():  # If is digit thats mean its update - this is the index of the row that updated

                if not flagValueUpdated[0] or flagValueUpdated[1] != key:  # For adding Event: update once
                    stringOfAllData += "Event: Updated Instances\n\n"
                    flagValueUpdated[0] = True  # Need to add one time to flag changed
                    flagValueUpdated[1] = "&update"

                jsonOfChanges = resultFromDiff[key]  # Json of changes
                i = 0
                # Adding before and after changes
                if typeOfCheck == 'RDS':
                    stringOfAllData += "Before:" + "DB Name:" + a[int(key)]["db_name"] + " | DB Type:" + a[int(key)][
                        "db_type"] + " | DB Engine:" + a[int(key)]["engine"] + " | DB Region:" + a[int(key)][
                                           "region"] + "\n"
                    stringOfAllData += "The Changes:"
                    for keyOfJson in jsonOfChanges:  # For each update
                        if i > 0:
                            stringOfAllData += " | "
                        if keyOfJson == 'db_name':
                            stringOfAllData += "DB Name:" + jsonOfChanges[keyOfJson]
                        elif keyOfJson == 'db_type':
                            stringOfAllData += "DB Type:" + jsonOfChanges[keyOfJson]
                        elif keyOfJson == 'engine':
                            stringOfAllData += "DB Engine:" + jsonOfChanges[keyOfJson]
                        elif keyOfJson == 'region':
                            stringOfAllData += "DB Region:" + jsonOfChanges[keyOfJson]
                        i += 1
                else:  # EC2.
                    stringOfAllData += "Before:" + "Instance Name:" + a[int(key)]["instance_name"] + " | Instance ID:" + \
                                       a[int(key)]["instance_id"] + " | Instance Status:" + a[int(key)][
                                           "status"] + " | Instance Region:" + a[int(key)]["region"] + "\n"
                    stringOfAllData += "The Changes:"
                    for keyOfJson in jsonOfChanges:  # For each update
                        if i > 0:
                            stringOfAllData += " | "
                        if keyOfJson == 'instance_name':
                            stringOfAllData += "Instance Name:" + jsonOfChanges[keyOfJson]
                        elif keyOfJson == 'instance_id':
                            stringOfAllData += "Instance ID:" + jsonOfChanges[keyOfJson]
                        elif keyOfJson == 'status':
                            stringOfAllData += "Instance Status:" + jsonOfChanges[keyOfJson]
                        elif keyOfJson == 'region':
                            stringOfAllData += "Instance Region:" + jsonOfChanges[keyOfJson]
                        i += 1

                stringOfAllData += "\n\n"
            stringOfAllData += "\n"

        return stringOfAllData
    except Exception as e:
        print("check_jsons_difference:", e)
        return None


def get_last_item_from_DB(table_name):  # This function get table name and return the last item from table by timestamp
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table(table_name)
    allTable = table.scan()
    listOfRowsTimestamp = []
    i = 0
    for item in allTable["Items"]:  # Get all items
        i += 1
        listOfRowsTimestamp.append(int(item["timestamp"]))
    if i == 0:
        unixtime_date = datetime.datetime.utcnow()
        unixtime_now = calendar.timegm(unixtime_date.utctimetuple())
        insert_item({"timestamp": unixtime_now, "data": []}, table_name)  # First time
        return [{"timestamp": unixtime_now, "data": []}, True]
    lastTimestamp = max(listOfRowsTimestamp)  # Check what is the biggest timestamp (Last time check)
    lastItem = None
    for item in allTable["Items"]:
        if int(item["timestamp"]) == lastTimestamp:
            lastItem = item  # Save the last item to variable
            break
    return [lastItem, False]


def check_all_regions_RDS_instances():  # This function return json with the data about RDS's status
    ec2 = boto3.client('ec2')
    regions = ec2.describe_regions()
    listToInsert = []
    unixtime_date = datetime.datetime.utcnow()
    # Unixtime now
    unixtime_now = calendar.timegm(unixtime_date.utctimetuple())
    for region in regions['Regions']:  # Pass all over regions
        regionName = region['RegionName']
        client = boto3.client('rds', region_name=regionName)
        response = client.describe_db_instances()  # Get all RDS instance of region
        i = 0
        for item in response["DBInstances"]:
            i += 1
            jsonOfData = {"db_name": str(item["DBInstanceIdentifier"]), "db_type": str(item["DBInstanceClass"]),
                          "engine": str(item["Engine"]), "region": str(regionName)}  # Data of the RDS
            listToInsert.append(jsonOfData)
        jsonToInsert = {"timestamp": unixtime_now, "data": listToInsert}

    return jsonToInsert


def insert_item(jsonToInsert, table_name):  # This function get data to insert into dynamoDB by table name
    dynamo = boto3.resource('dynamodb')
    # Insert the data into the DynamoDB
    table = dynamo.Table(table_name)
    table.put_item(
        TableName=table_name,
        Item=json.loads(json.dumps(jsonToInsert))
    )


def send_email_by_SNS(message):  # This function send Emails by SNS Service
    client = boto3.client('sns')
    response = client.publish(
        TargetArn='',
        Message=message,
        MessageStructure='text'
    )


def check_all_regions_ec2_instances():  # This function check all regions EC2 Instances status
    ec2 = boto3.client('ec2')
    listOfJsons = []
    regions = ec2.describe_regions()
    unixtime_date = datetime.datetime.utcnow()
    # Unixtime now
    unixtime_now = calendar.timegm(unixtime_date.utctimetuple())
    returnMessage = [str("EC2 Instances\n")]
    for region in regions['Regions']:  # Pass all over regions
        regionName = region['RegionName']
        ec2 = boto3.client('ec2', region_name=regionName)
        instances = ec2.describe_instances()
        fullListInstances = instances['Reservations']
        if fullListInstances == []:
            continue
        else:
            rangeOfList = len(fullListInstances)
            countHowMuchRunning = 0
            for index in range(rangeOfList):
                for instance in fullListInstances[index]['Instances']:
                    instanceRow = ""
                    instanceName = "No Name"  # For case that EC2 Instance dose'nt has name
                    if instance['State']['Name'] == 'running' and countHowMuchRunning == 0:
                        returnMessage.append("\n\n" + str(regionName + ": "))

                    if 'Tags' in instance:
                        tagsLength = len(instance['Tags'])
                        for indexTag in range(tagsLength):  # Get The Name
                            if instance['Tags'][indexTag]["Key"] == 'Name':
                                if instance['State']['Name'] == 'running':  # For display only running instances
                                    instanceRow += str("Instance Name:" + instance['Tags'][indexTag]["Value"]) + " | "
                                instanceName = instance['Tags'][indexTag]["Value"]  # Get Instance name anyway

                    if instance['State']['Name'] == 'running':
                        instanceRow += str("Instance ID:" + instance['InstanceId']) + " | "
                        instanceRow += str("Instance Type:" + instance['InstanceType']) + " | "
                        instanceRow += str("Instance State:" + instance['State']['Name'])
                        countHowMuchRunning += 1
                        returnMessage.append(str(instanceRow))
                        # Json of status to insert into dynamoDB

                    # Data of the EC2 to insert into dynamoDB
                    jsonOfData = {"instance_name": str(instanceName), "instance_id": str(instance["InstanceId"]),
                                  "status": str(instance['State']['Name']), "region": str(regionName)}

                    listOfJsons.append(jsonOfData)

            if countHowMuchRunning == 0:
                continue  # If there are no running instances
            else:
                returnMessage.append("\n\n" + str("There Are " + str(
                    countHowMuchRunning) + " Running Instances On This Region (" + regionName + ")"))  # Only if there are running instances
    jsonToInsert = {"timestamp": unixtime_now, "data": listOfJsons}
    listToReturn = [jsonToInsert, "\n".join(returnMessage)]
    return (listToReturn)


def lambda_handler(event, context):
    try:
        # List of json of data & string to send by SNS
        jsonOfInstancesStatus, stringOfCurrentInstancesStatus = check_all_regions_ec2_instances()
        jsonOfRDSStatus = check_all_regions_RDS_instances()
        stringEC2ToSendToSNS = stringOfCurrentInstancesStatus + "\n\n" + check_jsons_difference(jsonOfInstancesStatus,
                                                                                                "EC2Check", "EC2")
        stringRDSToSendToSNS = "\n\n\n" + check_jsons_difference(jsonOfRDSStatus, "RdsCheck", "RDS")

        # Send emails by SNS
        # Add account name
        accountName = "AccountName"
        send_email_by_SNS("Account :" + accountName + "\n\n" + stringEC2ToSendToSNS + stringRDSToSendToSNS)

        # Update dynamoDB with new data
        insert_item(jsonOfRDSStatus, "RdsCheck")  # Update the table with the new results
        insert_item(jsonOfInstancesStatus, "EC2Check")  # Update the table with the new results
        print("Process Success")
        return {
            'statusCode': 200,
            'body': 'success'
        }
    except Exception as e:
        print("Lambda handler:", e)
        return {
            'statusCode': 500,
            'body': 'failed'
        }
