import boto3
import json
import sys

# === CONFIG ===
CONFIG_FILE = 'aws.config'
INPUT_FILE = 'sg_rules.json'

# --- Load AWS credentials ---
def load_aws_credentials(path):
    creds = {}
    with open(path, 'r') as f:
        for line in f:
            if line.strip() and '=' in line:
                key, val = line.split('=', 1)
                creds[key.strip()] = val.strip()
    return creds

# --- Extract CLI argument ---
def get_argument(name_prefix):
    for arg in sys.argv:
        if arg.startswith(name_prefix + ":"):
            return arg.split(":", 1)[1]
    print(f"❌ Missing required argument: {name_prefix}:<value>")
    sys.exit(1)

# --- Compare two rules (normalize for set-like comparison) ---
def rule_to_tuple(rule):
    return (
        rule.get('IpProtocol'),
        rule.get('FromPort'),
        rule.get('ToPort'),
        tuple((ip.get('CidrIp'), ip.get('Description', '')) for ip in rule.get('IpRanges', [])),
        tuple((ip.get('CidrIpv6'), ip.get('Description', '')) for ip in rule.get('Ipv6Ranges', [])),
        tuple((g.get('GroupId'), g.get('Description', '')) for g in rule.get('UserIdGroupPairs', [])),
    )

# --- Required CLI args ---
target_sg_id = get_argument("--target-sg-id")
target_vpc_id = get_argument("--target-vpc-id")
aws_region = get_argument("--aws-region")

# --- Initialize AWS session ---
creds = load_aws_credentials(CONFIG_FILE)
ec2 = boto3.client(
    'ec2',
    region_name=aws_region,
    aws_access_key_id=creds.get('aws_access_key_id'),
    aws_secret_access_key=creds.get('aws_secret_access_key'),
    aws_session_token=creds.get('aws_session_token')
)

# --- Load existing SG rules ---
existing_sg = ec2.describe_security_groups(GroupIds=[target_sg_id])['SecurityGroups'][0]
existing_ingress = [rule_to_tuple(r) for r in existing_sg['IpPermissions']]
existing_egress = [rule_to_tuple(r) for r in existing_sg['IpPermissionsEgress']]

# --- Load rules to apply ---
with open(INPUT_FILE) as f:
    data = json.load(f)

print(f"✅ Target SG: {target_sg_id}")
print(f"✅ Target VPC: {target_vpc_id}")
print(f"✅ AWS Region: {aws_region}")

# --- Separate rules by direction ---
ingress_rules = []
egress_rules = []

for rule in data['Rules']:
    ip_permission = {
        'IpProtocol': rule['IpProtocol'],
        'FromPort': rule.get('FromPort'),
        'ToPort': rule.get('ToPort'),
    }

    if 'CidrIpv4' in rule:
        ip_permission['IpRanges'] = [{
            'CidrIp': rule['CidrIpv4'],
            'Description': rule.get('Description', '')
        }]
    if 'CidrIpv6' in rule:
        ip_permission['Ipv6Ranges'] = [{
            'CidrIpv6': rule['CidrIpv6'],
            'Description': rule.get('Description', '')
        }]
    if 'ReferencedGroupInfo' in rule:
        ip_permission['UserIdGroupPairs'] = [{
            'GroupId': rule['ReferencedGroupInfo']['GroupId'],
            'Description': rule.get('Description', '')
        }]

    rule_key = rule_to_tuple(ip_permission)

    if rule['IsEgress']:
        if rule_key in existing_egress:
            print(f"⚠️ Skipping existing egress rule: {rule_key}")
        else:
            egress_rules.append(ip_permission)
    else:
        if rule_key in existing_ingress:
            print(f"⚠️ Skipping existing ingress rule: {rule_key}")
        else:
            ingress_rules.append(ip_permission)

# --- Apply rules ---
if ingress_rules:
    ec2.authorize_security_group_ingress(
        GroupId=target_sg_id,
        IpPermissions=ingress_rules
    )
    print("✅ Ingress rules applied.")

if egress_rules:
    ec2.authorize_security_group_egress(
        GroupId=target_sg_id,
        IpPermissions=egress_rules
    )
    print("✅ Egress rules applied.")
