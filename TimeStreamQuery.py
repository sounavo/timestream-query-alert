#
# TimestreamQuery
#

import base64
import boto3
import botocore
import json
import logging
import os
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DATABASE_SENSORDATA = os.environ.get("DATABASE_SENSORDATA", "")
TABLE_SENSORDATA = os.environ.get("TABLE_SENSORDATA", "").split('|')[-1]

logger.info("DATABASE_SENSORDATA: {} TABLE_SENSORDATA: {} ".format(DATABASE_SENSORDATA, TABLE_SENSORDATA))

QUERY =  '   (  '  \
 '   SELECT measure_name, avg(measure_value::double) as average_humidity FROM ' + DATABASE_SENSORDATA + '.' + TABLE_SENSORDATA+ ' '\
 '   WHERE (time between ago(200m) and now())   '\
 '   GROUP BY measure_name  '\
 '   having measure_name=\'humidity\'  '\
 '   and avg(measure_value::double) >900        )'\
 '   UNION  '\
 '          (  '\
 '   SELECT measure_name, avg(measure_value::double) as average_temparature FROM ' + DATABASE_SENSORDATA + '.' + TABLE_SENSORDATA+ ' '\
 '   WHERE (time between ago(200m) and now())  '\
 '   GROUP BY measure_name  '\
 '   having measure_name=\'temperature\'       '\
 '   and avg(measure_value::double) > 20  '\
 '          )  '\
 '   UNION  '\
 '          (  '\
 '   SELECT measure_name, avg(measure_value::double) as average_temparature FROM ' + DATABASE_SENSORDATA + '.' + TABLE_SENSORDATA+ ' '\
 '   WHERE (time between ago(200m) and now())   '\
 '   GROUP BY measure_name  '\
 '   having measure_name=\'pressure\'      '\
 '   and avg(measure_value::double) > 20  '\
 '         )    '
def lambda_handler(event, context):
    logger.debug("event:\n{}".format(json.dumps(event, indent=2)))

    records_sensordata = []
    records_ggmetrics = []

    try:
        c_ts_query = boto3.client('timestream-query')
        sns = boto3.client('sns')

        response = c_ts_query.describe_endpoints()
        logger.info("response describe_endpoints: {}".format(response))
        if not DATABASE_SENSORDATA or not TABLE_SENSORDATA:
            logger.warn("database or table for sensordata not defined: DATABASE_SENSORDATA: {} TABLE_SENSORDATA: {}".format(DATABASE_SENSORDATA, TABLE_SENSORDATA))
            return {"status": "warn", "message": "database or table for sensordata not defined"}
        response = c_ts_query.query(QueryString=QUERY)
        print("response::")
        print(format(response))
        ret_val = {"status": "success"}
        #ret_val["records sensordata processed"] = "{}" .format(response)
        ret_val["records size"] = "{}" .format(len(response['Rows']))
        result = int(ret_val["records size"]);
        print("============================")
        
        record_size = format(len(response['Rows']))
        if result < 1:
            return result

        if result>0 and 'humidity' in response['Rows'][0]['Data'][0]['ScalarValue']:
            print('humity theshold exceeded with value ',response['Rows'][0]['Data'][1]['ScalarValue'])
            sns.publish(TopicArn='arn:aws:sns:eu-west-1:751195137645:Alarm-threshold-trigger', Message="Average Humidity theshold exceeded. Current value:"+response['Rows'][0]['Data'][1]['ScalarValue'], Subject="Alert")
        
        if result>1 and 'temperature' in response['Rows'][1]['Data'][0]['ScalarValue']:
            print('temperature theshold exceeded with value ',response['Rows'][1]['Data'][1]['ScalarValue'])
            sns.publish(TopicArn='arn:aws:sns:eu-west-1:751195137645:Alarm-threshold-trigger', Message="Average Temparature theshold exceeded. Current value:"+response['Rows'][1]['Data'][1]['ScalarValue'], Subject="Alert")
        
        if result>2 and 'pressure' in response['Rows'][2]['Data'][0]['ScalarValue']:
            print('pressure theshold exceeded with value ',response['Rows'][2]['Data'][1]['ScalarValue'])
            sns.publish(TopicArn='arn:aws:sns:eu-west-1:751195137645:Alarm-threshold-trigger', Message="Average Temparature theshold exceeded. Current value:"+response['Rows'][2]['Data'][1]['ScalarValue'], Subject="Alert")

            
    #   some data needs to be returned 
        return ret_val 

    except Exception as e:
        logger.error("{}".format(e))
        return {"status": "error", "message": "{}".format(e)}
        
     

def next_key(dict, key):
    keys = iter(dict)
    key in keys
    return next(keys, False)