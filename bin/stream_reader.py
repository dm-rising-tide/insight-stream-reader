#coding: utf-8

import sys
import logging
import os
import traceback
#from kafka_helper import KafkaHelper
import json
import pymongo
import logging.config
from data_transmitter import DataTransmitter

class InsightReader(object):
	def __init__(self, insight_conf):
		self.logger = logging.getLogger('tide')
		self.insight_conf = insight_conf
	def run(self):
		self.logger.info("Service is running")

		try:
			conn = pymongo.Connection('10.0.0.206',27777)

			db = conn.insight_database

			request_log = db.request_log
			self.logger.info("Connect MongoDB successfully.")
		except Exception, why:
			self.logger.fatal("Connect MongoDB occurred error: {}\n{}".format(why, traceback.format_exc()))

		
		dt = DataTransmitter(self.insight_conf, self.logger)
		while True:
			try:
				message = sys.stdin.readline()
				if not message:
					self.logger.info(">>>>STOP ON EOF <<<<")
					break

				#print message
				self.logger.info(message)

				request_info = json.loads(message)

				request_log.insert(request_info)

				self.logger.info('Insert a request into MongoDB successfully!')
				
				
				
				
				dt.save_to_mongo(message)

			except Exception, why:
				self.logger.fatal("Reader occurred error: {} \n{}".format(why,traceback.format_exc()))
				



