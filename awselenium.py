import boto3
import requests

seleniumAsgName = ['Selenium-NODES-AutoScalingGroup']
seleniumGridIp = "192.168.1.1"
seleniumGridPort = "4444"
nodes = 0


def get_instance_ids():
    """
    Retrieves instances IDs by ASG name from AWS
    :return: List of IDs ready to query IP
    """
    instanceIdList = []
    ids = 0
    client = boto3.client('autoscaling')
    response = client.describe_auto_scaling_groups(AutoScalingGroupNames=seleniumAsgName)

    for instanceId in response["AutoScalingGroups"][0]["Instances"]:
        instanceIdList.append(instanceId["InstanceId"])
        ids += 1

    print "There are {0} nodes in AWS".format(ids)
    return instanceIdList


def get_instance_ips(idlist):
    """
    Retrievs IPs by querying AWS ec2 module
    :param idlist: List of IDs from get_instance_ids
    :return: List of IPs ready to test on selenium API
    """
    instanceIpList = []
    ec2client = boto3.client('ec2')
    for instanceid in idlist:
        ec2response = ec2client.describe_instances(InstanceIds=[instanceid])
        instanceIpList.append(ec2response["Reservations"][0]["Instances"][0]["PrivateIpAddress"])

    return instanceIpList


def test_selenium_connection(iplist):
    """
    Testing IPs with selenium API for connection and registration with the grid
    :param iplist:
    :return: list of disconnected IPs
    """
    global nodes
    disconnections = []
    for ip in iplist:
        url = 'http://{0}:{1}/grid/api/proxy?id=http://{2}:5555'.format(seleniumGridIp, seleniumGridPort, ip)
        answer = requests.get(url)
        print "IP {0}: {1}".format(ip, answer.json()["success"])
        if answer.json()["success"] is not True:
            disconnections.append(ip)

    nodes = len(iplist)
    return disconnections


def report_to_dashing(disconnections):
    """
    Reports to a specific dashing widget
    :param disconnections:
    """
    if len(disconnections) == 0:
        text = "{0} selenium nodes, all connected".format(nodes)
    else:
        text = "{0} selenium nodes, {1} disconnected: {2}".format(nodes, len(disconnections), ', '.join(disconnections))

    requests.post('http://<dashing IP>:<dashing port>/widgets/selenium-nodes',
                  data='{ "auth_token": "YOUR_AUTH_TOKEN", "text": "%s" }' % text)


def main():
    # 1. get_instance_ids
    # 2. get_instance_ips
    # 3. test_selenium_connection
    # 4. report_to_dashing

    report_to_dashing(test_selenium_connection(get_instance_ips(get_instance_ids())))


main()
