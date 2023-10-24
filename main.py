import glob
import json
import os
import base64
import logging

import flet as ft


logging.basicConfig(level=logging.INFO)


chara_list = []
tag_list = []

search_word = ""
selected_tag_list = []

async def get_images():
	print("Loading Images...")

	with open("data/images.json", mode="rb") as k:
		image_list = json.loads(k.read())

	# キャラクター一覧を作成
	print("- Loading Character & Tag List")
	for k in image_list.keys():
		if image_list[k]["character"] not in chara_list: chara_list.append(image_list[k]["character"])
		# タグ一覧を作成
		for t in image_list[k]["tags"]:
			if t not in tag_list: tag_list.append(t)
	print(f"- Done - Character: {len(chara_list)} | Tag: {len(tag_list)}")

	print(f"Done ({str(len(image_list))})")

	return image_list


async def main(page: ft.page):
	page.title = "Rel1cStyle 3D Image Gallery"
	page.padding = 20
	await page.update_async()

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

	# 画像の読み込み&生成
	async def load_images():
		print("Loading...")

		image_grid.controls = []
		count = 0

		if search_word != "" or len(selected_tag_list) >= 1: print(f"- Filtering - Word: {search_box} | Tags: {str(selected_tag_list)}")

		for image in image_list.keys():
			# タグで絞り込み
			if len(selected_tag_list) >= 1 and set(selected_tag_list).isdisjoint(image_list[image]["tags"]): continue

			# 検索ワードで絞り込み
			if search_word.lower() not in image.lower(): continue

			count += 1
			print(f"- {image} ({str(count)}/{len(image_list)})")

			# 画像を生成
			image_grid.controls.append(
				ft.Stack(
					controls=[
						ft.Image(
							src_base64=image_list[image]["preview"],
							fit=ft.ImageFit.CONTAIN,
							repeat=ft.ImageRepeat.NO_REPEAT,
							border_radius=ft.border_radius.all(5)
						),
						ft.Row(
							[
								ft.Text(
									image_list[image]["character"] + " | " + image_list[image]["skin"],
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
		await page.update_async()
		print(f"Filtered Image Count: {str(count)}")

	# タグの読み込み&生成
	async def load_tags():
		tag_box.controls = []
		for tag in tag_list:
			tag_box.controls.append(
				ft.Checkbox(
					label=tag,
					value=False,
					on_change=tag_checkbox_on_change
				)
			)
		print(f"Tag Control Count: {len(tag_box.controls)}")
		await page.update_async()

	##### タグボックス #####
	async def tag_checkbox_on_change(e):
		global selected_tag_list
		if e.control.value:
			if e.control.label not in selected_tag_list: selected_tag_list.append(e.control.label)
		else:
			if e.control.label in selected_tag_list: selected_tag_list.remove(e.control.label)
		print(f"Selected Tags: {str(selected_tag_list)}")
		await load_images()


	tag_box = ft.Row(
		scroll=ft.ScrollMode.AUTO,
		alignment=ft.MainAxisAlignment.CENTER,
		vertical_alignment=ft.CrossAxisAlignment.START,
		expand=False
	)

	tag_box_base = ft.Container(
		content=tag_box,
		alignment=ft.alignment.center_left,
		expand=True
	)

	##### 検索ボックス #####
	async def search_box_on_submit(e):
		global search_word
		search_word = e.control.value
		await load_images()

	search_box = ft.TextField(
		label="Search",
		on_submit=search_box_on_submit
	)

	search_box_base = ft.Container(
		content=search_box,
		alignment=ft.alignment.center
	)

	##### ベース #####
	base_column = ft.Column(
		controls=[
			search_box_base,
			tag_box,
			image_grid_base
		],
		expand=True
	)

	await page.add_async(base_column)

	await load_tags()
	await load_images()


ft.app(target=main, view=ft.AppView.WEB_BROWSER, assets_dir="assets")
