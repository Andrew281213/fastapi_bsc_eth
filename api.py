import uvicorn

from app import app
from app.config import HOST, PORT, SSL_KEYFILE, SSL_CERTFILE
from app.services.service_1 import get_item_with_max_cost, parse_coinmarketcap_new, parse_coingecko_recent, \
	get_token_price_moralis, get_tokens_moralis
from app.utils import load_coins_list, load_proxies

print("=" * 50)
print("tg: @tanf93")
print("=" * 50)


@app.on_event("startup")
async def startup():
	load_coins_list()
	load_proxies()
	# await parse_coingecko_recent()
	# await parse_coinmarketcap_new()


@app.get("/bsc/{address}")
async def get_token(address: str):
	data = get_tokens_moralis(address, chain="bsc")
	[get_token_price_moralis(token) for token in data]
	item_with_max_price = get_item_with_max_cost(data)
	return {"address": address, "data": item_with_max_price}


@app.get("/bsc/{address}/debug")
async def get_token(address: str):
	data = get_tokens_moralis(address, chain="bsc")
	[get_token_price_moralis(token) for token in data]
	return {"address": address, "data": data}


@app.get("/eth/{address}")
async def get_service2_token(address: str):
	data = get_tokens_moralis(address, chain="eth")
	[get_token_price_moralis(token, chain="eth") for token in data]
	item_with_max_price = get_item_with_max_cost(data)
	return {"address": address, "data": item_with_max_price}


@app.get("/eth/{address}/debug")
async def get_service2_token(address: str):
	data = get_tokens_moralis(address, chain="eth")
	[get_token_price_moralis(token, chain="eth") for token in data]
	return {"address": address, "data": data}


if __name__ == '__main__':
	uvicorn.run("app:app", host=HOST, port=PORT, ssl_keyfile=SSL_KEYFILE, ssl_certfile=SSL_CERTFILE, reload=True)
