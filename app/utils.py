import os
import asyncio
import aiohttp

from aiohttp_socks import ProxyConnector
from random import choice
from fastapi_utils.tasks import repeat_every
from app import app

from app.config import DATA_DIR, MAX_ATTEMPTS, MAX_ACTIVE_COMPOUNDS, TIMEOUT, REPEAT_LOAD_COINS_LIST, \
	FILE_WITH_PROXIES, PROJECT_DIR, PROXY_TYPE

timeout = aiohttp.ClientTimeout(TIMEOUT)
semaphore = asyncio.BoundedSemaphore(MAX_ACTIVE_COMPOUNDS)


def load_proxies():
	app.proxies = []
	try:
		with open(os.path.join(PROJECT_DIR, FILE_WITH_PROXIES), "r") as file:
			for row in file:
				row = row.strip("\n").strip()
				row = row.strip("\n").split(":")
				proxy = f"{PROXY_TYPE}://{row[2]}:{row[3]}@{row[0]}:{row[1]}"
				app.proxies.append(proxy)
	except FileNotFoundError:
		print("File with proxies not found")


def load_coins_list():
	try:
		with open(os.path.join(DATA_DIR, "data.txt"), "r", encoding="utf-8") as file:
			data = [row.strip("\n").lower() for row in file]
		app.coins_list = list(set([item.split("|")[0] for item in data]))
	except FileNotFoundError:
		app.coins_list = []


@repeat_every(seconds=REPEAT_LOAD_COINS_LIST)
def reload_coins_list():
	try:
		with open(os.path.join(DATA_DIR, "data.txt"), "r", encoding="utf-8") as file:
			data = [row.strip("\n").lower() for row in file]
		app.coins_list = list(set([item.split("|")[0] for item in data]))
	except FileNotFoundError:
		app["coins_list"] = []


async def _request_while_with_proxy(url: str, json: bool = True):
	while True:
		if not app.proxies:
			break
		connector = ProxyConnector.from_url(choice(app.proxies))
		try:
			async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
				async with session.get(url, timeout=timeout) as response:
					if response.status == 200:
						if json:
							content = await response.json()
						else:
							content = await response.text()
						if content:
							return content
		except:
			continue


async def _request(url: str, headers: dict = None, json: bool = True):
	attempt = 1
	while attempt <= MAX_ATTEMPTS:
		attempt += 1
		try:
			async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
				async with session.get(url, timeout=timeout, headers=headers) as response:
					print(response.status)
					if response.status == 200:
						if json:
							content = await response.json()
						else:
							content = await response.text()
						if content:
							return content
		except:
			continue
