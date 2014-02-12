#!/usr/bin/env python
import json
import rethinkdb as r
from subprocess import call

# Setup
createUsersScript = "./create_sample_users.sh"
userFileName = "data.users.json"
dbname = "profiling"
dbhost = "192.168.11.69"
dbtable = "users"

call([createUsersScript])

# Read JSON file data
userData = open(userFileName, "r")
jsonData = userData.read()

# Insert data to DB
r.connect(dbhost, 28015).repl()
r.db(dbname).table(dbtable).insert(json.loads(jsonData)).run()

userData.close()
