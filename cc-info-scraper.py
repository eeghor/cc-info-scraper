import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select  # to deal with dropdown menues
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import re
import pandas as pd
from collections import defaultdict, namedtuple

from datetime import datetime

# where there's a list of letters
start_page = "https://www.finder.com.au/credit-cards/credit-card-products"

# WAIT_TIME = 40

# CC = namedtuple("CC", "rcc_name purchase_rate annual_fee cash_rate min_cred_limit min_income cc_type temp_res")

driver = webdriver.Chrome('/Users/ik/Codes/cc-info-scraper/webdriver/chromedriver')
print("-------> scraping www.finder.com.au")

lst_nav_letters = []
lst_letters = []

driver.get(start_page)

# bar with letters
nav_bar = driver.find_element_by_class_name('az-listing__nav')

# collect all letters to explore
for letter_block in nav_bar.find_elements_by_xpath(".//div[@class='az-listing__nav-letter']"):
	lst_nav_letters.append(letter_block.text.strip())

print("collected {} letters to explore...".format(len(lst_nav_letters)))

# now go to the table with letters
tbl = driver.find_element_by_class_name('az-listing__items')

letter_dict = defaultdict(list)   #  {"A": [url1, url2, ..]}

# find all header lettters
for letter in lst_nav_letters:

	try:
		letter_header = driver.find_element_by_id(letter)
	except:
		print("nothing starts from {}".format(letter))
		continue

	if letter_header:

		print("exploring {}...".format(letter_header.text.strip()))
		# need to return to parent
		try:
			letter_list = letter_header.find_element_by_xpath("..").find_element_by_class_name('az-listing__list')
		except:
			print("no list for this letter!")
			continue
		try:
			letter_list_items = letter_list.find_elements_by_class_name('az-listing__item')
		except:
			print("list for this letter is empty")
			continue

		# so fi there are some items for this letter...
		if letter_list_items:

			for letter_item in letter_list_items:

				# link to the card page
				lnk = letter_item.find_element_by_xpath(".//a[@href]").get_attribute("href")
				letter_dict[letter].append(lnk)
		
		print("collected {} links for this letter...".format(len(letter_dict[letter])))
		
		# now start visiting the links
		for lnk in letter_dict[letter]:

			driver.get(lnk)
			# get to the more button and get another link to more details
			time.sleep(3)
			# collect all more button links
			more_button_links = []

			try:
				more_buttons = driver.find_elements_by_class_name("btn-more-link")
				for mb in more_buttons:
					more_button_links.append(mb.get_attribute("href"))
				print("collected {} links to detailed information...".format(len(more_button_links)))
			except:
				print("found NO more buttons!")

			for i, mb_link in enumerate(more_button_links):  # recall these ar elinks for current letter
				print("grabbing link {}".format(i + 1))
				driver.get(mb_link)
				print("ok.some sleep now...")
				time.sleep(3)
				# grab stuff from cc description
				print("get the table info...")
				try:
					cc_string = driver.find_element_by_xpath("//table[contains(@class, 'product_infobox')]").text.strip()
					print(cc_string)
					print("going to next link...")
				except:
					print("cannot find the table with detailed info!")

	driver.get(start_page)
	time.sleep(3)

driver.quit()

# print("done. retrieved {} match results".format(len(list_matches)))