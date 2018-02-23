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

CC = namedtuple("CC", "cc_name annual_fee min_cred_limit min_income cc_type temp_res")

"""
Product Name ANZ First Visa Credit Card
Balance transfer rate (p.a.) 0% p.a. for 16 months with 2% balance transfer fee
Balance Transfer Revert Rate Standard Balance Transfer Revert Rate (21.49% p.a.)
Balance Transfer Limit 95% of available credit limit
Purchase rate (p.a.) 19.74% p.a.
Annual fee $30 p.a.
Interest Free Period Up to 44 days on purchases
Cash advance rate (p.a.) 21.49% p.a.
Min credit limit $1,000
Max credit limit $15,000
Minimum Monthly Repayment 2% of the closing balance or $25, whichever is greater
Minimum Income $15,000
Card Type Visa
Late Payment Fee $20
Foreign Currency Conversion Fee (VISA) 3% of transaction value
Complimentary Travel Insurance No
Available To Temporary Residents No
Joint Application No
"""
def parse_cc_string(s):

	rows = s.strip().lower().split("\n")

	cc_name = None
	cc_type = None
	annual_fee = None
	min_cred_limit = None
	max_cred_limit = None
	min_income = None
	temp_res = None

	for row in rows:

		if "product" in row.split():
			cc_name = " ".join([w.strip() for w  in row.split("product name") if w.strip()])
		
		if "annual" in row.split():
			annual_fee = "".join([w for w in row.split() if "$" in w]).split("(")[-1]
		
		if  len(set("min credit limit".split()) & set(row.split())) == 3:
			min_cred_limit = "".join([w for w in row.split() if "$" in w])

		if len(set("minimum income".split()) & set(row.split())) == 2:
			min_income = "".join([w for w in row.split() if "$" in w])

		if len(set("card type".split()) & set(row.split())) == 2:
			cc_type = " ".join([w.strip() for w  in row.split("card type") if w.strip()])

		if len(set("available to temporary residents".split()) & set(row.split())) == 4:
			temp_res = "".join([w.strip() for w  in row.split("available to temporary residents") if w.strip()])

	return CC(cc_name=cc_name, annual_fee=annual_fee,
		min_cred_limit=min_cred_limit,
		min_income=min_income, cc_type=cc_type,temp_res=temp_res)

collected_ccs = list()

# where there's a list of letters
start_page = "https://www.finder.com.au/credit-cards/credit-card-products"

# WAIT_TIME = 40

# CC = namedtuple("CC", "rcc_name purchase_rate annual_fee cash_rate min_cred_limit min_income cc_type temp_res")

driver = webdriver.Chrome('/Users/ik/Codes/cc-info-scraper/webdriver/chromedriver')
print("-------> scraping www.finder.com.au")

lst_nav_letters = []
lst_letters = []

driver.get(start_page)
time.sleep(5)
# bar with letters
nav_bar = driver.find_element_by_class_name('az-listing__nav')

# collect all letters to explore
for letter_block in nav_bar.find_elements_by_xpath(".//div[@class='az-listing__nav-letter']"):
	lst_nav_letters.append(letter_block.text.strip())

print("collected {} letters to explore...".format(len(lst_nav_letters)))

letter_dict = defaultdict(list)   #  {"A": [url1, url2, ..]}

# find all header lettters
for letter in lst_nav_letters:

	try:
		letter_header = driver.find_element_by_id(letter)
	except:
		print("nothing starts from {}! on to the next letter in navigation...".format(letter))
		continue

	if letter_header:

		print("exploring {}...".format(letter_header.text.strip()))

		try:
			letter_list = letter_header.find_element_by_xpath("..").find_element_by_class_name('az-listing__list')
		except:
			print("no list for this letter! on to the next letter in navigation...")
			continue
		try:
			letter_list_items = letter_list.find_elements_by_class_name('az-listing__item')
		except:
			print("list for this letter is empty! on to the next letter in navigation...")
			continue

		# so fi there are some items for this letter...
		if letter_list_items:

			for letter_item in letter_list_items:

				# link to the card page
				lnk = letter_item.find_element_by_xpath(".//a[@href]").get_attribute("href")
				letter_dict[letter].append(lnk)

		print("collected {} links for this letter...".format(len(letter_dict[letter])))
		
		# now start visiting the urls
		for lnk in letter_dict[letter]:

			print("url: {}...".format(lnk))
			driver.get(lnk)
			# get to the more button and get another link to more details
			time.sleep(5)
			# collect all more button links
			more_info_links = []

			try:
				row = driver.find_element_by_xpath("//form[contains(@name, 'compareForm')]")
			except:
				print("cannot find any form with card info! going to the next link...")
				continue

			try:
				more_info_urls = row.find_elements_by_link_text("More info")
			except:
				print("cannot find any more info urls!")
				continue

			if more_info_urls:

				for mb in more_info_urls:
					more_info_links.append(mb.get_attribute("href"))
				print("collected {} links to detailed information...".format(len(more_info_links)))
	

				for i, mb_link in enumerate(more_info_links):  # recall these ar elinks for current letter
					print("grabbing link {}".format(i + 1))
					driver.get(mb_link)
					time.sleep(5)
					try:
						cc_string = driver.find_element_by_xpath("//table[contains(@class, 'product_infobox')]").text.strip()
					except:
						print("cannot find any table with credit card description!")
						continue

					if cc_string:
						parse_cc_string(cc_string)

						try:
							collected_ccs.append(parse_cc_string(cc_string))
						except:
							print("cannot do parsing!")
							continue

	# go back to starting page
	driver.get(start_page)
	time.sleep(5)

driver.quit()

print("done. retrieved {} credit card descriptions".format(len(collected_ccs)))

if len(collected_ccs) > 0:
	df = pd.DataFrame(collected_ccs, columns=collected_ccs[0]._fields)
	print(df.head())
	df.to_csv("ccs.csv", index=False)