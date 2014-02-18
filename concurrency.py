#!/usr/bin/env python

'''	Concurrency tests
	1. Read before any data modification
	2. Thread that updates a field for all registers in 'users' table
	3. Thread which tries to read some registers while updating thread is running
	4. Read after any data modification

	Result: while updating data is not available.
'''

import sys, getopt
import json
import rethinkdb as r
from threading import Thread
from time import sleep
from random import randint, shuffle

class Count():
	hits = 0
	errors = 0

class ReadCount(Count):
	fresh = 0
	pass

class UpdateCount(Count):
	pass


def read(dbhostname, dbname, dbtable, key = 'random'):
	'''	Reads a row from db
	'''
	updatedFieldBefore = "80.80.80.1"
	updatedFieldAfter = "80.80.80.80"

	try:
		rRd = r.connect(dbhostname, 28015, dbname)
		''' print "Begin thread read <key: {}>".format(key)
		'''
		if key is not None and key != 'random':
			doc = r.db(dbname).table(dbtable).get(key).run(rRd)
		else:
			doc = r.db(dbname).table(dbtable).get(randint(1,1000)).run(rRd)

		if assertEquals(doc['address'], updatedFieldAfter):
			''' print "FRESH data:", doc['address']
			'''
			ReadCount.fresh += 1

		ReadCount.hits += 1
		''' print "End thread read <key: {}>".format(key)
		'''
		rRd.close()
	except:
		''' print "Read thread error."
		'''
		ReadCount.errors += 1


def update(dbhostname, dbname, dbtable, key = 'random'):
	''' Update all users table
	'''
	try:
		''' print "Thread update Start < key: {} >".format(key)
		'''
		rUp = r.connect(dbhostname, 28015, dbname)
		if key is not None and key == 'all':
			r.db(dbname).table(dbtable).update({'address':'80.80.80.80'}).run(rUp)
		elif key is not None and isinstance(key, (int, long)):
			''' specific key '''
			r.db(dbname).table(dbtable).get(key).update({'address':'80.80.80.{}'.format(randint(1,255))}).run(rUp)
		else:
			''' random '''
			r.db(dbname).table(dbtable).get(randint(1,1000)).update({'address':'80.80.80.{}'.format(randint(1,255))}).run(rUp)

		UpdateCount.hits += 1
		''' print "Thread update finished."
		'''
		rUp.close()
	except:
		''' print "Update thread error."
		'''
		UpdateCount.errors += 1

def assertEquals(expected, obtained):
	return expected == obtained

def reset(dbhostname, dbname, dbtable):
	''' Reset users table to init status
	'''
	rRst = r.connect(dbhostname, 28015, dbname)
	r.db(dbname).table(dbtable).update({'address':'80.80.80.1'}).run(rRst)
	rRst.close()

def usage():
	print "Usage: concurrency.py -h -r NUMBER_OF_READS"
	print "Long options: --help --reads=NUMBER_OF_READS"

def getHost():
	dbhosts = [
		"192.168.56.101", "192.168.56.102", "192.168.56.103", "192.168.56.104",
		"192.168.56.105", "192.168.56.106", "192.168.56.107", "192.168.56.108",
		"192.168.56.109", "192.168.56.110", "192.168.56.111", "192.168.56.112",
		"192.168.56.113", "192.168.56.114", "192.168.56.115", "192.168.56.116",
		"192.168.56.117", "192.168.56.118", "192.168.56.119", "192.168.56.120"
	]
	return dbhosts[randint(0,19)]

def getDbConfig():
	''' Returns a list with database configuration, including a random node
	'''
	dbname = "profiling"
	dbtable = "users"
	return [getHost(), dbname, dbtable]

def test(test, threadList, counter, key = None):
	''' Function to test sequential/random reads and writes
	'''
	if test in ('read', 'update'):
		for i in range(0, counter):
			threadList.append(Thread(target = globals()[test], name="test-{}-{}".format(test, i), args = getDbConfig() + [key]))
	else:
		usage


def main(argv):
	try:
		opts, args = getopt.getopt(argv, "hr:u:k:", ["help", "reads=", "updates=", "key="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)


	actions = {'key':None}
	threadList = []

	''' Parse script arguments
	'''
	for opt, arg in opts:
		if opt in ('-h', "--help"):
			usage()
			sys.exit(1)
		elif opt in ('-u', '--updates'):
			actions['updates'] = int(arg)
		elif opt in ('-r', '--reads'):
			actions['reads'] = int(arg)
		elif opt in ('-k', '--key'):
			actions['key'] = arg

	if 'updates' in actions:
		''' Update (launch thread)
		'''
		test('update', threadList, actions['updates'], actions['key'])

	if 'reads' in actions:
		''' Read (launch thread)
		'''
		test('read', threadList, actions['reads'], actions['key'])


	''' Start running threads
	'''
	shuffle(threadList)
	for th in threadList:
		th.start()	

	''' Reset environment (launch thread)
	'''
	threadList.append(Thread(target = reset, name="concurrency-rst", args = getDbConfig()))
	threadList[len(threadList)-1].start()


	''' Finish threads (wait until finished)
	'''
	for th in threadList:
		threadList.pop(0).join(120)

	sleep(5)
	
	print "Reads:			{} hits ({} fresh);	{} errors".format(ReadCount.hits, ReadCount.fresh, ReadCount.errors)
	print "Updates:		{} hits;	{} errors".format(UpdateCount.hits, UpdateCount.errors) 

if __name__ == "__main__":
	main(sys.argv[1:])
