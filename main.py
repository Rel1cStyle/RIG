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
	tags: dict = {}

	async def load():
		print("Loading Images...")

		tag_base = {"count": 0}

		with open("data/images.json", mode="rb") as k:
			Images.data = json.loads(k.read())

		print("- Loading Character & Tag List")
		for k, v in Images.data.items():
			# レジェンド一覧を作成
			if v["character"] not in Images.legends: Images.legends.append(v["character"])
			# タグ一覧を作成
			for t in v["tags"]:
				if t not in Images.tags: Images.tags[t] = tag_base.copy() # タグが存在しない場合は新たに追加する
				Images.tags[t]["count"] += 1 # タグが存在する場合は個数のカウントを増やす
		# レジェンド一覧を名前順に並べ替え
		Images.legends.sort()
		# タグ一覧を名前順に並べ替え
		Images.tags = dict(sorted(Images.tags.items()))
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
			expand=True,
			animate_opacity=300
		)


		##### タグボックス #####
		self.tag_box_expand = False

		self.tag_box_expand_button = ft.ElevatedButton("Open", on_click=self.tag_box_expand_button_on_click)

		self.tag_box = ft.ListView(
			#scroll=ft.ScrollMode.AUTO,
			#alignment=ft.MainAxisAlignment.CENTER,
			#vertical_alignment=ft.CrossAxisAlignment.START,
			spacing=1,
			item_extent=20,
			horizontal=False,
			expand=True,
			visible=False
		)

		self.tag_box_base = ft.Column(
			[
				ft.Row(
					[
						ft.Text("Tags", size=18),
						self.tag_box_expand_button
					]
				),
				self.tag_box # タグ一覧部品
			],
			alignment=ft.alignment.center_left,
			expand=False
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
				self.tag_box_base,
				self.image_grid_base
			],
			expand=True
		)

	# タグボックス
	async def switch_tag_selection(self, tag_name: str, enable: bool=None):
		"""タグの有効/無効を切り替えます。

		Args:
			tag_name (str): 切り替えるタグの名前
			enable (bool, optional): 対象のタグを有効にするか無効にするか None の場合は切り替える
		"""
		if enable == None: enable = tag_name not in self.selected_tags
		
		if enable:
			if tag_name not in self.selected_tags: self.selected_tags.append(tag_name)
		else:
			if tag_name in self.selected_tags: self.selected_tags.remove(tag_name)

		# タグ一覧の部品のチェック状態を更新する
		for t in self.tag_box.controls:
			if tag_name == t.key:
				t.value = enable
				break
		
		print(f"Selected Tags: {str(self.selected_tags)}")
		
		await self.load_images()

	async def tag_box_expand_button_on_click(self, e):
		self.tag_box_expand = not self.tag_box_expand
		self.tag_box.visible = self.tag_box_expand
		self.tag_box_base.expand = self.tag_box_expand
		self.image_grid_base.visible = not self.tag_box_expand
		if self.tag_box_expand:
			self.tag_box_expand_button.text = "Close"
		else:
			self.tag_box_expand_button.text = "Open"
		await self.update_async()

	async def tag_checkbox_on_change(self, e):
		await self.switch_tag_selection(e.control.key, e.control.value)
		await self.load_images()

	# 検索ボックス
	async def search_box_on_submit(self, e):
		self.search_word = e.control.value
		await self.load_images()

	async def image_tag_button_on_click(self, e):
		await self.switch_tag_selection(e.control.text)

	# 画像の読み込み&生成
	async def load_images(self):
		print("Loading...")

		self.image_grid.controls = []
		count = 0

		if self.search_word != "" or len(self.selected_tags) >= 1: print(f"- Filtering - Word: {self.search_box} | Tags: {str(self.selected_tags)}")

		for k, v in Images.data.items():
			# ループ対象の画像に選択中のタグのいずれかが含まれているかチェック
			tag_found = not set(self.selected_tags).isdisjoint(v["tags"])

			# タグで絞り込み
			if len(self.selected_tags) >= 1 and not tag_found: continue

			# 検索ワードで絞り込み
			if self.search_word.lower() not in k.lower(): continue

			count += 1
			#print(f"- {image} ({str(count)}/{len(Images.data)})")

			# タグボタン部品を生成
			tag_buttons = []
			for tag in v["tags"]:
				tb = ft.Container(
						ft.Text(
							spans=[
								ft.TextSpan(
									tag,
									style=ft.TextStyle(
										14
									),
									on_click=self.image_tag_button_on_click
								)
							]
						),
						border_radius=ft.border_radius.all(14),
						padding=ft.padding.only(6, 4, 6, 4)
					)
				# 選択中のタグは色を変えて枠線をつける
				if tag in self.selected_tags:
					tb.bgcolor = ft.colors.BLACK
					tb.border = ft.border.all(2, color=ft.colors.WHITE)
				else:
					tb.bgcolor = ft.colors.BLACK54
				# タグ部品一覧へ追加
				tag_buttons.append(
					tb
				)

			# 画像を生成
			self.image_grid.controls.append(
				ft.Stack(
					controls=[
						# 画像
						ft.Image(
							src_base64=v["preview"],
							fit=ft.ImageFit.CONTAIN,
							repeat=ft.ImageRepeat.NO_REPEAT,
							border_radius=ft.border_radius.all(5)
						),
						# 画像情報(名前など)
						ft.Row(
							[
								ft.Text(
									v["character"] + " | " + v["skin"] + " - " + v["number"],
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
						),
						# タグ
						ft.Row(
							tag_buttons,
							alignment=ft.MainAxisAlignment.START,
							left=5,
							right=5,
							top=5
						)
					]
				)
			)
		await self.update_async()
		print(f"Filtered Image Count: {str(count)}")

	# タグの読み込み&生成
	async def load_tags(self):
		self.tag_box.controls = []
		for k, v in Images.tags.items():
			self.tag_box.controls.append(
				ft.Checkbox(
					key=k,
					label=k + " (" + str(v["count"]) + ")",
					value=False,
					on_change=self.tag_checkbox_on_change
				)
			)
		print(f"Tag Control Count: {len(self.tag_box.controls)}")
		await self.update_async()


async def main(page: ft.Page):
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
		center_title=False,
		actions=[
			# バージョン表記テキスト
			ft.Container(
				ft.Text(f"Branch: {App.branch} Commit: {App.commit_sha}", size=12, text_align=ft.TextAlign.RIGHT),
				padding=ft.padding.only(0, 0, 20, 0),
				alignment=ft.alignment.center_right,
				expand=False
			)
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
