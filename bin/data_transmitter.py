#coding: utf-8
#Author: 		Fan Jianing
#Create Date: 	2016/12/08
#Description:

import json
import pymongo
import datetime
import logging
import traceback

class DataTransmitter(object):
	def __init__(self, conf,log ):
		self.log = log
		self.conf = conf

	def construct_page_element(self, page_request):
		ele = {}
		ele["id"] = page_request["id"] if "id" in page_request else None
		ele["eleType"] = page_request["eleType"] if "eleType" in page_request else None
		ele["name"] = page_request["name"] if "name" in page_request else None
		ele["className"] = page_request["className"] if "className" in page_request else None
		ele["btnText"] = page_request["btnText"] if "btnText" in page_request else None
		ele["type"] = page_request["type"] if "type" in page_request else None
		ele["elementId"]="{id}-{name}-{type}-{className}-{btnText}-{eleType}".format(id = ele["id"], name = ele["name"], className = ele["className"], btnText = ele["btnText"], eleType = ele["eleType"], type = ele["type"])
		return ele

	def construct_page_info(self, page_request):
		page_info = {}
		page_info["pageTitle"] = page_request["pageTitle"] if "pageTitle" in page_request else None
		page_info["url"] = page_request["url"] if "url" in page_request else None
		page_info["pageElements"] = []
		ele = self.construct_page_element(page_request)
		page_info["pageElements"].append(ele)

		return page_info

	def construct_visit_info(self, page_request, page_id):
		visit_info = {}
		visit_info["pageId"] = page_id
		visit_info["id"] = page_request["tidePvId"] if "tidePvId" in page_request else None
		visit_info["uid"] = page_request["tideUvId"] if "tideUvId" in page_request else None
		visit_info["system"] = page_request["system"] if "system" in page_request else None
		visit_info["browser"] = page_request["browser"] if "browser" in page_request else None
		visit_info["ua"] = page_request["ua"] if "ua" in page_request else None
		visit_info["firstAccessTime"] = page_request["date"] if "date" in page_request else None
		visit_info["lastAccessTime"] = page_request["date"] if "date" in page_request else None
		visit_info["referrer"] = page_request["referrer"] if "referrer" in page_request else None
		visit_info["operationOrder"]=[]
		visit_info["operationInfo"]={}
		visit_info["elementInfo"]={}
		return visit_info

	def check_element_indentity(self, element, page_element):
		if element["elementId"] == page_element["elementId"]:
			return True
		else:
			return False



	def save_to_mongo(self, request):
		try:
			connection = pymongo.Connection(self.conf.get("mongo","host"), int(self.conf.get("mongo","port")))
			
			self.log.info('Connect Mongo DB Successfully.')

			db = connection.insight_database

			#page_request = {"url":"http://123.58.165.121/domob.php/xxx", "page_elements":[{"id":"addApp","type":"btn","className":"span4","btn_text":"提交"}]}

			page_request = json.loads(request)
			if "webStatus" in page_request or page_request["type"] == 'a':
				self.log.debug("这是一个页面状态 或是一个a标签，过滤")
				return

			else:
				self.log.debug("{}".format(page_request))
			if self.conf.get("system","mode") == "debug":
				page_info = db.test_page_info
				visit_info = db.test_visit_info
				self.log.debug("System is DEBUG mode.")
			else:
				page_info = db.page_info
				visit_info = db.visit_info
				self.log.debug("System is NORMAL mode.")

			is_insert_new_ele = False
			#构建页面信息
			exist_page_info = page_info.find_one({"url":page_request["url"]})

			if exist_page_info is None:
				#页面请求不存在，新建页面信息
				page_info_dict = self.construct_page_info(page_request)
				page_info.insert(page_info_dict)
				self.log.debug("{}".format(page_info))
				page_info_res = page_info.find_one({"url":page_request["url"]})
				page_id = page_info_res["_id"]
				self.log.debug("页面请求不存在，新建页面信息:[{}]".format(page_request["url"]))
			else:
				self.log.debug("页面请求已经存在:[{}]".format(page_request["url"]))
				page_id = exist_page_info["_id"]
				#用每一个请求构建一个 页面信息
				
				ele = self.construct_page_element(page_request)
				if ele["elementId"] == "None-None-None-None-None-None":
					self.log.debug("Element Id全为空，无效")
					return 

				if "pageElements" not in exist_page_info:
					#不存在页信息
					page_elements = []
					page_elements.append(ele)
					is_insert_new_ele = True
					self.log.debug('不存在页面信息，添加页面信息')
				else:
					#存在页面信息
					page_elements = exist_page_info["pageElements"]
					flag = True
					
					for element in page_elements:
						if self.check_element_indentity(ele, element) == True:
							flag = False
							break


					if flag == True:#没有这个页面的组件

						page_elements.append(ele)
						self.log.debug("添加页面组件：id = [{}]".format(ele["id"]))
						is_insert_new_ele = True
				
				page_info.update({"_id":page_id},{"$set":{"pageElements":page_elements}})

				page_info_res = page_info.find_one({"_id":page_id})
				self.log.debug("更新页面组件信息成功, page_id = [{}]".format(page_id))
			#构建请求信息

			visit_info_res = visit_info.find_one({"id":page_request["tidePvId"]})
			visit_info_dict = {}
			operationOrder = []
			if visit_info_res is None:
				#从来没见过的访问请求
				self.log.debug("从来没见过的访问请求.pvId=[{}]".format(page_request["tidePvId"]))
				visit_info_dict = self.construct_visit_info(page_request, page_id)
				#operation = {}
				ele = self.construct_page_element(page_request)
				for i, page_ele in enumerate(page_info_res["pageElements"]): #把当前访问的次序搞定
					if self.check_element_indentity(ele, page_ele) == True:
							visit_info_dict["elementInfo"][str(i)] = {"times": 1 }
							operation = {	str(i) : 
											{	
												"triggerTime":page_request["date"]
											}
										}
							break
				operationOrder.append(operation)
				visit_info_dict["operationOrder"] = operationOrder
				visit_info.insert(visit_info_dict)
				self.log.debug("添加访问次序成功。{}".format(visit_info_dict["operationOrder"]))
				self.log.debug("{}".format(visit_info_dict))

			else:	#访问过
				self.log.debug("见过访问 的请求 pvId=[{}]".format(page_request["tidePvId"]))
				#visit_info_res["lastAccessTime"] = page_request["date"] if "date" in page_request else None
				operationOrder = visit_info_res["operationOrder"]
				ele = self.construct_page_element(page_request)
				for i, page_ele in enumerate(page_info_res["pageElements"]): #把当前访问的次序搞定
					self.log.debug("{}".format(i))
					if self.check_element_indentity(ele, page_ele) == True:
						#self.log.debug("@@@@@@@@@@@@@@@@")
						#self.log.debug("page_info:{}".format(page_info_res))
						#self.log.debug("visit_info:{}".format(visit_info_res))
						#self.log.debug("ele:{}".format(ele))
						#self.log.debug("page_ele:{}".format(page_ele))
						#self.log.debug("{}".format(visit_info_res["elementInfo"][str(i)]))
						if str(i) in visit_info_res["elementInfo"]:

							#self.log.debug("times:{}".format( visit_info_res["elementInfo"][str(i)]["times"]))
							visit_info_res["elementInfo"][str(i)] = {"times": visit_info_res["elementInfo"][str(i)]["times"] + 1}
						else:
							visit_info_res["elementInfo"][str(i)]={"times":1}

						visit_info.update({"id":page_request["tidePvId"]},{"$set":{"elementInfo":visit_info_res["elementInfo"],"lastAccessTime":page_request["date"]}})

						operation = { str(i): 
										{
											"triggerTime": page_request["date"]
										}
									}
						operationOrder.append(operation)
						visit_info.update({"id":page_request["tidePvId"]},{"$set":{"operationOrder":operationOrder}})
						self.log.debug('修改访问次序成功。{}'.format(operationOrder))
						break
			
			visit_info_res = visit_info.find_one({"id":page_request["tidePvId"]})
			ele_amount = len(page_info_res["pageElements"]) #页面的元素数量


			operationOrder = visit_info_res["operationOrder"]
			operationInfo = visit_info_res["operationInfo"]
	
			if ele_amount > 1: #已经有至少一个元素了
				self.log.debug('页面已经有超过1个元素了')
				for i, ele in enumerate(page_info_res["pageElements"]):
					for j, ele in enumerate(page_info_res["pageElements"]):
						if i == j:
							#元素相同 不需要
							self.log.debug('元素相同，不要')
							continue
						else:
							obj_key = "{i}-{j}".format(i=i, j=j)
							self.log.debug("构建 {}-{} 的关系".format(i, j))
							if obj_key in operationInfo:
								continue
							else:
								order_length  = len(operationOrder)

								#更新时间时间间隔
								operationInfo[obj_key] = {"interval":None, "times":0}

								self.log.debug('{}'.format(operationOrder))

								for start_op in xrange(order_length):
									op_st_key = operationOrder[start_op].keys()[0]
									#self.log.debug("****[op_st_key = {}]****".format(op_st_key))
									#self.log.debug("{}".format(operationOrder[start_op]))
									op_st_val = operationOrder[start_op][op_st_key]["triggerTime"]
									if int(op_st_key) != i:
										continue
									else:
										for end_op in xrange(order_length):
											op_end_key = operationOrder[end_op].keys()[0]
											if op_st_key == op_end_key:
												continue
											else:
												self.log.debug("找到了一对关系。计算间隔时间")
												
												op_end_val = operationOrder[end_op][op_end_key]["triggerTime"]
												if int(op_end_key) == j :
													#如果正好是要寻求的起点
													interval_time = int(op_end_val) - int(op_st_val)
													
													if (operationInfo[obj_key]["interval"] is None or (operationInfo[obj_key] is not None and interval_time < operationInfo[obj_key]["interval"])):
														#如果存在的最短访问时间不存在，或者更短，替换之，否则不管
														self.log.debug("{}-{} 最短间隔为：{}".format(i, j, interval_time))
														operationInfo[obj_key]["interval"] = interval_time
								#更新点击次数:(倒序寻找，最后一次出现X的时刻)
								times = 0
								self.log.debug('更新点击次数')
								self.log.debug("{}".format(operationOrder))
			 					for index, reverse_op in enumerate(operationOrder[::-1]):
			 						self.log.debug("Reverse_op:{}".format(reverse_op))

			 						asc_index = order_length - 1 - index
			 						self.log.debug("asc_index:{}".format(asc_index))
			 						end_op = int(reverse_op.keys()[0]) 
			 						if int(end_op) == j:
			 							for index2 in xrange(0, asc_index - 1):
			 								if int(operationOrder[index].keys()[0]) == i:
			 									times += 1
			 									self.log.debug("在{}之前 出现了{}次{}".format(j, times, i))
			 							break

			 						else:
			 							continue
			 					operationInfo[obj_key]["times"] = times
			 					operationInfo[obj_key]["interval"] = None if operationInfo[obj_key]["times"] == 0 else operationInfo[obj_key]["interval"]

			visit_info_res["operationInfo"] = operationInfo

			visit_info.save(visit_info_res)

			self.log.debug("更新visit_info成功")

		except Exception, why:
			self.log.fatal("Save data to MongoDB occurred error: {}\n{}".format(why, traceback.format_exc()))
			raise why
