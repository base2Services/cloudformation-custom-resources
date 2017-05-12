"use strict";

const AWS = require('aws-sdk');

const ec2 = new AWS.EC2({
    apiVersion: '2016-11-15'
});


class EniCleanupLogic {

    //store handler and bucket name locally
    constructor(subnetIds, handler) {
        this.subnetIds = subnetIds;
        this.successHandler = (data) => { handler(null, data) };
        this.errorHandler = (err) => { handler(err, null); }
        this.enis = {};
    }

    //delete eni handler
    deleteEniHandler(eniid) {
        let self = this;
        return (err, data) => {
            if (err) {
                console.error(err);
                self.errorHandler(err);
                return;
            }

            delete self.enis[eniid];
            console.log(`Deleted ${eniid}`);
            if (Object.keys(self.enis) == 0) {
                self.successHandler();
            }
        }
    }

    //list enis handler
    deleteEnis() {
        var self = this;
        return (err, data) => {
            if (err) {
                console.error(err);
                self.errorHandler(err);
                return;
            }

            //no ENIs to delete
            if (data.NetworkInterfaces.length == 0) {
                self.successHandler();
                return;
            }

            //delete each ENI
            data.NetworkInterfaces.forEach((iface) => {
                self.enis[iface.NetworkInterfaceId] = true;
                console.log(`Starting deletion of ${iface.NetworkInterfaceId}`);
                ec2.deleteNetworkInterface({ NetworkInterfaceId: iface.NetworkInterfaceId },
                    self.deleteEniHandler(iface.NetworkInterfaceId)
                );
            });
        }
    }

    //list enis
    listEnis() {
        let self = this;
        console.log(`Retrieving ENIs in subnets ${self.subnetIds}`);
        ec2.describeNetworkInterfaces({
            Filters: [{ Name: 'subnet-id', Values: self.subnetIds }]
        }, self.deleteEnis());
    }

    cleanupEnis() {
        this.listEnis();
    }
}


module.exports = EniCleanupLogic;