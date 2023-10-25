from os import getenv

class App():
    def __init__(self):
        App.name = "Rel1cStyle Render Image Gallery"
        App.version = "1.0"
        with open("_commit_sha.txt", mode="r") as f:
            App.commit_sha = f.read()
