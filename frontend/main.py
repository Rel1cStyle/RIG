import glob
import json
import os
import base64
import logging
import requests

from deta import Deta
import flet as ft


logging.basicConfig(level=logging.DEBUG)


backend_url = "https://rel1cstylefig-1-c7867224.deta.app"


def get_images():
	res = requests.get(backend_url + "/list")
	image_list = json.loads(res.text)
	image_files = []

	os.makedirs(f"/tmp/images", exist_ok=True)

	for image_name in image_list:
		if not image_name.endswith(".webp"): continue
		# 画像を取得する
		image_bytes = requests.get(backend_url, params={"name": image_name}).content
		# 画像をファイルに書き込む
		with open("/tmp/images/" + image_name, "wb") as f:
			f.write(image_bytes)
		image_bytes.close()
		# 画像一覧へ追加
		image_files.append("/tmp/images/" + image_name)

	return image_files


def main(page: ft.page):
	page.title = "RFIG"
	page.padding = 20
	page.update()

	image_list = get_images()
	print("Image Count: " + str(len(image_list)))

	image_grid = ft.GridView(
		expand=True,
		runs_count=5,
		max_extent=400,
		child_aspect_ratio=1.77,
		spacing=10,
		run_spacing=10,
	)

	image_grid_base = ft.Container(
		content=image_grid,
		alignment=ft.alignment.center,
		expand=True
	)

	def load_images(t: str=""):
		image_grid.controls = []
		for image in image_list:
			if t.lower() not in os.path.basename(image).lower(): continue
			# 画像を生成
			image_grid.controls.append(
				ft.Stack(
					controls=[
						ft.Image(
							src=image,
							fit=ft.ImageFit.CONTAIN,
							repeat=ft.ImageRepeat.NO_REPEAT,
							border_radius=ft.border_radius.all(5)
						),
						ft.Row(
							[
								ft.Text(
									f"{os.path.basename(image)}",
									color="white",
									#bgcolor="black",
									size=14,
									weight="regular",
									opacity=0.7
								)
							],
							alignment=ft.MainAxisAlignment.CENTER,
							left=5,
							right=5,
							bottom=5
						)
					]
				)
			)
		page.update()


	def search_box_on_change(e):
		print(f"Filtering: {e.control.value}")
		load_images(e.control.value)

	search_box = ft.TextField(
		label="Search",
		on_change=search_box_on_change
	)

	search_box_base = ft.Container(
		content=search_box,
		alignment=ft.alignment.center
	)

	base_column = ft.Column(
		controls=[
			search_box_base,
			image_grid_base
		],
		expand=True
	)

	page.add(base_column)

	load_images()


ft.app(target=main, view=ft.AppView.WEB_BROWSER)
