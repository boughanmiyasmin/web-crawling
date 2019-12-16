# -*- coding: utf-8 -*-
import scrapy
import glob
import os
from libScrapy import lib_scrapy
from scrapy import Spider
from scrapy.http import Request, FormRequest
from time import sleep
import re
import time
from selenium import webdriver
import requests
from scrapy.selector import Selector
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from random import randint

class AefSpider(scrapy.Spider):
	name = 'aef'
	allowed_domains = ['aef.cci.fr']
	#the start link
	start_urls = ['http://aef.cci.fr/']
	
	#Importing the driver for selemium use.
	global chromedriver
	chromedriver = webdriver.Chrome(executable_path = 'C:\ProgramData\chromedriver')
	
	global start
	start = time.time()

	# get the information on where to start the scraping like in page '6' on department '01' in name 'Piter'
	def __init__(self):
		global input_name
		global input_dep
		global input_page
		global quest
		quest = raw_input("Do you have a specific place you need to start with? [Y/N]")
		if quest == "y" or quest == "Y":
			input_name = raw_input("name :")
			input_dep = raw_input("department :")
			input_page = raw_input("page :")
		global url
		url = 'http://aef.cci.fr/'
		result_get = "False"
		while result_get not in "True":
			global chromedriver
			chromedriver, result_get = lib_scrapy().driver_get(chromedriver, url)

	def parse(self, response):
		global quest
		global input_name
		global input_dep
		global input_page
		# open the txt file that contains all the names 
		with open("prenom.txt", 'r+') as names:
			deps = 96
			page = None
			#if the input is yes start with the specific name, department and page.
			if quest == "y" or quest == "Y":
				s_dep = int(input_dep)
				input_page = int(input_page)
				for dep in range(s_dep,deps):
					items =  self.parse_start(input_name, dep, input_page)
					input_page = None
					for item in items:
						yield item
				for name in names:
					name = name.replace("\r","")
					name = name.replace("\n","")
					if name == input_name:
						break
				for name in names:
					for dep in range(1,deps):
						items = self.parse_start(name, dep, page)

						for item in items:
							yield item
			#otherwise start from the beginning.
			else:
				s_dep = 1
				for name in names:
					for dep in range(s_dep,deps):
						items = self.parse_start(name, dep, page)
						for item in items:
							yield item
				

	def parse_start(self, name, dep, page):
		global url 
		global chromedriver
		
		if dep < 10:
			dep = "0" + str(dep)
		else:
			dep = str(dep)
		name = (name.lower()).replace("\r","")
		name = (name.lower()).replace("\n","")
		
		element_name = chromedriver.find_element_by_id("nom")
		element_dep = chromedriver.find_element_by_id("dep")
		element_name.clear()
		element_dep.clear()
		element_name.send_keys(name)
		element_dep.send_keys(dep)
		result_click_ok = "False"
		page_num = 1
		while result_click_ok not in "True":
			ok = chromedriver.find_element_by_id("valider")
			chromedriver, result_click_ok = lib_scrapy().driver_click(chromedriver, ok)
			#-----------------------------------------------------------------------------------------------------------
			if page != None :
				for i in range(1,page):
					result_next = "False"
					while result_next not in "True":
						element_next = chromedriver.find_elements_by_link_text("Page suivante")
						chromedriver, result_next = lib_scrapy().driver_click(chromedriver, element_next[0])
				page_num = page
		#----------------------------------------------------------------------------------------------------------------
		more_pages = True
		back_button = 1
		while more_pages == True:
			to_print = ("***************** nom: "+ name + " , dep: " + str(dep) + " , page: " + str(page_num) )
			page_num = page_num + 1
			items = []
			try:
				for a_num in range(1,11):
					result_click = "False"
					while result_click not in "True":
						comp = chromedriver.find_element_by_xpath('//*[@id="listeEntreprises"]/li/table/tbody/tr[%s]/td[1]/strong/a' % a_num)
						chromedriver, result_click = lib_scrapy().driver_click(chromedriver, comp)
					#-----------------------------------------------------------------------------------------------------
					global start
					start =lib_scrapy().timer_code(start)
					print(start)
					print("\n")
					print( to_print + " , entreprise numero: " + str(a_num) + "************************")
					
					sleep(randint(5,8))
					#------------------------------------------------------------------------------------------------------
					sel = Selector(text=chromedriver.page_source)
					item = self.parse_items(sel)
					items.append(item)
					#------------------------------------------------------------------------------------------------------
					chromedriver.execute_script("window.history.go(-1)")
					sleep(randint(3,5))
					print(more_pages)
				#----------------------------------------------------------------------------------------------------------
				try:
					result_next = "False"
					while result_next not in "True":
						element_next = chromedriver.find_elements_by_link_text("Page suivante")
						chromedriver, result_next = lib_scrapy().driver_click(chromedriver, element_next[0])
					
				except IndexError:
					more_pages = False
					result_get_last = "False"
					while result_get_last not in "True":
						chromedriver, result_get_last = lib_scrapy().driver_get(chromedriver, url)
			except NoSuchElementException:
					
					more_pages = False
					result_get_last = "False"
					while result_get_last not in "True":
						chromedriver, result_get_last = lib_scrapy().driver_get(chromedriver, url)
		return items

	#extracting all the data from the html
	def parse_items(self, sel):
		try:	
			# ----------IDENTITÉ------------------
			siret = sel.xpath('.//div[@id="contenu"]/dl[1]/dd[1]/text()').extract_first()
			statut = sel.xpath('.//div[@id="contenu"]/dl[1]/dd[2]/text()').extract_first()
			categorie = sel.xpath('.//div[@id="contenu"]/dl[1]/dd[3]/text()').extract_first()
			lieu_dexercice = sel.xpath('.//div[@id="contenu"]/dl[1]/dd[4]/text()').extract_first()
			effectif = sel.xpath('.//div[@id="contenu"]/dl[1]/dd[5]/text()').extract_first()
			#----------COORDONNÉES-----------------
	
			dict = {}
			cp = voie = pays = c_voie = ville = tel_copie = tel = site = e_mail = None
			coor = sel.xpath('//*[@id="contenu"]/dl[2]').extract_first()
			l = coor.split("/dd>")
			for i in range(len(l)-1):
				lab = re.search('<dt>(.*)</dt>', l[i])
				val = re.search('<dd>(.*)<', l[i])
				if lab != None and val != None:
						dict[lab.group(1)] = val.group(1)
				keys = dict.keys()
				for key in keys :
					k = key.strip()
					k = k.encode("utf-8")
					if k in "Code postal":
						cp = dict[key]
					if k in "Voie":
						voie = dict[key]
					if k in "Pays":
						pays = dict[key]
					if k in "Complément voie":
						c_voie = dict[key]
					if k in "Ville":
						ville = dict[key]
					if k in "Télécopie":
						tel_copie = dict[key]
					if k in "Téléphone":
						tel = dict[key]
					if k in "Site internet":
						site = dict[key]
					if k in "E-mail":
						e_mail = dict[key]
	
			#----------INFORMATIONS ÉCONOMIQUES------
			date_debut = sel.xpath('.//div[@id="contenu"]/dl[3]/dd[1]/text()').extract_first()
			#----------Activité de l'établissement----
			code_APET = sel.xpath('.//div[@id="contenu"]/dl[4]/dd[1]/text()').extract_first()
			lib_code_APET = sel.xpath('.//div[@id="contenu"]/dl[4]/dd[2]/text()').extract_first()
			code_NAF = sel.xpath('.//div[@id="contenu"]/dl[4]/dd[3]/text()').extract_first()
			lib_code_NAF = sel.xpath('.//div[@id="contenu"]/dl[4]/dd[4]/text()').extract_first()
			activite = sel.xpath('.//div[@id="contenu"]/dl[4]/dd[5]/text()').extract_first()
			#-----------Identité----------------------
			siren = sel.xpath('.//div[@id="contenu"]/dl[5]/dd[1]/text()').extract_first()
			raison_sociale = sel.xpath('.//div[@id="contenu"]/dl[5]/dd[2]/text()').extract_first()
			denomination = sel.xpath('.//div[@id="contenu"]/dl[5]/dd[3]/text()').extract_first()
			#-----------Renseignements juridiques------
			ren_count = sel.xpath('count(.//div[@id="contenu"]/dl[6]/dt/text())').extract_first()
			capital_social = sel.xpath('.//div[@id="contenu"]/dl[6]/dd[1]/text()').extract_first()
			if ren_count > 1:
				forme_juridique = sel.xpath('.//div[@id="contenu"]/dl[6]/dd[2]/text()').extract_first()
			else:
				forme_juridique = None
			#-----------Dirigeants---------------------
			responsable_legal = sel.xpath('.//div[@id="contenu"]/div/dl/dd[1]/text()').extract_first()
			items = {'siret':siret,
        	        'statut':statut,
        	        'categorie':categorie,
        	        'lieu_dexercice':lieu_dexercice,
        	        'effectif':effectif,
        	        'voie':voie,
        	        'cp':cp,
        	        'ville':ville,
        	        'pays':pays,
        	        'tel_copie':tel_copie,
        	        'tel':tel,
        	        'site':site,
        	        'e_mail':e_mail,
        	        'date_debut':date_debut,
        	        'code_APET':code_APET,
        	        'lib_code_APET':lib_code_APET,
        	        'code_NAF':code_NAF,
        	        'lib_code_NAF':lib_code_NAF,
        	        'activite':activite,
        	        'siren':siren,
        	        'raison_sociale':raison_sociale,
        	        'denomination':denomination,
        	        'ren_count':ren_count,
        	        'capital_social':capital_social,
        	        'forme_juridique':forme_juridique,
        	        'responsable_legal':responsable_legal}
			return items
		except:
			pass

			
        	




