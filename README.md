# py-copy-sg-rules-aws


**1 - create aws.config**

aws_access_key_id=xxxxxx
aws_secret_access_key=xxxxxx
aws_session_token=xxxxxx

**2 - save rules**

<pre> ```bash python save_sg_rules.py --source-sg-id:sg-xxxxx --source-vpc-id:vpc-xxxxx --aws-region:us-east-1 ``` </pre>

<pre> ```bash python save_sg_rules.py --source-sg-id:sg-xxxxxx   --source-vpc-id:vpc-xxxxx --aws-region:us-east-x ``` </pre>

**3 - review/edit rules**

vi sg_rules.json

**4 - apply rules**

python apply-sg-rules.py --target-sg-id:sg-xxxx   --target-vpc-id:vpc-xxxx --aws-region:us-east-x
