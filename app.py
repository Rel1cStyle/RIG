from os import environ, path

class App():
	NAME = "Rel1cStyle RIG"

	VERSION = "0.2.1"

	#API_URL = "https://api.rig.rel1c.work"
	API_URL = "https://rig-api-thunder.rel1c.work"
	#preview_image_url = "https://rig-r2-images.huerisalter.com"

	COMMIT_SHA = ""
	BRANCH = ""
	ENV = ""

	if path.isfile("_commit_sha.txt"):
		with open("_commit_sha.txt", mode="r") as f:
			COMMIT_SHA = f.read()[0:7].replace("\n", "")
	else:
		COMMIT_SHA = "0"

	if path.isfile("_branch_name.txt"):
		with open("_branch_name.txt", mode="r") as f:
			BRANCH = f.read().replace("\n", "")
	else:
		BRANCH = "dev"

	if path.isfile("_env_name.txt"):
		with open("_env_name.txt", mode="r") as f:
			ENV = f.read().replace("\n", "")
	else:
		ENV = "UNKNOWN"
