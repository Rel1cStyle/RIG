import glob
import json
import os
import base64
import logging
from typing import Any, List, Optional, Union

import flet as ft
from flet_core.control import Control, OptionalNumber
from flet_core.ref import Ref
from flet_core.types import AnimationValue, ClipBehavior, OffsetValue, ResponsiveNumber, RotateValue, ScaleValue

from app import App


logging.basicConfig(level=logging.INFO)


class Images():
	data: dict = {}
	legends: list = []
	tags: list = []

	async def load():
		print("Loading Images...")

		with open("data/images.json", mode="rb") as k:
			Images.data = json.loads(k.read())

		# キャラクター一覧を作成
		print("- Loading Character & Tag List")
		for k in Images.data.keys():
			if Images.data[k]["character"] not in Images.legends: Images.legends.append(Images.data[k]["character"])
			# タグ一覧を作成
			for t in Images.data[k]["tags"]:
				if t not in Images.tags: Images.tags.append(t)
		print(f"- Done - Character: {len(Images.legends)} | Tag: {len(Images.tags)}")

		print(f"Done ({str(len(Images.data))})")


class RRIGApp(ft.UserControl):
	def __init__(self):
		super().__init__()

		# 変数の初期化
		self.search_word = "" # 検索ワード
		self.selected_tags = [] # 選択中のタグ一覧


	def build(self):
		self.expand = True

		self.image_grid = ft.GridView(
			runs_count=5,
			max_extent=400,
			child_aspect_ratio=1.77,
			spacing=10,
			run_spacing=10,
			expand=True
		)

		self.image_grid_base = ft.Container(
			content=self.image_grid,
			alignment=ft.alignment.center,
			expand=True
		)


		##### タグボックス #####
		self.tag_box = ft.Row(
			scroll=ft.ScrollMode.AUTO,
			alignment=ft.MainAxisAlignment.CENTER,
			vertical_alignment=ft.CrossAxisAlignment.START,
			expand=False
		)

		self.tag_box_base = ft.Container(
			content=self.tag_box,
			alignment=ft.alignment.center_left,
			expand=True
		)


		##### 検索ボックス #####
		self.search_box = ft.TextField(
			label="Search",
			on_submit=self.search_box_on_submit
		)

		self.search_box_base = ft.Container(
			content=self.search_box,
			alignment=ft.alignment.center
		)

		# ベース部品
		return ft.Column(
			controls=[
				self.search_box_base,
				self.tag_box,
				self.image_grid_base
			],
			expand=True
		)

	# タグボックス
	async def tag_checkbox_on_change(self, e):
		if e.control.value:
			if e.control.label not in self.selected_tags: self.selected_tags.append(e.control.label)
		else:
			if e.control.label in self.selected_tags: self.selected_tags.remove(e.control.label)
		print(f"Selected Tags: {str(self.selected_tags)}")
		await self.load_images()

	# 検索ボックス
	async def search_box_on_submit(self, e):
		self.search_word = e.control.value
		await self.load_images()

	# 画像の読み込み&生成
	async def load_images(self):
		print("Loading...")

		self.image_grid.controls = []
		count = 0

		if self.search_word != "" or len(self.selected_tags) >= 1: print(f"- Filtering - Word: {self.search_box} | Tags: {str(self.selected_tags)}")

		for image in Images.data.keys():
			# タグで絞り込み
			if len(self.selected_tags) >= 1 and set(self.selected_tags).isdisjoint(Images.data[image]["tags"]): continue

			# 検索ワードで絞り込み
			if self.search_word.lower() not in image.lower(): continue

			count += 1
			#print(f"- {image} ({str(count)}/{len(Images.data)})")

			# 画像を生成
			self.image_grid.controls.append(
				ft.Stack(
					controls=[
						ft.Image(
							src_base64=Images.data[image]["preview"],
							fit=ft.ImageFit.CONTAIN,
							repeat=ft.ImageRepeat.NO_REPEAT,
							border_radius=ft.border_radius.all(5)
						),
						ft.Row(
							[
								ft.Text(
									Images.data[image]["character"] + " | " + Images.data[image]["skin"],
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
		await self.update_async()
		print(f"Filtered Image Count: {str(count)}")

	# タグの読み込み&生成
	async def load_tags(self):
		self.tag_box.controls = []
		for tag in Images.tags:
			self.tag_box.controls.append(
				ft.Checkbox(
					label=tag,
					value=False,
					on_change=self.tag_checkbox_on_change
				)
			)
		print(f"Tag Control Count: {len(self.tag_box.controls)}")
		await self.update_async()


async def main(page: ft.page):
	page.title = App.name
	page.padding = 20
	await page.update_async()

	print("Version: " + App.version)
	print("Commit: " + App.commit_sha)

	# 画像一覧を読み込み
	await Images.load()

	# アプリバー
	page.appbar = ft.AppBar(
		title=ft.Text(App.name, size=16),
		center_title=True,
		actions=[
			ft.Container(content=ft.Text(f"{App.version}-{App.branch}.{App.commit_sha}", size=14), padding=20)
		]
		#leading=ft.Image(
		#	src="icons/icon.png",
		#	fit=ft.ImageFit.CONTAIN
		#),
		#leading_width=50
	)

	base = RRIGApp()

	await page.add_async(base)

	await base.load_tags()
	await base.load_images()


ft.app(target=main, assets_dir="assets")
