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
	print("Loading Images...")

	with open("images.json", mode="rb") as i:
		image_list = json.loads(i.read())

	print("Done")

	return image_list


async def main(page: ft.page):
	page.title = "Rel1cStyle 3D Image Gallery"
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
		print("Loading...")

		image_grid.controls = []
		count = 0

		if t != "": print(f"- Filtering: {t}")

		for image in image_list.keys():
			if t.lower() not in image.lower(): continue
			count += 1
			print(f"- {image} ({str(count)}/{len(image_list)})")

			# 画像を生成
			image_grid.controls.append(
				ft.Stack(
					controls=[
						ft.Image(
							src_base64=image_list[image],
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


	async def search_box_on_submit(e):
		await load_images(e.control.value)

	search_box = ft.TextField(
		label="Search",
		on_submit=search_box_on_submit
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
