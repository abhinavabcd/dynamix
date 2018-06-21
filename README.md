[![Coverage Status](https://coveralls.io/repos/github/abhinavabcd/dynamix/badge.svg?branch=master)](https://coveralls.io/github/abhinavabcd/dynamix?branch=master)

# Dynamix
Another Python DynamoDb ORM, syntax and patterns stolen from a mix of other ORMs. This was developed as part of an app migration strategy from Google App engine to AWS.



# Connecting 
	dynamix.set_connection(is_local_endpoint=True or ("127.0.0.1", "8000") , aws_access_key_id = "*", aws_secret_access_key = "*", region_name = "ap-south-1")

# Example full featured model

	class ForumThread(Model):
	
	    __table_name__ = 'forum_thread'
	
	    ReadCapacityUnits = 2
	    WriteCapacityUnits = 2
	
	    __secondary_indexes__ = {
	                             "user_threads_index": dict(hash_key="user_id", range_key="updated_at", read_capacity=2, write_capacity=2, projections=["title"]), #secondary index with additional projections
	                            }
	    
	    forum_id = CharField(name='forum_id', hash_key=True) # hash key        
	    thread_id = CharField(name='thread_id', range_key=True) # range key
	    user_id = CharField(name="user_id")
	    title = CharField(name="title")
	    description = CharField(name="description")
	    updated_at = IntegerField(name='updated_at', default=lambda : int(time.time()*1000), indexed=True) # local index
	    expiry_timestamp = IntegerField(name='expiry_timestamp', indexed=True, projections=["updated_at"]) # local index with selected attributes projected to index
	    tags = SetField(name="tags")
	    user_reviews = ListField(name="user_reviews", default=[])
	    key_value_data = DictField(name="key_value_data")



# Creating a table
	dynamix.create_table(ForumThread, force=True)


# CharField, ListField, DictField, SetField, IntegerField


# Create new entry
	forum_thread = ForumThread.create(forum_id="science", thread_id="physics_1", title="gravitational field of a blackhole", description="equations and more", tags=set(["physics", "gravity"]) , user_id="me", key_value_data={"a": 1, "b" : 2})
## don't overwrite with overwrite=False
	forum_thread = ForumThread.create(forum_id="science", thread_id="physics_1", title="gravitational field of a blackhole", description="equations and more", tags=set(["physics", "gravity"]) , user_id="me", key_value_data={"a": 1, "b" : 2} , overwrite=False)




# Querying
## By primay key
	forum_thread =  ForumThread.get(forum_id="science", thread_id="physics_1")

## By using a query
	threads, cursor =   ForumThread.query().where(ForumThread.forum_id.eq("science"), ForumThread.thread_id.begins_with("physics_")).get_items()

Can use .begins_with, .gte, .eq, .lt, .lte, .ne, .gt

get_items always returns a tuple of items and cursor that is used for paginating

## Get next page using cursor : start_key()
	threads, cursor =   ForumThread.query().start_key(cursor).where(ForumThread.forum_id.eq("science"), ForumThread.thread_id.begins_with("physics_")).get_items()


## Query on a local Index : use_index(index_name/field, asc=True/False)

	threads, cursor =   ForumThread.query().start_key(cursor).use_index(ForumThread.updated_at , asc=True).where(ForumThread.forum_id.eq("science"), ForumThread.updated_at.lte(int(time.time()*1000))).get_items(requery_for_all_projections=True)

*requery_for_all_projections=True* requeries for dynamoDb to fetch all projections. If not given, will return primary key( hash_key, range_key) and projections specifically mentioned in index


## Query on a Secondary Index using index name

	user_recent_threads, cursor =   ForumThread.query().start_key(cursor).use_index("user_threads_index" , asc=True).where(ForumThread.user_id.eq("some_new_user_id"), ForumThread.updated_at.lte(int(time.time()*1000)).get_items()


#Batch get , delete, write

	forum_threads = ForumThread.batch_get(*[{"forum_id": "science" , "thread_id": "physics_"+num} for num in range(100)])

	ForumThread.batch_delete(keys = [{"forum_id": "science" , "thread_id": "physics_"+num} for num in range(100)]) # can also pass items directly

## write multiple items / python objects in one go
	ForumThread.batch_write([{"forum_id": "science" , "thread_id": "physics_"+str(num), "title": "Physics", "description" : "some description ...."} for num in range(100)])



# Updating and commit_changes()

## set a field value
	forum_thread.set_field(ForumThread.updated_at, int(time.time()*1000))

## add a value to a field 
	forum_thread.add_to_field(ForumThread.updated_at, 1000) # will add thousand to the current value atomically

## Dict Field
	forum_thread.update_to_dict_field(ForumThread.key_value_data, {"c": 100, "b" : 5}) #updates new and replaces existing keys
	forum_thread.remove_from_dict_field(ForumThread.key_value_data, ["a","b"])

## List Field
	forum_thread.append_to_listfield(ForumThread.user_reviews, "100")
	forum_thread.append_to_listfield(ForumThread.user_reviews, ["100","101"]) 

	forum_thread.replace_by_index_in_listfield(ForumThread.user_reviews, 1, "1000") # index , value
	forum_thread.remove_by_index_from_listfield(ForumThread.user_reviews, 1)) #removes first index
 
## Set Field    
	forum_thread.add_to_setfield(ForumThread.tags, set(["black_hole", "white_hole"])) 
	forum_thread.delete_from_setfield(ForumThread.tags, set(["black_hole"])) 

## Finally commit all pending updates at once
	forum_thread.commit_changes()



# Set modify conditions 
Conditions on other fields when updating

	forum_thread.set_modify_conditions(ForumThread.updated.ne(int(time.time()*1000))) # can use query conditions , begins_with, gte, lte like mentioned above


# .to_son()
Will return the python object that can be serialized with json.dumps()

# Scan all data 
	Model.scan()

# is still under active development


