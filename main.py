import asyncio
#import glob
#import json
import os
#import base64
import logging
#import time
from typing import Any, List, Optional, Union
import requests
import pyodide_http

import flet as ft
from flet_core.control import Control, OptionalNumber
from flet_core.ref import Ref
from flet_core.types import AnimationValue, ClipBehavior, OffsetValue, ResponsiveNumber, RotateValue, ScaleValue

from app import App


logging.basicConfig(level=logging.INFO)

pyodide_http.patch_requests()


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

		#with open("data/images.json", mode="rb") as k:
		#	Images.data = json.loads(k.read())
		res = requests.get(App.api_url + "/image/list")
		Images.data = res.json()

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


def loading_ctrl() -> ft.Container:
	return ft.Container(
		ft.Column(
			[
				ft.ProgressRing(),
				ft.Text("Loading", text_align=ft.TextAlign.CENTER)
			],
			expand=True,
			alignment=ft.MainAxisAlignment.CENTER,
			horizontal_alignment=ft.CrossAxisAlignment.CENTER
		),
		#bgcolor=,
		alignment=ft.alignment.center
	)

def appbar_ctrl() -> ft.AppBar:
	return ft.AppBar(
		title=ft.Column(
			[
				# タイトル
				ft.Text(App.name, size=16),
				# バージョン表記テキスト
				ft.Container(
					ft.Text(f"Version {App.version}-{App.branch}.{App.commit_sha}", size=12, text_align=ft.TextAlign.LEFT),
					padding=ft.padding.only(0, 0, 0, 0),
					alignment=ft.alignment.center_left,
					expand=False
				)
			],
			spacing=3
		),
		center_title=False,
		actions=[]
		#leading=ft.Image(
		#	src="icons/icon.png",
		#	fit=ft.ImageFit.CONTAIN
		#),
		#leading_width=50
	)

class RRIGApp(ft.View):
	def __init__(self):
		# 変数の初期化
		self.search_word = "" # 検索ワード
		self.selected_legends = [] # 選択中のレジェンド一覧
		self.selected_skins = [] # 選択中のスキン一覧
		self.selected_tags = [] # 選択中のタグ一覧

		##### 画像タイル #####
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
			expand=False,
			on_submit=self.search_box_on_submit
		)

		self.search_button = ft.IconButton(ft.icons.SEARCH, on_click=self.search_button_on_click)

		self.search_box_base = ft.Container(
			ft.Row(
				[
					self.search_box,
					self.search_button
				],
				expand=True,
				wrap=True,
				alignment=ft.MainAxisAlignment.END
			),
			expand=True,
			alignment=ft.alignment.center,
			padding=ft.padding.only(0, 0, 15, 0)
		)

		self.appbar_ctrl = appbar_ctrl()
		self.appbar_ctrl.toolbar_height = 80
		self.appbar_ctrl.actions.append(self.search_box_base)

		# ベース部品
		controls = [
			self.appbar_ctrl,
			#self.search_box_base,
			self.filter_box_base,
			self.image_grid_base
		]

		super().__init__("/", controls=controls)

	# サイズ変更イベント
	async def on_resize(self, e: ft.ControlEvent):
		_size = e.data.split(","); width = float(_size[0]); height = float(_size[1])
		self.appbar_ctrl.title.visible = width > 500
		await self.update_async()

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

	async def search_button_on_click(self, e):
		self.search_word = self.search_box.value
		await self.load_images()

	# 画像ダウンロードボタンクリック時
	async def image_download_button_on_click(self, e):
		await self.page.go_async("/image/preview/" + os.path.splitext(os.path.basename(e.control.key))[0])

	# 画像タグクリック時
	async def image_tag_button_on_click(self, e):
		await self.switch_tag_selection(e.control.text)
		await self.load_images()

	# 画像の読み込み&生成
	async def load_images(self):
		print("Loading...")

		# 読み込み表示
		self.page.splash = loading_ctrl()
		await self.page.update_async()

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

			# ダウンロードボタン
			"""dl_button = ft.IconButton(
				ft.icons.DOWNLOAD,
				#url=App.api_url + "/image/download/" + k,
				key=k,
				style=ft.ButtonStyle(
					color=ft.colors.WHITE,
					bgcolor=ft.colors.BLACK54
				),
				on_click=self.image_download_button_on_click
			)"""

			# 画像を生成
			self.image_grid.controls.append(
				ft.Stack(
					controls=[
						# 画像
						ft.Image(
							src=App.api_url + "/image/preview/" + k,
							fit=ft.ImageFit.CONTAIN,
							repeat=ft.ImageRepeat.NO_REPEAT,
							border_radius=ft.border_radius.all(5)
						),
						ft.Container(
							ft.Row(
								[
									# 画像情報テキスト
									ft.Text(
										v["character"] + " | " + v["skin"] + " - " + v["number"],
										color="white",
										#bgcolor="black",
										size=14,
										weight="regular",
										opacity=0.8,
									),
									#dl_button
								],
								alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
								vertical_alignment=ft.CrossAxisAlignment.END
							),
							key=k,
							margin=ft.padding.all(10),
							alignment=ft.alignment.bottom_center,
							on_click=self.image_download_button_on_click
							#gradient=ft.LinearGradient(
							#	begin=ft.alignment.top_center,
							#	end=ft.alignment.bottom_center,
							#	colors=[ft.colors.TRANSPARENT, ft.colors.BLACK]
							#)
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

			# URLが設定されていない画像の場合はダウンロードボタンを隠す
			#dl_button.visible = (v["url"] != "")

		# 検索結果テキストを更新
		self.search_result_text.value = f"Result: {str(count)}"

		# 読み込み表示を消す
		self.page.splash = None
		await self.page.update_async()

		await self.update_async()
		print(f"Done: {str(count)}")

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
				if k not in skins: skins[k] = v # スキンを追加する
				else: skins[k]["count"] += v["count"] # すでにスキンがリストにある場合はカウントを増やす

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


# ダウンロードプレビュービュー
class DLPreviewView(ft.View):
	def __init__(self, image_name: str):
		self.image_name = image_name
		controls = [
			appbar_ctrl(),
			ft.Container(
				ft.Column(
					[
						# プレビュー画像 & 画像名 & ダウンロードボタン
						ft.Column(
							[
								ft.Image(
									src=App.api_url + "/image/preview/" + image_name,
									fit=ft.ImageFit.CONTAIN,
									repeat=ft.ImageRepeat.NO_REPEAT,
									border_radius=ft.border_radius.all(5)
								),
								ft.Text(
									image_name
								),
								ft.FilledButton(
									"Download",
									icon=ft.icons.DOWNLOAD,
									on_click=self.download
								)
							],
							expand=False,
							alignment=ft.MainAxisAlignment.CENTER,
							horizontal_alignment=ft.CrossAxisAlignment.CENTER,
						)
					],
					expand=True,
					alignment=ft.MainAxisAlignment.SPACE_AROUND,
					horizontal_alignment=ft.CrossAxisAlignment.START
				),
				expand=True,
				alignment=ft.alignment.center
			)
		]
		super().__init__("/image/preview/" + image_name, controls=controls)

	async def download(self, e):
		await self.page.go_async("/image/download/" + self.image_name)

# ダウンロードビュー
class DLAcceptView(ft.View):
	def __init__(self, image_name: str):
		self.image_name = image_name

		self.twitter_button = ft.FilledButton(
			"Twitter",
			url="https://x.com/Apex_tyaneko",
			url_target="_blank",
			on_click=self.follow_twitter
		)
		self.download_button = ft.FilledButton(
			"Download",
			url=App.api_url + "/image/download/" + image_name,
			url_target="_blank",
			icon=ft.icons.DOWNLOAD,
			style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.WHITE),
			key=image_name,
			disabled=True,
			on_click=self.accept
		)
		self.button_ctrls = ft.Row(
			[
				self.twitter_button,
				self.download_button
			],
			#wrap=True,
			alignment=ft.MainAxisAlignment.START,
			vertical_alignment=ft.CrossAxisAlignment.CENTER
		)
		self.preview_image = ft.Image("sample1.png", fit=ft.ImageFit.CONTAIN, expand=1)

		controls = [
			appbar_ctrl(),
			ft.Container(
				ft.Row(
					[
						ft.Container(
							ft.Row(
								[
									ft.Column(
										[
											ft.Text("ダウンロード条件", style=ft.TextThemeStyle.DISPLAY_SMALL, weight=ft.FontWeight.BOLD),
											ft.Text("このフリー画像を使用する際は、\n@Apex_tyaneko をフォローしてから使用してください。", style=ft.TextThemeStyle.BODY_LARGE, size=18),
											ft.Text("文字入れ・立ち絵入れは○\n\"それ以外\"の加工はおやめください。", style=ft.TextThemeStyle.BODY_LARGE, size=18),
											self.button_ctrls
										],
										scroll=ft.ScrollMode.ALWAYS,
										expand=True,
										spacing=30,
										alignment=ft.MainAxisAlignment.CENTER,
										horizontal_alignment=ft.CrossAxisAlignment.START,
									)
								],
								expand=True,
								alignment=ft.MainAxisAlignment.CENTER, # 左右
								vertical_alignment=ft.CrossAxisAlignment.CENTER # 上下
							),
							expand=1,
							padding=ft.padding.only(0, 10, 0, 10)
						),
						self.preview_image
					],
					wrap=False,
					expand=True,
					alignment=ft.MainAxisAlignment.SPACE_EVENLY, # 左右
					vertical_alignment=ft.CrossAxisAlignment.STRETCH # 上下
				),
				expand=True,
				padding=ft.padding.only(80, 20, 80, 20 + 56)
			)
		]

		super().__init__("/image/download/" + image_name, controls=controls)

	async def follow_twitter(self, e):
		await asyncio.sleep(3)
		self.download_button.disabled = False
		await self.update_async()

	async def accept(self, e):
		#await self.page.go_async("/")
		pass

	async def on_resize(self, e: ft.ControlEvent):
		_size = e.data.split(","); width = float(_size[0]); height = float(_size[1])
		# 幅が800未満になったら画像を非表示にする
		await self.adapt_image(width)

	async def adapt_image(self, width):
		self.preview_image.visible = width >= 800
		if width >= 800:
			self.button_ctrls.alignment=ft.MainAxisAlignment.START
		else:
			self.button_ctrls.alignment=ft.MainAxisAlignment.START
		await self.update_async()


async def main(page: ft.Page):
	page.title = App.name
	page.padding = 20

	# 全体のフォント
	page.fonts = {
		"Noto Sans Japanese": "/fonts/NotoSansJP-Regular.ttf"
	}
	page.theme = ft.Theme(font_family="Noto Sans Japanese")

	# 変数
	previous_route = "/"
	pop_flag = False
	init_load = False

	print("Version: " + App.version)
	print("Commit: " + App.commit_sha)


	# 読み込み表示
	page.splash = loading_ctrl()
	await page.update_async()

	# メインビュー
	main_ctrl = RRIGApp()

	# メインビューを追加
	page.views.clear()
	page.views.append(main_ctrl)

	await page.update_async()

	# アプリバー
	appbar = ft.AppBar(
		title=ft.Text(App.name, size=16),
		center_title=False,
		actions=[
			# バージョン表記テキスト
			ft.Container(
				ft.Text(f"Version {App.version}-{App.branch}.{App.commit_sha}", size=12, text_align=ft.TextAlign.RIGHT),
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

	#page.controls.append(appbar)

	# サイズ変更時イベント
	async def on_resize(e: ft.ControlEvent):
		# ページに存在するビューをループして on_resize() が実装されていれば実行する
		for view in page.views:
			if hasattr(view, "on_resize"): await view.on_resize(e)

	##### ページルーティング #####
	# ルート変更イベント
	async def route_change(e: ft.RouteChangeEvent):
		nonlocal previous_route
		nonlocal pop_flag
		nonlocal init_load

		troute = ft.TemplateRoute(e.route)

		print("Route: \"" + page.route + "\"")

		# ルートが / の場合はメインビュー以外のビューを削除する
		if page.route == "/":
			# ページが2以上の場合はメインビュー以外を消す
			if len(page.views) >= 2: 
				print("- Clear views")
				del page.views[1:len(page.views)]
			print(page.views)
			pop_flag = False
			page.route = "/"
			page.title = App.name
			await page.update_async()
			# 画像の初回読み込みが行われていない場合は読み込みを実行する
			if not init_load: await load_image(); init_load = True
		else:
			pop_flag = False
			if pop_flag:
				pop_flag = False
			else:
				# ダウンロードプレビュー
				if troute.match("/image/preview/:name"):
					if troute.name in Images.data:
						if previous_route.startswith("/image/download/"): page.views.pop()
						view = DLPreviewView(troute.name)
						# ビューを生成
						page.views.append(
							view
						)
						page.title = troute.name + " - " + App.name

				# ダウンロード
				elif troute.match("/image/download/:name"):
					# ダウンロード確認ビューを経由せずにアクセスした場合はメインビューへ飛ばす
					if previous_route.startswith("/image/preview/"):
						if troute.name in Images.data:
							# ダウンロード確認ビューを削除
							page.views.pop()
							# ビューを生成
							view = DLAcceptView(troute.name)
							page.views.append(
								view
							)
							await page.update_async()
							page.title = troute.name + " - " + App.name
							# 画面のサイズに合わせて画像の表示の初期値を切り替え
							await view.adapt_image(page.width)
							print("Width: " + str(page.width))
					else:
						await page.go_async("/")

				await page.update_async()
				print(page.views)
		# 次のルート変更時に以前のルートを取得するための変数
		previous_route = e.route

	# ルートポップイベント
	async def ex_view_pop():
		nonlocal pop_flag

		pop_flag = True
		page.views.pop()
		#if len(page.views) < 1: top_view = page.views[0]
		#else: top_view = page.views[-1]
		if len(page.views) > 1: top_route = page.views[-1].route
		else: top_route = "/"
		#print("Views: " + str(page.views))
		print("Route (Pop): \"" + str(top_route) + "\"")
		await page.go_async(top_route)

	async def view_pop(view: ft.ViewPopEvent):
		await ex_view_pop()
		return
		if len(page.views) > 1:
			print("- Back")
			await page.go_async(top_view.route)
			#await page.update_async()
		else:
			print("- Root")
			await page.go_async("/")
		page.appbar = appbar
		page.appbar.visible = True
		await page.update_async()

	async def load_image():
		page.splash = loading_ctrl()
		await page.update_async()
		await main_ctrl.load_legends()
		await main_ctrl.load_skins()
		await main_ctrl.load_tags()
		await main_ctrl.load_images()
		page.splash = None
		await page.update_async()

	# ページルーティングのイベント定義
	page.on_route_change = route_change
	page.on_view_pop = view_pop

	# サイズ変更時のイベント定義
	page.on_resize = on_resize

	# 画像一覧を読み込み (APIから取得)
	await Images.load()

	# ページを移動する URLを直接入力してアクセスすると入力したパスのページが表示される
	await page.go_async(page.route, False)

	page.splash = None

	await page.update_async()


ft.app(target=main, assets_dir="assets", port=8000, view=ft.AppView.FLET_APP, web_renderer=ft.WebRenderer.HTML)
