import logging
import os

from fastapi import Body, FastAPI, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse,Response
from deta import Deta


logging.basicConfig(level=logging.DEBUG)


app = FastAPI()

deta = Deta(project_key=os.getenv("DETA_PROJECT_KEY"))

dd = deta.Drive("free_images")


@app.get("/list")
def get_image_list():
	return (JSONResponse(content=jsonable_encoder(image_list)))

@app.get("/", responses={200: {"content": {"image/jpeg": {}}}}, response_class=Response)
def get_image(name: str):
	if name in image_list:
		with dd.get(name) as i:
			img = i.read()
		return Response(content=img, media_type="image/jpeg")
	else:
		return Response(content=None, status_code=404)


def main():
	global image_list
	image_list = dd.list()["names"]


main()
