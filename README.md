# base2 Cloudformation custom resources

This project will contain the code and configuration to deploy various Cloudformation custom resources.

## Custom resources

### S3 Bucket cleanup

Removes all keys within a bucket. Role assumed by Lambda needs to have appropriate 
permissions to remove bucket keys, commonly set through Bucket policies.  
Cleanup logic is implemented in 'DELETE' action. 'CREATE' and 'UPDATE'
actions are just dummy stubs.

handler: `src/cleanup-s3-bucket/index.handler`

Required parameters: 
- `BucketName` - String. Name of the bucket that should have it's keys cleaned up




### ENI Cleanup

Detaches (if requiered) and deletes all ENIs within specified subnets.
Cleanup logic is implemented in 'DELETE' action. 'CREATE' and 'UPDATE'
actions are just dummy stubs.

handler: `src/cleanup-subnet-enis/index.hanlder`

Required parameters:
- `SubnetIds` - Array of Strings. Self explanitory - all subnets within this area
shall have their ENI's cleaned up on stack deletion


### Route 53 DNS Records creation

Creates, Updates and Cleans up Rotue53 DNS records in specified zone. All
operations are done using assumed role that is passed down as Custom Resource
parameters

handler: `src/route53-changeset/index.handler`

Required parameters:
- `role` - ARN of role that should be assumed by Custom Resource. It's assumed
that user would just directly create Route53 records using supported resource 
types in same account where stack resides - so this is mandaroty parameter, as
custom resource is intended to be used for managing records in account diferent 
from where stack is being created. This custom resource is making appropriate API calls 
for all 3 operations - CREATE, UPDATE and DELETE. 

- `recordset` - json object with following properties
- - `ttl` - TTL for recrod set
- - `zoneId` - Route53 zone id where record should be created (PRs welcome to move from zoneId to ZoneName)
- - `type` - DNS Record type, e.g. `A`, `CNAME` ...
- - `value` - Actual value of DNS record


### Reading values from JSON file on S3 bucket

Reads values from JSON file placed in S3 bucket, allowing this values to be referenced in other resources.
Example of creating s3 bucket with name specified within JSON file can be found in `src/read-s3-json-file/cf_template_example.json`

handler: `src/read-s3-json-file/index.handler`

Required parameters:
- `Bucket` - name of bucket where configuration file resides
- `Key` - key within bucket of configuration file

Optional parameters:
- `EnsureKeys` - comma separated list of keys that are always returned out of custom resource. This ensures your 
   Cloud formation does not break if property that does not exist in JSON file is passed around the stack. Key values
   will default to empty string, or value of `EmptyKeyDefaultValue` parameter
   
- `EmptyKeyDefaultValue` value for keys not present in JSON file and requested by `EnsureKeys` 

### Creating cloudformation stack in specific region

It is easy to create sub-stacks in CloudFormation as long as they are in same region.
In some cases, there is need to create stack in region different than region where
parent stack is being create, or for example, to create same stack in multiple regions.
Such (sub)stack lifecycle can be controlled via custom resource having it's code in 
`src/regional-cfn-stack` folder

handler: `src/regional-cfn-stack/handler.lambda_handler`
runtime: `python3.6`

Required parameters:
- `Region` - AWS Region to create stack in
- `StackName` - Name of the stack to be created
- `TemplateUrl` - S3 Url of stack template
- `Capabilities` - Comma seperated list of capabilities. Set to empty value if no IAM capabilities required.
- `EnabledRegions` - Comma separated list of regions that stack is allowed to be created in.
 Useful when passing this list is template parameters. 


Optional parameters:
- `StackParam_Key` - Will pass value of this param down to stack's `Key` parameter
- `OnFailure` - Behaviour on stack creation failure. Accepted values are `DO_NOTHING`,`ROLLBACK` and `DELETE`

### Copy or unpack objects between S3 buckets

This custom resource allows copying from source to destination s3 buckets. For source, if you provide prefix
(without trailing slash), all objects under that prefix will be copied. Alternatively, if you provide s3 object
with `*.zip` extensions, this object will be unpacked before it's files are unpacked to target bucket / prefix. 
Please note that this lambda function design does not include recursive calls if lambda is timing out, thus it does not 
permit mass file unpacking, but is rather designed for deployment of smaller files, such as client side web applications.

handler: `src/s3-copy/handler.lambda_handler`
runtime:  `python3.6`

Required parameters:

- `Source` - Source object/prefix/zip-file in `s3://bucket-name/path/to/prefix/or/object.zip` format
- `Destination` - Destination bucket and prefix in `s3://bucket-name/destination-prefix` format

No optional parameters. 




