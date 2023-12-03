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


def lists_match(l1: list, l2: list) -> bool:
	if len(l1) != len(l2):
		return False
	return all(x == y and type(x) == type(y) for x, y in zip(l1, l2))

class Images():
	data: dict = {}
	legends: dict = {}
	tags: dict = {}

	async def load():
		print("Loading Images...")

		skin_base = {"count": 0}
		legend_base = {"count": 0, "skins": None}
		tag_base = {"count": 0}

		with open("data/images.json", mode="rb") as k:
			Images.data = json.loads(k.read())

		print("- Loading Legends & Tag List")
		for k, v in Images.data.items():
			legend = str(v["character"])
			skin = str(v["skin"])

			# レジェンド一覧を作成
			Images.legends.setdefault(legend, legend_base.copy())["count"] += 1 # レジェンドのカウントを増やす

			# スキン一覧を作成
			if Images.legends[legend]["skins"] == None: Images.legends[legend]["skins"] = dict()
			Images.legends[legend]["skins"].setdefault(skin, skin_base.copy())["count"] += 1 # スキンのカウントを増やす

			# タグ一覧を作成
			for t in v["tags"]: Images.tags.setdefault(t, tag_base.copy())["count"] += 1 # タグのカウントを増やす

		# レジェンド一覧を名前順に並べ替え
		Images.legends = dict(sorted(Images.legends.items()))

		# スキン一覧を名前順に並べ替え
		for k, v in Images.legends.items(): v["skins"] = dict(sorted(v["skins"].items()))

		# タグ一覧を名前順に並べ替え
		Images.tags = dict(sorted(Images.tags.items()))

		print(f"- Done - Legends: {len(Images.legends)} | Tag: {len(Images.tags)}")
		print(f"Done ({str(len(Images.data))})")


class RRIGApp(ft.UserControl):
	def __init__(self):
		super().__init__()

		# 変数の初期化
		self.search_word = "" # 検索ワード
		self.selected_legends = [] # 選択中のレジェンド一覧
		self.selected_skins = [] # 選択中のスキン一覧
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


		##### フィルターボックス #####
		self.filter_box_expand = False
		self.filter_box_expand_button = ft.FilledButton("Filter", on_click=self.filter_box_expand_button_on_click)

		self.legend_box = ft.ListView(
			spacing=1,
			item_extent=20,
			horizontal=False,
			expand=True,
			visible=False
		)

		self.skin_box = ft.ListView(
			spacing=1,
			item_extent=20,
			horizontal=False,
			expand=True,
			visible=False
		)

		self.filter_control_box = ft.Row(
			[
				ft.Column(
					[
						ft.Row(
							[
								ft.Text("Legends", style=ft.TextThemeStyle.TITLE_LARGE),
								ft.FilledTonalButton("Reset", on_click=self.legend_reset_button_on_click)
							]
						),
						self.legend_box # レジェンド一覧
					],
					expand=True
				),
				ft.Column(
					[
						ft.Row(
							[
								ft.Text("Skin", style=ft.TextThemeStyle.TITLE_LARGE),
								ft.FilledTonalButton("Reset", on_click=self.skin_reset_button_on_click)
							]
						),
						self.skin_box # タグ一覧
					],
					expand=True
				),
			],
			expand=True,
			visible=False
		)

		##### タグボックス #####
		self.tag_box_expand = False
		self.tag_box_expand_button = ft.FilledButton("Tag", on_click=self.tag_box_expand_button_on_click)

		self.tag_box = ft.ListView(
			spacing=1,
			item_extent=20,
			horizontal=False,
			expand=True,
			visible=False
		)

		self.tag_control_box = ft.Row(
			[
				ft.Column(
					[
						ft.Row(
							[
								ft.Text("Tag", style=ft.TextThemeStyle.TITLE_LARGE),
								ft.FilledTonalButton("Reset", on_click=self.tag_reset_button_on_click)
							]
						),
						self.tag_box # タグ一覧
					],
					expand=True
				)
			],
			expand=True,
			visible=False
		)

		# 検索結果テキスト
		self.search_result_text = ft.Text("")

		##### フィルターボックス&タグボックス ベース部品 #####
		self.filter_box_base = ft.Column(
			[
				ft.Row(
					[
						self.filter_box_expand_button,
						self.tag_box_expand_button,
						self.search_result_text
					]
				),
				self.filter_control_box,
				self.tag_control_box
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
				self.filter_box_base,
				self.image_grid_base
			],
			expand=True
		)

	# レジェンドボックス
	async def switch_legend_selection(self, legend_name: str, enable: bool=None):
		"""レジェンドの選択状態を切り替えます。

		Args:
			tag_name (str): 切り替えるタグの名前
			enable (bool, optional): 対象のタグを有効にするか無効にするか None の場合は切り替える
		"""
		if enable == None: enable = legend_name not in self.selected_legends

		if enable:
			if legend_name not in self.selected_legends: self.selected_legends.append(legend_name)
		else:
			if legend_name in self.selected_legends: self.selected_legends.remove(legend_name)

		# チェックボックスの状態を更新する
		for c in self.legend_box.controls:
			if legend_name == c.key:
				c.value = enable
				break

		# スキン一覧を更新する
		await self.load_skins(self.selected_legends)

	async def reset_legend_selection(self):
		"""レジェンドの選択状態をリセットします。"""
		self.selected_legends = []
		for c in self.legend_box.controls:
			c.value = False
		await self.reset_skin_selection() # スキンの選択状態もリセットする
		await self.update_async()


	# スキンボックス
	async def switch_skin_selection(self, skin_name: str, enable: bool=None):
		"""スキンの選択状態を切り替えます。

		Args:
			skin_name (str): 切り替えるスキンの名前
			enable (bool, optional): 対象のスキンを有効にするか無効にするか None の場合は切り替える
		"""
		if enable == None: enable = skin_name not in self.selected_skins

		if enable:
			if skin_name not in self.selected_skins: self.selected_skins.append(skin_name)
		else:
			if skin_name in self.selected_skins: self.selected_skins.remove(skin_name)

		# チェックボックスの状態を更新する
		for c in self.skin_box.controls:
			if skin_name == c.key:
				c.value = enable
				break
		
		print(f"Selected Skins: {str(self.selected_skins)}")

	async def reset_skin_selection(self):
		"""スキンの選択状態をリセットします。"""
		self.selected_skins = []
		await self.load_skins(self.selected_legends)


	# タグボックス
	async def switch_tag_selection(self, tag_name: str, enable: bool=None):
		"""タグの選択状態を切り替えます。

		Args:
			tag_name (str): 切り替えるタグの名前
			enable (bool, optional): 対象のタグを有効にするか無効にするか None の場合は切り替える
		"""
		if enable == None: enable = tag_name not in self.selected_tags
		
		if enable:
			if tag_name not in self.selected_tags: self.selected_tags.append(tag_name)
		else:
			if tag_name in self.selected_tags: self.selected_tags.remove(tag_name)

		# チェックボックスの状態を更新する
		for c in self.tag_box.controls:
			if tag_name == c.key:
				c.value = enable
				break
		
		print(f"Selected Tags: {str(self.selected_tags)}")

	async def reset_tag_selection(self):
		"""タグの選択状態をリセットします。"""
		self.selected_tags = []
		for c in self.tag_box.controls:
			c.value = False
		await self.update_async()

	# レジェンド&スキン選択部品の表示切り替え
	async def filter_box_expand_button_on_click(self, e):
		self.filter_box_expand = not self.filter_box_expand

		self.filter_control_box.visible = self.filter_box_expand

		self.filter_box_base.expand = self.filter_box_expand

		self.legend_box.visible = self.filter_box_expand

		self.skin_box.visible = self.filter_box_expand

		self.tag_box_expand_button.disabled = self.filter_box_expand

		self.image_grid_base.visible = not self.filter_box_expand

		if self.filter_box_expand:
			self.filter_box_expand_button.text = "Close"
		else:
			self.filter_box_expand_button.text = "Filter"
			await self.load_images() # 画像一覧を更新する
		await self.update_async()

	# タグ選択部品の表示切り替え
	async def tag_box_expand_button_on_click(self, e):
		self.tag_box_expand = not self.tag_box_expand

		self.tag_control_box.visible = self.tag_box_expand

		self.filter_box_base.expand = self.tag_box_expand

		self.tag_box.visible = self.tag_box_expand

		self.filter_box_expand_button.disabled = self.tag_box_expand

		self.image_grid_base.visible = not self.tag_box_expand

		if self.tag_box_expand:
			self.tag_box_expand_button.text = "Close"
		else:
			self.tag_box_expand_button.text = "Tag"
			await self.load_images() # 画像一覧を更新する
		await self.update_async()


	async def legend_checkbox_on_change(self, e): # レジェンドが選択されたとき
		await self.switch_legend_selection(e.control.key, e.control.value)

	async def legend_reset_button_on_click(self, e): # レジェンドのリセットボタンがクリックされたとき
		await self.reset_legend_selection()


	async def skin_checkbox_on_change(self, e): # スキンが選択されたとき
		await self.switch_skin_selection(e.control.key, e.control.value)

	async def skin_reset_button_on_click(self, e): # スキンのリセットボタンがクリックされたとき
		await self.reset_skin_selection()


	async def tag_checkbox_on_change(self, e): # タグが選択されたとき
		await self.switch_tag_selection(e.control.key, e.control.value)

	async def tag_reset_button_on_click(self, e): # タグのリセットボタンがクリックされたとき
		await self.reset_tag_selection()


	# 検索ボックス
	async def search_box_on_submit(self, e):
		self.search_word = e.control.value
		await self.load_images()

	async def image_tag_button_on_click(self, e):
		await self.switch_tag_selection(e.control.text)
		await self.load_images()

	# 画像の読み込み&生成
	async def load_images(self):
		print("Loading...")

		self.image_grid.controls = []
		count = 0

		if self.search_word != "" or len(self.selected_tags) >= 1: print(f"- Filtering - Word: {self.search_box.value} | Tags: {str(self.selected_tags)}")

		for k, v in Images.data.items():
			# レジェンドで絞り込み
			if len(self.selected_legends) >= 1: # 選択されたレジェンドではない画像を除外
				if v["character"] not in self.selected_legends:
					continue

			# スキンで絞り込み
			if len(self.selected_skins) >= 1: # 選択されたスキンではない画像を除外
				if v["skin"] not in self.selected_skins:
					continue

			# タグで絞り込み
			if len(self.selected_tags) == 1: # 選択されたタグが1つのみの場合は、そのタグが含まれていない画像を除外
				if set(self.selected_tags).isdisjoint(v["tags"]):
					continue
			elif len(self.selected_tags) >= 2: # 選択されたタグが2つ以上の場合は、選択されたタグのうち一つでも含まれていない画像を除外
				if not set(self.selected_tags).issubset(v["tags"]):
					continue 

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
						padding=ft.padding.only(8, 4, 8, 4)
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
							src="data/images/" + k,
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

		# 検索結果テキストを更新
		self.search_result_text.value = f"Result: {str(count)}"

		await self.update_async()
		print(f"Filtered Image Count: {str(count)}")

	# レジェンドの読み込み&生成
	async def load_legends(self):
		self.legend_box.controls = []
		for k, v in Images.legends.items():
			self.legend_box.controls.append(
				ft.Checkbox(
					key=k,
					label=k + " (" + str(v["count"]) + ")",
					value=False,
					on_change=self.legend_checkbox_on_change
				)
			)
		print(f"Legend Control Count: {len(self.legend_box.controls)}")
		await self.update_async()

	# スキンの読み込み&生成
	async def load_skins(self, legends: list=Images.legends.keys()):
		if len(legends) == 0: legends = Images.legends.keys()

		skins = {}

		for l in legends:
			for k, v in Images.legends[l]["skins"].items():
				if k not in skins: skins[k] = v

		# スキン名一覧を名前順に並べ替え
		skins = dict(sorted(skins.items()))

		# 選択中のスキンをすべて消す
		self.selected_skins = []

		# 各スキンのチェックボックスを生成
		self.skin_box.controls = []
		for k, v in skins.items():
			self.skin_box.controls.append(
					ft.Checkbox(
						key=k,
						label=k + " (" + str(v["count"]) + ")",
						value=False,
						on_change=self.skin_checkbox_on_change
					)
				)
		print(f"Skin Control Count: {len(self.skin_box.controls)}")
		await self.update_async()

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

	await base.load_legends()
	await base.load_skins()
	await base.load_tags()
	await base.load_images()


ft.app(target=main, assets_dir="assets")
