from dynamix.connection_pool import use_connection_pool
from dynamix.config import aws_config, IS_LOCAL_ENDPOINT 
from dynamix.table import Table
from botocore.exceptions import ClientError
import traceback



def set_connection(is_local_endpoint=None, **kwargs):
    if(is_local_endpoint):
        IS_LOCAL_ENDPOINT[0] = ("127.0.0.1", "8000") if is_local_endpoint == True else is_local_endpoint
    aws_config.update(kwargs)

@use_connection_pool(db="dynamodb")
def create_table(model_cls, db=None, force=False):
    
    table_obj = Table(model_cls(), db)
    if(force):
        try:
            table_obj.delete()
            table_obj.table.wait_until_not_exists()
        except Exception as ex:
            print("table doesnt exist ", table_obj.instance, ex)
        
    
    try:
        if(not force):
            try:
                table_obj.table.load()
                print("skipping %s table already exists"%(table_obj.table.name))
                return #continue if table already exists
            except ClientError as ce:
                pass

        table_obj.create()
        table_obj.table.wait_until_exists() #should wait until exisits
    except Exception as ex:
        print("could not create ", table_obj.instance,  ex)
        traceback.print_exc()
