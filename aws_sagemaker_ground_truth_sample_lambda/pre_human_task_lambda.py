import json
import boto3
from urllib.parse import urlparse

def lambda_handler(event, context):
    """Sample PreHumanTaskLambda ( pre-processing lambda) for custom labeling jobs.

    For custom AWS SageMaker Ground Truth Labeling Jobs, you have to specify a PreHumanTaskLambda (pre-processing lambda).
    AWS SageMaker invokes this lambda for each item to be labeled. Output of this lambda, is merged with the specified
    custom UI template. This code assumes that specified custom template have only one placeholder "taskObject".
    If your UI template have more parameters, please modify output of this lambda.


    Parameters
    ----------
    event: dict, required
        Content of event looks some thing like following

        {
           "version":"2018-10-16",
           "labelingJobArn":"<your labeling job ARN>",
           "dataObject":{
              "source-ref":"s3://<your bucket>/<your keys>/awesome.jpg"
           }
        }

        As SageMaker product evolves, content of event object will change. For a latest version refer following URL

        Event doc: https://docs.aws.amazon.com/sagemaker/latest/dg/sms-custom-templates-step3.html

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    output: dict

        This output is an example JSON. We assume that your template have only one placeholder named "taskObject".
        If your template have more than one placeholder, make sure to add one more attribute under "taskInput"

        {
           "taskInput":{
              "taskObject":src_url_http
           },
           "isHumanAnnotationRequired":"true"
        }


        Note: Output of this lambda will be merged with the template, you specify in your labeling job.
        You can use preview button on SageMaker Ground Truth console to make sure merge is successful.

        Return doc: https://docs.aws.amazon.com/sagemaker/latest/dg/sms-custom-templates-step3.html
    """

    # Event received
    print("Received event: " + json.dumps(event, indent=2))

    # Get source if specified
    #source = event['dataObject']['source'] if "source" in event['dataObject'] else None
    source = event['dataObject']['video']

    # Get source-ref if specified
    #source_ref = event['dataObject']['source-ref'] if "source-ref" in event['dataObject'] else None

    # if source field present, take that otherwise take source-ref
    #task_object = source if source is not None else source_ref
    task_object = source

    # Build response object
    output = {
        "taskInput": {
            "taskObject": format_input(task_object)
        },
        "isHumanAnnotationRequired": "true"
    }

    print(output)
    # If neither source nor source-ref specified, mark the annotation failed
    if task_object is None:
        print(" Failed to pre-process {} !".format(event["labelingJobArn"]))
        output["isHumanAnnotationRequired"] = "false"

    return output


def format_input(task_object):
    new_obj = {}
    new_obj = { "title" : task_object["title"],
                "currentFrame" : task_object["currentFrame"]}
    
    new_frames = []
    for o in task_object['frames']:
        new_frames.append({"url": create_presigned_url(o["url"], expiration=864000), "seq_id": o["seq_id"]})
    
    new_obj["frames"] = new_frames
    
    return new_obj

def create_presigned_url(object_s3_uri, expiration):
    """Generate a presigned URL to share an S3 object

    :param object_s3_uri: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')
    object_url = urlparse(object_s3_uri)
    bucket_name = object_url.netloc
    object_name=object_url.path[1:]
    
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
                                                    
        print("S3 signed url :{}".format(response))                                            
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response