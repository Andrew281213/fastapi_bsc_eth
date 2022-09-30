with open("data.txt", "r") as file:
	data = [row.strip("\n") for row in file]

new_data = []
new_addresses = []
for row in data:
	row = row.lower()
	address = row.split("|")[0]
	if address not in new_addresses:
		new_addresses.append(address)
		new_data.append(row)
with open("new_data.txt", "w", encoding="utf-8") as file:
	[file.write(row + "\n") for row in new_data]
