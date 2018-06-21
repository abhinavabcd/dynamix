try:
    from gevent.queue import Queue, Empty
except:
    import Queue, Queue.Empty as Empty

import boto3
from config import aws_config, IS_LOCAL_ENDPOINT


conn_pools = {}
boto_session = boto3.session.Session(**aws_config)


def get_from_pool(pool_id='dynamodb'):
    conn = None

    conn_pool = conn_pools.get(pool_id, None)
    if (conn_pool == None):
        #if no conn_pool for given pool_id create and store in co]nn_pools
        conn_pool = Queue()
        conn_pools[pool_id] = conn_pool

    try:
        conn = conn_pool.get(block=False)
    # print "reusing from pool"
    except Empty:
        #if queue is empty create a connection for use.
        if(pool_id.startswith("dynamodb")):
            #table_name = pool_id.split("_")[1]
            #create new session
            if(IS_LOCAL_ENDPOINT[0]):                
                conn = boto3.resource('dynamodb', endpoint_url='http://{addr}:{port}'.format(addr=IS_LOCAL_ENDPOINT[0][0],port=IS_LOCAL_ENDPOINT[0][1]), aws_access_key_id=" ", aws_secret_access_key=" ", region_name="ap-south-1" )
            else:
                conn = boto_session.resource('dynamodb')

        elif(pool_id.startswith("s3")):
            conn = boto_session.resource('s3')
            # print "new connection"
        elif(pool_id.startswith("sqs")):
            conn = boto_session.client('sqs')
        
        elif(pool_id.startswith("ses")):
            conn = boto_session.client('ses', region_name="eu-west-1")
            
    return conn


def release_to_pool(conn, pool_id='es'):
    # print "releasing to pool"
    conn_pools[pool_id].put(conn)


def use_connection_pool(**pool_args):
    def use_db_connection(func):
        def func_wrap(*args, **kwargs):

            conn_args = {}
            for pool_arg, pool_id in pool_args.iteritems():
                conn = get_from_pool(pool_id)
                conn_args[pool_arg] = conn
            ret = None
            conn_args.update(kwargs)
            ret = func(*args, **conn_args)
            for pool_arg, pool_id in pool_args.iteritems():
                release_to_pool(conn_args[pool_arg], pool_id)
            return ret

            # TODO: try to remove connection timeout
            # retry = 0
            # while (retry < 2):
            #     conn_args = {}
            #     for pool_arg, pool_id in pool_args.iteritems():
            #         conn = get_from_pool(pool_id)
            #         conn_args[pool_arg] = conn
            #     ret = None
            #     try:
            #         conn_args.update(kwargs)
            #         ret = func(*args, **conn_args)
            #         for pool_arg, pool_id in pool_args.iteritems():
            #             release_to_pool(conn_args[pool_arg], pool_id)
            #         return ret
            #     except Exception, e:
            #         logger.error(message=e, event="message") # dont release that stupid connections to pool, instread write destroyers for each pool
            #         logger.error(message=traceback.format_exc(), event="message")
            #
            #         retry += 1
            #         if retry >= 2:
            #             raise e
        func_wrap._original = func
        return func_wrap

    return use_db_connection
