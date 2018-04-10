var grunt = require('grunt');
grunt.loadNpmTasks('grunt-aws-lambda');

var account_id = grunt.option('account_id');
var region = grunt.option('region') || 'us-east-1';

grunt.initConfig({
    lambda_invoke: {
        default: {
        }
    },
    lambda_deploy: {
        default: {
            arn: 'arn:aws:lambda:' + region + ':' + account_id + ':function:lookup-ami'
        }
    },
    lambda_package: {
        default: {
        }
    }
});

grunt.registerTask('deploy', ['lambda_package', 'lambda_deploy']);
