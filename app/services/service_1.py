import os
import asyncio
import requests

from decimal import Decimal
from lxml import html as ht
from fastapi_utils.tasks import repeat_every
from pprint import pprint

from app import app
from app.config import DATA_DIR, REPEAT_PARSE_COINMARKETCAP, REPEAT_PARSE_COINGECKO, MORALIS_API_KEY
from app.utils import semaphore, _request, _request_while_with_proxy


# Parsers for coinmarketcap, coingecko
# Get tokens and token price from moralis api


def load_coinmarketcap_last_urls():
	try:
		with open(os.path.join(DATA_DIR, "coinmarketcap_last_urls.txt"), "r", encoding="utf-8") as file:
			return [row.strip("\n") for row in file]
	except FileNotFoundError:
		return []


def load_coingecko_last_urls():
	try:
		with open(os.path.join(DATA_DIR, "coingecko_last_urls.txt"), "r", encoding="utf-8") as file:
			return [row.strip("\n") for row in file]
	except FileNotFoundError:
		return []


async def parse_coingecko_data(item: dict):
	async with semaphore:
		txt = await _request_while_with_proxy(item["url"], json=False)
		doc = ht.document_fromstring(txt)
		try:
			item["contract"] = doc.xpath("//span[text()='Contract']/..//i[@data-address]")[0].get(
				"data-address").lower()
		except:
			item["contract"] = None
		try:
			item["api_id"] = doc.xpath("//span[text()='API id']/..//i[@data-address]")[0].get("data-address").lower()
		except:
			item["api_id"] = None


@repeat_every(seconds=REPEAT_PARSE_COINGECKO)
async def parse_coingecko_recent():
	try:
		print("Start coingecko parser")
		base_url = "https://www.coingecko.com"
		txt = await _request_while_with_proxy("https://www.coingecko.com/en/coins/recently_added", json=False)
		if txt:
			doc = ht.document_fromstring(txt)
			last_urls = load_coingecko_last_urls()
			items = doc.xpath("//span[@data-content='BSC']/../../../../../td[3]//a[1]")
			items += doc.xpath("//td[@data-sort='ethereum']/../td[3]//a[1]")
			data = []
			for item in items:
				url = base_url + item.get("href")
				if url not in last_urls:
					data.append({"url": url, "name": item.text.strip().lower()})
			tasks = [parse_coingecko_data(item) for item in data]
			await asyncio.gather(*tasks)
			cnt = 0
			with open(os.path.join(DATA_DIR, "data.txt"), "a+", encoding="utf-8") as file:
				for item in data:
					if item["contract"]:
						if item["contract"] not in app.coins_list:
							row = "|".join([item["contract"], item["api_id"]])
							file.write(row + "\n")
							cnt += 1
			with open(os.path.join(DATA_DIR, "coingecko_last_urls.txt"), "w", encoding="utf-8") as file:
				[file.write(item["url"] + "\n") for item in data if item["contract"]]
			print(f"From coingecko add {cnt} rows")
	except Exception as e:
		print(f"Error get data from coingecko", e)


async def parse_coinmarketcap_data(item: dict):
	async with semaphore:
		txt = await _request(item["url"], json=False)
		doc = ht.document_fromstring(txt)
		try:
			item["name"] = doc.xpath("//h2[contains(@class, 'h1')]")[0].text
		except:
			item["name"] = None
		try:
			xpath = "//div[@class='content']//span[@class='mainChainAddress']/.."
			item["address"] = doc.xpath(xpath)[0].get("href").split("/")[-1].lower()
		except:
			item["address"] = None


@repeat_every(seconds=REPEAT_PARSE_COINMARKETCAP)
async def parse_coinmarketcap_new():
	try:
		print("Start coinmarketcap parser")
		base_url = "https://coinmarketcap.com"
		txt = await _request("https://coinmarketcap.com/new/", json=False)
		doc = ht.document_fromstring(txt)
		items = doc.xpath("//div[text()='Binance Coin']/../../td[3]/a")
		last_urls = load_coinmarketcap_last_urls()
		data = []
		for item in items:
			url = base_url + item.get("href")
			if url not in last_urls:
				data.append({"url": url})
		tasks = [parse_coinmarketcap_data(item) for item in data]
		await asyncio.gather(*tasks)
		cnt = 0
		with open(os.path.join(DATA_DIR, "data.txt"), "a+", encoding="utf-8") as file:
			for item in data:
				if item["address"]:
					if item["address"] not in app.coins_list:
						row = "|".join([item["address"], item["name"]])
						file.write(row + "\n")
						cnt += 1
		with open(os.path.join(DATA_DIR, "coinmarketcap_last_urls.txt"), "w", encoding="utf-8") as file:
			[file.write(item["url"] + "\n") for item in data if item["address"]]
		print(f"From coinmarketcap add {cnt} rows")
	except Exception as e:
		print(f"Error get data from coinmarketcap", e)


def get_item_with_max_cost(data: list):
	item_with_max_price = {"cost": 0}
	for item in data:
		try:
			if item_with_max_price["cost"] < item["cost"]:
				item_with_max_price = item
		except:
			pass
	return item_with_max_price


def get_token_price_moralis(token: dict, chain="bsc"):
	url = f"https://deep-index.moralis.io/api/v2/erc20/{token['token_address']}/price?chain={chain}"
	headers = {
		"x-api-key": MORALIS_API_KEY
	}
	try:
		data = requests.get(url, headers=headers).json()
		token["price"] = float(data.get("usdPrice"))
		token["cost"] = token["price"] * token["count"]
	except:
		print(f"Error get price to token: {token}")
		token["price"] = 0


def get_tokens_moralis(address: str, chain="bsc"):
	url = f"https://deep-index.moralis.io/api/v2/{address}/erc20?chain={chain}"
	headers = {
		"x-api-key": MORALIS_API_KEY
	}
	tokens = []
	try:
		data = requests.get(url, headers=headers).json()
		for item in data:
			if item["token_address"] in app.coins_list:
				tokens.append(
					{
						"token_address": item.get("token_address"),
						"token_name": item.get("symbol"),
						"decimals": int(item.get("decimals", 0)),
						"count": int(item["balance"]) / (10 ** int(item["decimals"]))
					}
				)
		return tokens
	except Exception as e:
		print(f"Error get tokens to {address} {e}")
