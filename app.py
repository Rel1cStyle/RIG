from os import path

class App():
	name = "Rel1cStyle RIG"

	version = "0.1"

	api_url = "http://rig-api-thunder.rel1c.work"

	if path.isfile("_commit_sha.txt"):
		with open("_commit_sha.txt", mode="r") as f:
			commit_sha = f.read()[0:7]
			commit_sha = commit_sha.replace("\n", "")
	else:
		commit_sha = "0"

	if path.isfile("_branch_name.txt"):
		with open("_branch_name.txt", mode="r") as f:
			branch = f.read()
			branch = branch.replace("\n", "")
	else:
		branch = "dev"
