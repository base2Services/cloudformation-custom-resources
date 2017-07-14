/**
 * A Lambda function that returns data read from JSON file on S3 bucket
 **/


const CfnLambda = require('cfn-lambda');
const AWS = require('aws-sdk');

Logic = {
    ReadS3Json: function (bucket, key, callback) {
        var s3 = new AWS.S3();
        s3.getObject({Bucket: bucket, Key: key}, function (err, data) {
            if (err) {
                //return error
                callback(err, null);
            }
            else {
                //try parsing json file
                try {
                    callback(null, JSON.parse(data.Body.toString()))
                } catch (err) {
                    callback(err, null)
                }
            }
        });
    }
};


// return json file properties
var Create = (cfnRequestParams, reply) => {
    Logic.ReadS3Json(cfnRequestParams.Bucket, cfnRequestParams.Key, function (err, data) {
        if (err) {
            reply(err, `s3-${cfnRequestParams.Bucket}-${cfnRequestParams.Key}`)
        } else {
            reply(err, `s3-${cfnRequestParams.Bucket}-${cfnRequestParams.Key}`, data)
        }
    });
};

// return json file properties
var Update = (requestPhysicalID, cfnRequestParams, oldCfnRequestParams, reply) => {
    Logic.ReadS3Json(cfnRequestParams.Bucket, cfnRequestParams.Key, function (err, data) {
        if (err) {
            reply(err, requestPhysicalID)
        } else {
            reply(err, requestPhysicalID, data)
        }
    });
};

// return json file properties
var Delete = (requestPhysicalID, cfnRequestParams, reply) => {
    Logic.ReadS3Json(cfnRequestParams.Bucket, cfnRequestParams.Key, function (err, data) {
        if (err) {
            reply(err, requestPhysicalID)
        } else {
            reply(err, requestPhysicalID, data)
        }
    });
};

exports.handler = CfnLambda({
    Create: Create,
    Update: Update,
    Delete: Delete,
    TriggersReplacement: [],
    SchemaPath: [__dirname, 'schema.json']
});