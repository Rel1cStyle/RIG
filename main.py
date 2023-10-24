import glob
import json
import os
import base64
import logging
from pyodide.http import pyfetch

import flet as ft


logging.basicConfig(level=logging.INFO)


backend_url = "https://rel1cstylefig-1-c7867224.deta.app/"


async def get_images():
	print("Fetching Images...")
	res = await pyfetch(backend_url + "list")
	list = json.loads(await res.text())
	image_list = []
	for image in list:
		res = await pyfetch(backend_url + image)
		img = await res.text()
		image_list.append(img)
	return image_list

	"""image_files = []

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

	return image_files"""


async def main(page: ft.page):
	page.title = "RFIG"
	page.padding = 20
	page.update()

	image_list = await get_images()
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

	async def load_images(t: str=""):
		image_grid.controls = []
		count = 0
		for image in image_list:
			if t.lower() not in image.lower(): continue
			count += 1
			# 画像を生成
			image_grid.controls.append(
				ft.Stack(
					controls=[
						ft.Image(
							src_base64=image,
							fit=ft.ImageFit.CONTAIN,
							repeat=ft.ImageRepeat.NO_REPEAT,
							border_radius=ft.border_radius.all(5)
						),
						ft.Row(
							[
								ft.Text(
									f"{image}",
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
		print(f"Filtered Image Count: {str(count)}")


	async def search_box_on_change(e):
		print(f"Filtering: {e.control.value}")
		await load_images(e.control.value)

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

	await load_images()


ft.app(target=main, view=ft.AppView.WEB_BROWSER)
