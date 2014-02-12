#!/usr/bin/env python

'''	CAP theorem: rethinkDb priorizes consistency before availability
	1. Read before any data modification
	2. Thread that updates a field for all registers in 'users' table
	3. Thread which tries to read some registers while updating thread is running
	4. Read after any data modification

	Result: while updating data is not available.
'''

import json
import rethinkdb as r
from threading import Thread
from time import sleep
from random import randint

def read(dbhostname, dbname, dbtable):
	'''	Reads a row from db
	'''
	try:
		rRd = r.connect(dbhosts[0], 28015, dbname)
		print "Begin thread read (while)..."
		doc = r.db(dbname).table(dbtable).get(randint(1,1000)).run(rRd)
		if (doc['address'] == updatedFieldBefore):
			print "OLD data:", doc['address']
		else:
			print "FRESH data:", doc['address']

		print "End thread read (while)..."
	except:
		print "Read thread error."
	finally:
		rRd.close()


def update(dbhostname, dbname, dbtable):
	''' Update all users table
	'''
	try:
		print "Thread update Start."
		rUp = r.connect(dbhostname, 28015, dbname)
		r.db(dbname).table(dbtable).update({'address':'80.80.80.80'}).run(rUp)
		print "Thread update finished."
	except:
		print "Update thread error."
	finally:
		rUp.close()


def reset(dbhostname, dbname, dbtable):
	''' Reset users table to init status
	'''
	rRst = r.connect(dbhostname, 28015, dbname)
	r.db(dbname).table(dbtable).update({'address':'80.80.80.1'}).run(rRst)
	rRst.close()


''' DB Setup
'''
dbhosts = ["192.168.11.69", "192.168.11.70"]
dbname = "profiling"
dbtable = "users"
updatedFieldBefore = "80.80.80.1"
updatedFieldAfter = "80.80.80.80"


''' Read
	Read BEFORE any data modification
'''
try:
	rRd = r.connect(dbhosts[1], 28015, dbname)
	print "Begin read before..."
	doc = r.db(dbname).table(dbtable).get(randint(1,1000)).run(rRd)
	if (doc['address'] == updatedFieldBefore):
		print "OLD data:", doc['address']
	else:
		print "FRESH data:", doc['address']

	print "End read before..."
except:
	print "Read error."
finally:
	rRd.close()


''' Update (launch thread)
'''
threadUpdate = Thread(target = update, name="cap-theorem-upd", args = [dbhosts[0], dbname, dbtable])
threadUpdate.start()

''' Read (launch thread)
'''
threadRead = Thread(target = read, name="cap-theorem-rd", args = [dbhosts[0], dbname, dbtable])
threadRead.start()

''' Finish threads
'''
threadUpdate.join(10)
threadRead.join(10)

''' 3rd Read
	Read AFTER data modification
'''
try:
	rRd = r.connect(dbhosts[1], 28015, dbname)
	print "Begin 3rd read (after)..."
	doc = r.db(dbname).table(dbtable).get(randint(1,1000)).run(rRd)
	if (doc['address'] == updatedFieldBefore):
		print "OLD data:", doc['address']
	else:
		print "FRESH data:", doc['address']

	print "End 3rd read (after)..."
except:
	print "Read error 3."
finally:
	rRd.close()


''' Reset environment (launch thread)
'''
threadReset = Thread(target = reset, name="cap-theorem-rst", args = [dbhosts[0], dbname, dbtable])
threadReset.start()
threadReset.join(10)
