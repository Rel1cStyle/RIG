class App():
	name = "Rel1cStyle Render Image Gallery"
	version = "1.0"
	try:
		with open("_commit_sha.txt", mode="r") as f:
			commit_sha = f.read()
	except Exception:
		commit_sha = "dev"
