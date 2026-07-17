import os
import logging
import json
import azure.functions as func
from azure.data.tables import TableServiceClient
from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

#For Azure Table
storage_key=os.environ.get('AzureWebJobsStorage')
#For ACS
credential = AzureKeyCredential(os.environ["ACS_EMAIL_KEY"])
endpoint=os.environ["ACS_ENDPOINT"]
client = EmailClient(endpoint,credential)

@app.route(route="http_get",methods=["GET"])
def http_get(req: func.HttpRequest) -> func.HttpResponse:
    table_service = TableServiceClient.from_connection_string(conn_str=storage_key)
    table_client = table_service.get_table_client("MasterTable")

    routelist=[]

    entities=table_client.list_entities()
    for entity in entities:
        routelist.append({"DEP":entity["DEP"],
                    "ARR":entity["ARR"],
                    "FREQ":entity["FREQ"],
                    "DATE":entity["DATE"]})

    return func.HttpResponse(json.dumps(routelist), status_code=200)


@app.route(route="http_post", methods=['POST'])
def http_post(req: func.HttpRequest) -> func.HttpResponse:
    code = req.params.get('code')
    
    e_code=os.environ.get('ACCESS_CODE')

    if code==e_code:
        table_service = TableServiceClient.from_connection_string(conn_str=storage_key)
        table_client = table_service.get_table_client("MasterTable")

        data = req.get_json()

        rk=data["DEP"].upper()+data["ARR"].upper()+data["DATE"]
        new_entity={"PartitionKey":"Route",
                    "RowKey":rk,
                    "DEP":data["DEP"],
                    "ARR":data["ARR"],
                    "FREQ":data["FREQ"],
                    "DATE":data["DATE"]}
        
        table_client.create_entity(new_entity)

        dep=data["DEP"]
        arr=data["ARR"]
        freq=data["FREQ"]
        date=data["DATE"]

        message = {
            "senderAddress": "DoNotReply@b69c3249-d05b-47d9-a9a3-9fc4b60755d6.azurecomm.net",
            "recipients": {
                "to": [{"address": "autoalpha72110@gmail.com"}]
            },
            "content": {
                "subject": f'New Prompt Added',
                "plainText": f'A new prompt has been added on the app, for:\n\nRoute: {dep}-{arr}\nFrequency (as on date of addition): {freq}\nDate: {date}',
            },
            
        }
        poller = client.begin_send(message)

        return func.HttpResponse("New Prompt Added Successfully",status_code=201)
    else:
        return func.HttpResponse("Access denied", status_code=403)
    
@app.route(route="http_del",methods=["DELETE"])
def http_del(req: func.HttpRequest) -> func.HttpResponse:
    code = req.params.get('code')
    
    e_code=os.environ.get('ACCESS_CODE')

    if code==e_code:
        table_service = TableServiceClient.from_connection_string(conn_str=storage_key)
        table_client = table_service.get_table_client("MasterTable")

        partition_key = req.params.get("PartitionKey")
        row_key = req.params.get("RowKey")

        data=table_client.get_entity(partition_key=partition_key,row_key=row_key)
        dep=data["DEP"]
        arr=data["ARR"]
        freq=data["FREQ"]
        date=data["DATE"]

        message = {
            "senderAddress": "DoNotReply@b69c3249-d05b-47d9-a9a3-9fc4b60755d6.azurecomm.net",
            "recipients": {
                "to": [{"address": "autoalpha72110@gmail.com"}]
            },
            "content": {
                "subject": f'Prompt Deleted',
                "plainText": f'A prompt has been deleted from the app, for:\n\nRoute: {dep}-{arr}\nFrequency (as on date of deletion): {freq}\nDate: {date}',
            },
            
        }
        poller = client.begin_send(message)

        table_client.delete_entity(partition_key=partition_key, row_key=row_key)


        return func.HttpResponse("Sucessfully Deleted",status_code=200)
    else:
        return func.HttpResponse("Access Denied",status_code=403)
