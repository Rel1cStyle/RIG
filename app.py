from os import path

class App():
	NAME = "Rel1cStyle RIG"

	VERSION = "0.2.4"

	API_URL = "https://api-rig-rel1cstyle.ezolys.com"

	COMMIT_SHA = ""
	BRANCH = ""
	ENV = ""

	if path.isfile("_commit_sha.txt"):
		with open("_commit_sha.txt", mode="r", encoding="utf-8") as f:
			COMMIT_SHA = f.read()[0:7].replace("\n", "")
	else:
		COMMIT_SHA = "0"

	if path.isfile("_branch_name.txt"):
		with open("_branch_name.txt", mode="r", encoding="utf-8") as f:
			BRANCH = f.read().replace("\n", "")
	else:
		BRANCH = "dev"

	if path.isfile("_env_name.txt"):
		with open("_env_name.txt", mode="r", encoding="utf-8") as f:
			ENV = f.read().replace("\n", "")
	else:
		ENV = "UNKNOWN"
