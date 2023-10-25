from os import getenv

class App():
    name = "Rel1cStyle Render Image Gallery"
    version = "1.0"
    commit_sha = getenv("CF_PAGES_COMMIT_SHA")
