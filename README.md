STEPS TO SET UP AWS AND CONNECT TO RASPBERRY PI

1.SETTING UP AWS IoT MQTT CLIENT 
•	After saving the python code in the raspberry pi, create an AWS account and sign in to the console.
•	Now search for IoT core and create a thing
•	Download the credentials and save it in the same folder where your python code is saved.
•	Now,
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

  # Define your custom Client ID
      myClientId = "give a unique client name here"

 # Initialize the client
      myMQTTClient = AWSIoTMQTTClient(myClientId)

run this python script,before running this install the AWS SDK using

                     "pip install AWSIoTPythonSDK" 
                     
•	Now fill the Client id you have created and the root path of the necessary credentials.
•	Copy the AWS endpoint URL from the settings page in AWS IoT Core and paste it in the python code.
•	Finally, in the MQTT test client of the AWS IoT subscribe to “topic/flood_alert”.
•	Now the device is connected to AWS and the data are published to the AWS IoT Client by the raspberry pi.

2.SETTING UP AWS LAMBDA AND DYNAMODB
•	Navigate to Lambda service and create a new and set the run time environment as python.
•	Create an IAM role that allows permission to access DynamoDB and add the role to the lambda function.
•	Now program the lambda function that updates the respective DynamoDB table that you have created.
•	Create a DynamoDB table by giving partition key as sensor_ID, short key as timestamp and additional partition key as location.
•	Now the data will be stored in the DynamoDB from the MQTT client.






