#!/usr/bin/env python

'''	Concurrency tests
	1. Read before any data modification
	2. Thread that updates a field for all registers in 'users' table
	3. Thread which tries to read some registers while updating thread is running
	4. Read after any data modification

	Result: while updating data is not available.
'''

import sys, getopt
import subprocess
import json
from threading import Thread
from time import sleep
from random import randint, shuffle, random
import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

class Count():
	''' Counter for events
	'''
	def __init__(self):
		self.hits = 0
		self.errors = 0
		self.other = 0
		self.notFound = []

class ReadCount(Count):
	fresh = 0
	pass


class UpdateCount(Count):
	pass



class Concurrency:
	''' Class that launches multiple threaded reads and updates in a rethinkDb cluster
	'''

	def __init__(self):
		self.readCount = ReadCount()
		self.updateCount = UpdateCount()
		self.threadList = []
		self.actions = {'key':None, 'outdated':None}


	def usage(self):
		print "Usage: concurrency.py -h [-r #READS] [-u #UPDATES] [-k all|1..20] [-d 1] [-x 1] [-o]"
		print "Long options: --help --reads=#READS --updates=#UPDATES --key=all|1..20 --readdown 1 --updatedown 1 [--outdated]"


	def getHost(self, index = None):
		''' Get a random/specific node ip address
		'''
		dbhosts = [
			"192.168.56.101", "192.168.56.102", "192.168.56.103", "192.168.56.104",
			"192.168.56.105", "192.168.56.106", "192.168.56.107", "192.168.56.108",
			"192.168.56.109", "192.168.56.110", "192.168.56.111", "192.168.56.112",
			"192.168.56.113", "192.168.56.114", "192.168.56.115", "192.168.56.116",
			"192.168.56.117", "192.168.56.118", "192.168.56.119", "192.168.56.120"
		]

		if index is None:
			index = randint(0,19)

		return dbhosts[index]


	def getDbConfig(self):
		''' Returns a list with database configuration, including a random node
		'''
		dbname = "profiling"
		dbtable = "users"
		return [self.getHost(), dbname, dbtable]


	def assertEquals(self, expected, obtained):
		return expected == obtained


	def reset(self, dbhostname, dbname, dbtable):
		''' Reset users table to init status
		'''
		rRst = r.connect(dbhostname, 28015, dbname)
		r.db(dbname).table(dbtable).update({'address':'80.80.80.1'}).run(rRst)
		rRst.close()


	def read(self, dbhostname, dbname, dbtable, key = 'random', outOfDate = False):
		'''	Reads users table
		'''
		updatedFieldBefore = "80.80.80.1"
		updatedFieldAfter = "80.80.80.80"

		try:
			rRd = r.connect(dbhostname, 28015, dbname)
			if key is not None and key != 'random':
				doc = r.db(dbname).table(dbtable).get(int(key)).run(rRd, use_outdated = outOfDate)
			else:
				key = randint(1,1000)
				doc = r.db(dbname).table(dbtable).get(key).run(rRd, use_outdated = outOfDate)

			'''
			if self.assertEquals(doc['address'], updatedFieldAfter):
				self.readCount.fresh += 1
			'''
			if doc is not None:
				self.readCount.hits += 1
			else:
				self.readCount.notFound.append(key)

			rRd.close()
			return doc
		except RqlDriverError as e:
			print e
			self.readCount.errors += 1
		except RqlRuntimeError as e:
			print e
			self.readCount.errors += 1
		except:
			self.readCount.other += 1


	def update(self, dbhostname, dbname, dbtable, key = 'random', outOfDate = False):
		''' Update users table
		'''
		try:
			rUp = r.connect(dbhostname, 28015, dbname)
			if key is not None and key == 'all':
				doc = r.db(dbname).table(dbtable).update({'address':'80.80.80.80'}).run(rUp, use_outdated = outOfDate)
			elif key is not None and isinstance(key, (int, long)):
				''' specific key '''
				doc = r.db(dbname).table(dbtable).get(key).update({'address':'80.80.80.{}'.format(randint(1,255))}).run(rUp, use_outdated = outOfDate)
			else:
				''' random '''
				doc = r.db(dbname).table(dbtable).get(randint(1,1000)).update({'address':'80.80.80.{}'.format(randint(1,255))}).run(rUp, use_outdated = outOfDate)

			if doc is not None:
				self.updateCount.hits += 1
			else:
				self.updateCount.notFound.append(key)

			rUp.close()
			return doc
		except RqlDriverError, RqlRuntimeError:
			self.updateCount.errors += 1
		except:
			self.updateCount.other += 1


	def actionDownNode(self, action, outOfDate = False):
		''' Shutdown rethinkDb node and tries to read/update a key from it
			Node:	2
			Key:	999

			Note: I know node 2 is master for the key 999
		'''
		conf = self.getDbConfig()
		self.power('off', 2)
		if action == 'updateDownNode':
			print self.update(conf[0], conf[1], conf[2], 999, outOfDate)
		else:
			print self.read(conf[0], conf[1], conf[2], 999, outOfDate)
		self.power('on', 2)


	def power(self, action, node):
		''' Start/Stop rethinkdb
		'''
		if action == 'on':
			command = "ssh -n {} nohup /home/rsicart/launch_rethink_cluster.sh -t node -a {} &".format(self.getHost(node), self.getHost(0))
		else:
			command = "ssh -n {} /home/rsicart/launch_rethink_cluster.sh -k stop".format(self.getHost(node))
		process = subprocess.Popen(command.split(), stdout = subprocess.PIPE)
		output = process.communicate()[0]
		sleep(5)


	def test(self, test, counter, key = None, outOfDate = False):
		''' Function to test sequential/random reads and writes
		'''
		if test in ('read', 'update'):
			for i in range(0, counter):
				self.threadList.append(Thread(target = getattr(self, test), name="test-{}-{}".format(test, i), args = self.getDbConfig() + [key] + [outOfDate]))
		elif test in ('readDownNode, updateDownNode'):
			self.threadList.append(Thread(target = self.actionDownNode, name="test-{}-{}".format(test, 1), args = [test, outOfDate]))
		else:
			usage


	def stopThreads(self):
		''' Finish threads (wait until finished)
		'''
		for th in self.threadList:
			self.threadList.pop(0).join(120)


	def stats(self):
		print "Reads:			{} hits ({} fresh);	{} errors;	{} other".format(self.readCount.hits, self.readCount.fresh, self.readCount.errors, self.readCount.other)
		if len(self.readCount.notFound) > 0:
			print "Reads not found: {}".format(set(self.readCount.notFound))
		print "Updates:		{} hits;	{} errors;	{} other".format(self.updateCount.hits, self.updateCount.errors, self.updateCount.other) 
		if len(self.updateCount.notFound) > 0:
			print "Updates not found: {}".format(set(self.updateCount.notFound))



def main(argv):
	try:
		opts, args = getopt.getopt(argv, "hr:u:k:d:x:o", ["help", "reads=", "updates=", "key=", "readdown=", "updatedown=", "outdated"])
	except getopt.GetoptError:
		c.usage()
		sys.exit(2)

	c = Concurrency()

	''' Parse script arguments
	'''
	for opt, arg in opts:
		if opt in ('-h', "--help"):
			c.usage()
			sys.exit(1)
		elif opt in ('-u', '--updates'):
			c.actions['updates'] = int(arg)
		elif opt in ('-r', '--reads'):
			c.actions['reads'] = int(arg)
		elif opt in ('-k', '--key'):
			c.actions['key'] = arg
		elif opt in ('-d', '--readdown'):
			c.actions['readdown'] = int(arg)
		elif opt in ('-x', '--updatedown'):
			c.actions['updatedown'] = int(arg)
		elif opt in ('-o', '--outdated'):
			c.actions['outdated'] = True

	if 'updates' in c.actions:
		''' Update (launch thread)
		'''
		c.test('update', c.actions['updates'], c.actions['key'], c.actions['outdated'])

	if 'reads' in c.actions:
		''' Read (launch thread)
		'''
		c.test('read', c.actions['reads'], c.actions['key'], c.actions['outdated'])

	if 'readdown' in c.actions:
		''' Read dead node
		'''
		c.test('readDownNode', c.actions['readdown'], c.actions['key'], c.actions['outdated'])

	if 'updatedown' in c.actions:
		''' Update dead node
		'''
		c.test('updateDownNode', c.actions['updatedown'], c.actions['key'], c.actions['outdated'])


	''' Start running threads
	'''
	count = 0
	maxThreads = 30
	shuffle(c.threadList)
	for th in c.threadList:
		'''
		if randint(0,1) > 0:
			sleep(0.2)
		'''
		if count == maxThreads:
			count = 0
			sleep(1)

		th.start()	
		count += 1

	''' Reset environment (launch thread)
	'''
	if 'updates' in c.actions or 'updatedown' in c.actions:
		c.threadList.append(Thread(target = c.reset, name="concurrency-rst", args = c.getDbConfig()))
		c.threadList[len(c.threadList)-1].start()


	''' Finish threads
	'''
	c.stopThreads()

	sleep(5)

	c.stats()

if __name__ == "__main__":
	main(sys.argv[1:])
