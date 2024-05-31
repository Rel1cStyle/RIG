from os import getenv

class App():
	NAME = "Rel1cStyle RIG"

	VERSION = "0.2.1"

	API_URL = "https://rig-api-thunder.rel1c.work"

	COMMIT_SHA = getenv("SOURCE_COMMIT")
	BRANCH = getenv("COOLIFY_BRANCH")
	ENV = getenv("DYNA")
