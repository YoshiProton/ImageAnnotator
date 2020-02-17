import tkinter as tk
import cv2
from PIL import Image, ImageTk
import os
import glob
import tkinter.filedialog as dlg
import tkinter.messagebox as msgbx

class ImageData():
    """
    読み込んだ画像のファイルパス、編集有無を保持する。

    Attributes:
    -------

    """
    def __init__(self, path):
        self.file_path = path
        self.base_name = None
        self.isEditted = False

        self.set_basename()

    def set_basename(self):
        if self.file_path is not None:
            self.base_name = os.path.basename(self.file_path)


class MainFrame(tk.Tk):
    """
    アプリケーションのメイン画面
    """
    def __init__(self):
        super(MainFrame, self).__init__()

        # 指定したディレクトリと画像リスト
        self.dir = None
        self.anno_dir = None
        self.data_list = []
        self.num_img_file = 0
        # 左右クリック中の状態
        self.isLeftDown = False
        self.isRightDown = False
        # キャンバス上描画可能
        self.isDrawable = False
        # 画像をグローバル？に保持しておかないと、open/create_imageしてもメモリ解放されてしまい表示できない。
        # [Todo] ファイル管理は別にまとめたほうがよさそう？
        self.ref_id = None
        self.ref_image_org = None
        self.ref_image_edit = None
        self.ref_image_display = None
        self.ann_id = None
        self.ann_image_org = None
        self.ann_image_edit = None
        self.ann_image_display = None
        # ブラシ関連
        self.brush_size = 2
        self.colorlist = {'Red' : (255, 0, 0), 
                        'Green' : (0, 255, 0), 
                        'Blue' : (0, 0, 255), 
                        'Cyan' : (0, 255, 255), 
                        'Magenta' : (255, 0, 255),
                        'Yellow' : (255, 255, 0)}
        self.COLORS = {'FG': (255), 'BG': (0), 'HIGHLIGHT': self.colorlist['Red']} #default color: Red

        # フレーム関係
        self.title("Image Annotator")
        #self.iconbitmap('xxx.ico')
        #self.geometry()
        self.resizable()
        # UI生成
        self.set_widgets()

        # 参考用
        #tkinter.messagebox.showinfo('○×プログラム','処理ファイルを選択してください！')
        # ファイル選択ダイアログ
        #fTyp = [("","*.csv")]
        #iDir = os.path.abspath(os.path.dirname(__file__))
        #tkinter.messagebox.showinfo('○×プログラム','処理ファイルを選択してください！')
        #file = tkinter.filedialog.askopenfilename(filetypes = fTyp,initialdir = iDir)


    def set_widgets(self):
        """
        UIの生成
        """
        ### ファイル読み込み部
        self.lf_dir = tk.LabelFrame(self, text='Directory')
        self.lf_dir.pack(anchor=tk.W, padx=10, pady=2)
        # 一行入力ボックス
        self.entry_dir = tk.Entry(self.lf_dir, width=100)
        self.entry_dir.pack(side=tk.LEFT, padx=10)
        # self.entry_anno_dir = tk.Entry(sel.lf_dir, width=100) # アノテーションフォルダの指定
        # ボタン
        self.open_btn_dir = tk.Button(self.lf_dir, text='Open Folder...', command=self.open_img_directory)
        self.open_btn_dir.pack(side=tk.LEFT, pady=5, padx=10)
        self.read_btn_dir = tk.Button(self.lf_dir, text='Read Images', command=self.read_images)
        self.read_btn_dir.pack(side=tk.LEFT, pady=5, padx=2)
        
        ### 画像表示部
        self.f_canvas = tk.Frame(self)
        self.f_canvas.pack(padx=10, pady=2)
        self.label_text = tk.StringVar()
        self.label_text.set("")
        self.label_ref_img = tk.Label(self.f_canvas, textvariable=self.label_text)
        self.label_ref_img.pack()
        # 参照画像
        self.f_canvas_ref = tk.Frame(self.f_canvas)
        self.f_canvas_ref.pack(side=tk.LEFT)
        self.canvas_ref = tk.Canvas(self.f_canvas_ref, bg = "black", width=400, height=300)
        self.canvas_ref.pack(pady=2, padx=10)
        self.canvas_ref.bind("<ButtonPress-1>", self.on_left_clicked)
        self.canvas_ref.bind("<ButtonRelease-1>", self.on_left_released)
        self.canvas_ref.bind("<ButtonPress-3>", self.on_right_clicked)
        self.canvas_ref.bind("<ButtonRelease-3>", self.on_right_released)
        self.canvas_ref.bind("<Button1-Motion>", self.on_mouse_move)    # left/right共通化できる？？分ける？
        self.canvas_ref.bind("<Button3-Motion>", self.on_mouse_move)
        #self.canvas_ref.bind("Whirl expand/shrink", None) # ホイールによる拡大・縮小。補間されてしまう？
        # アノテーション結果画像
        self.f_canvas_ann = tk.Frame(self.f_canvas)
        self.f_canvas_ann.pack(side=tk.LEFT)
        self.canvas_ann = tk.Canvas(self.f_canvas_ann, bg = "black", width=400, height=300)
        self.canvas_ann.pack(pady=2, padx=10)
        # 描画ポイントのサイズ選択リストボックス
        self.lf_listbox = tk.LabelFrame(self.f_canvas, text='BrushSize')
        self.lf_listbox.pack()
        brushsize = ("1", "2", "3", "4", "5")
        brushlistvar = tk.StringVar(value=brushsize)
        self.listbox = tk.Listbox(self.lf_listbox, listvariable=brushlistvar, width=10, height=len(brushsize))
        self.listbox.configure(selectmode="single")
        self.listbox.pack()
        self.listbox.bind('<<ListboxSelect>>', self.listbox_selected)
        #
        self.lf_colorlistbox = tk.LabelFrame(self.f_canvas, text='Color')
        self.lf_colorlistbox.pack()
        colorlistvar = tk.StringVar(value=tuple(self.colorlist.keys()))
        self.colorlistbox =tk.Listbox(self.lf_colorlistbox, listvariable=colorlistvar, width=10, height=len(self.colorlist))
        self.colorlistbox.configure(selectmode="single")
        self.colorlistbox.pack()
        self.colorlistbox.bind('<<ListboxSelect>>', self.colorlistbox_selected)
        #
        self.switch_btn_text = tk.StringVar()
        self.switch_btn_text.set("To Org")
        self.switch_btn = tk.Button(self.f_canvas, textvariable=self.switch_btn_text, width=10, command=self.on_switch_btn_pressed)
        self.switch_btn.pack()

        # 次・前ボタン
        self.fr_btn = tk.Frame(self)
        self.fr_btn.pack(anchor=tk.S, padx=10, pady=2)
        self.prev_btn = tk.Button(self.fr_btn, text='←Previous', command=self.on_previous_btn_pressed)
        self.prev_btn.pack(side=tk.LEFT, padx=2)
        self.entry_pagejump = tk.Entry(self.fr_btn, width=5)
        self.entry_pagejump.pack(side=tk.LEFT, padx=5)
        self.jump_btn = tk.Button(self.fr_btn, text='Jump', command=self.on_jump_btn_pressed)
        self.jump_btn.pack(side=tk.LEFT, padx=2)
        self.next_btn = tk.Button(self.fr_btn, text='Next→', command=self.on_next_btn_pressed)
        self.next_btn.pack(side=tk.RIGHT, padx=5)


    def open_img_directory(self):
        """
        フォルダ選択ダイアログの起動
        """
        self.dir = dlg.askdirectory()
        if self.dir:
            self.entry_dir.delete(0, tk.END)
            self.entry_dir.insert(0, self.dir)


    def read_images(self):
        """
        指定されたフォルダの画像一覧を読み込み、最初の画像を表示する。
        アノテーションデータ保存用フォルダの作成も行う。
        """
        if self.dir:
            # annnotationデータ格納用ディレクトリ作成
            self.anno_dir = os.path.join(self.dir, "anno")
            if not os.path.exists(self.anno_dir):
                try:
                    os.mkdir(self.anno_dir)
                    tk.messagebox.showinfo('フォルダの作成', '以下のフォルダを作成しました。\n'+self.anno_dir)
                except:
                    pass

            # 画像読み込み
            dir = self.dir
            #self.data_list = os.listdir(dir)
            dir = os.path.join(dir, "*.jpg") # [ToDo] Suports to other file extensions
            #self.data_list = sorted(glob.glob(dir))
            file_list = sorted(glob.glob(dir))
            
            self.num_img_file = len(file_list)
            print("Number of images in {}: {}".format(self.dir, str(self.num_img_file)))


            # read first image
            if self.num_img_file > 0:
                for i in range(self.num_img_file):
                    self.data_list.append(ImageData(file_list[i]))

                self.ref_id = 0
                self.load_image()
                self.isDrawable = True


    def on_left_clicked(self, event):
        """
        左クリック押下時のイベントハンドラ。
        クリック地点に色を塗る。

        parameters
        ------
        event: event
            クリック座標などを持つイベントオブジェクト
        """
        self.isLeftDown = True 
        if self.ref_image_edit == None: return 
        if not self.isDrawable: return
        
        self.data_list[self.ref_id].isEditted = True
        self.draw_point(event.x, event.y)


    def on_left_released(self, event):
        """
        左クリックリリース時のイベントハンドラ

        parameters
        ------
        event: event
            マウス離脱時の座標などを持つイベントオブジェクト
        """
        self.isLeftDown = False


    def on_right_clicked(self, event):
        """
        右クリック押下時のイベントハンドラ。
        クリック地点の色を消す（画像オリジナルの色に戻す）

        parameters
        ------
        event: event
            クリック座標などを持つイベントオブジェクト
        """
        self.isRightDown = True
        if self.ref_image_edit == None: return
        if not self.isDrawable: return
        
        self.data_list[self.ref_id].isEditted = True
        self.erase_point(event.x, event.y)


    def on_right_released(self, event):
        """
        右クリックリリース時のイベントハンドラ

        parameters
        ------
        event: event
            マウス離脱時の座標などを持つイベントオブジェクト
        """
        self.isRightDown = False


    def on_mouse_move(self, event):
        """
        左右クリック押下状態でマウス移動時のイベントハンドラ

        parameters
        ------
        event: event
            マウス離脱時の座標などを持つイベントオブジェクト
        """
        px = event.x
        py = event.y

        # まだ画像を読み込んでいない時の対応
        if ((self.ref_image_edit is None) or (self.ref_image_org is None)): return

        # 画面外存在時の対応
        if not self.is_within_image_size(px, py, self.ref_image_org.width, self.ref_image_org.height): return 

        # アノテーション・オリジナル切り替え時対応
        if not self.isDrawable: return

        # 左右クリックによって描画・消去処理
        if self.isLeftDown:
            self.draw_point(px,py)
        elif self.isRightDown:
            self.erase_point(px,py)


    def is_within_image_size(self, px, py, width, height):
        """
        座標の範囲内外判定

        parameters
        ------
        px : Int
            x座標
        py : Int
            y座標
        width : Int
            画像の幅
        height : Int
            画像の高さ

        Returns
        ------
        True/False :True/False
            範囲内ならTrue, 範囲外ならFalse 
        """
        if px < 0: return False
        if py < 0: return False
        if px >= width: return False
        if py >= height: return False

        return True 


    def draw_point(self, x, y):
        """
        指定された座標を中心にbrush_sizeのピクセルに色を塗り、表示する

        parameters
        ------
        x : Int
            描画するx座標
        y : Int
            描画するy座標
        """   
        # draw clicked point on ref_display and annotation image
        extent = self.brush_size / 2
        for tx in range(self.brush_size):
            for ty in range(self.brush_size):
                if not self.is_within_image_size(x + tx, y + ty, self.ref_image_edit.width, self.ref_image_edit.height): continue

                self.ref_image_edit.putpixel((x + tx, y + ty), self.COLORS['HIGHLIGHT'])
                self.ann_image_edit.putpixel((x + tx ,y + ty), self.COLORS['FG'])
        # show result
        self.show_images()


    def erase_point(self, x, y):
        """
        指定された座標を中心にbrush_sizeのピクセルにオリジナル画像の色を塗り、消去したように見せて表示する

        parameters
        ------
        x : Int
            描画するx座標
        y : Int
            描画するy座標
        """
        extent = self.brush_size / 2
        for tx in range(self.brush_size):
            for ty in range(self.brush_size):
                if not self.is_within_image_size(x+tx, y + ty, self.ref_image_edit.width, self.ref_image_edit.height): continue
            
                # [todo]erase colored pixcels and recover original color on it
                org_color = self.ref_image_org.getpixel((x + tx, y + ty))
                self.ref_image_edit.putpixel((x + tx, y + ty), org_color)
                self.ann_image_edit.putpixel((x + tx, y + ty), self.COLORS['BG'])
        # Show result
        self.show_images()


    def listbox_selected(self, event):
        """
        リストボックスからbrush_sizeを選択されたときのイベント

        parameters
        ------
        event : event
            状態はlistbox自体が持つため、その値を利用
        """
        for i in self.listbox.curselection():
            self.brush_size = int(self.listbox.get(i))


    def colorlistbox_selected(self, event):
        """
        カラーリストボックスから、HIGHLIGHTカラーを選択設定するイベント

        parameters
        ------
        event: event
            状態はlistbox自体が持つため、その値を利用
        """
        for i in self.colorlistbox.curselection():
            selectedcolor = self.colorlistbox.get(i)
            self.COLORS['HIGHLIGHT'] = self.colorlist[selectedcolor]

        ### 画像の更新
        # 現在の状態の保存
        # 画像の再読み込みと表示
        if self.ref_id == None: return
        if self.data_list[self.ref_id].isEditted:
            self.ann_image_edit.save(self.get_annotation_filepath())
            self.data_list[self.ref_id].isEditted = False
        self.load_image()


    def on_next_btn_pressed(self):
        """
        次ボタン（次の画像読み込み）押下時のイベント
        現在画像が編集済みなら保存して、idをカウントアップして次の画像を表示
        """
        if self.ref_id == None: return

        # [Todo] save current images
        if self.data_list[self.ref_id].isEditted:
            self.ann_image_edit.save(self.get_annotation_filepath())
            self.data_list[self.ref_id].isEditted = False

        self.ref_id += 1
        if self.ref_id >= self.num_img_file:
            self.ref_id = 0

        # [todo] テキストボックスの値の更新

        self.load_image()


    def on_previous_btn_pressed(self):
        """
        戻ボタン（前の画像読み込み）押下時のイベント
        現在画像が編集済みなら保存して、idをカウントダウンして前の画像を表示
        """
        if self.ref_id == None: return

        # [Todo] save current images
        if self.data_list[self.ref_id].isEditted:
            self.ann_image_edit.save(self.get_annotation_filepath())
            self.data_list[self.ref_id].isEditted = False

        self.ref_id -= 1
        if self.ref_id < 0:
            self.ref_id = self.num_img_file - 1

        # [todo] テキストボックスの値の更新

        self.load_image()


    def on_jump_btn_pressed(self):
        """
        画像ＩＤ指定ボタンを押下時のイベント
        """
        # フォルダ指定してないなら無視
        if self.ref_id is None: return

        # ID取得
        id_str = self.entry_pagejump.get()

        # 値チェック
        if (id_str is None) or (id_str is "") : return
        id = int(id_str) -1 # indexの調整
        if id < 0:
            id = self.num_img_file - abs(id) 
        if id >= self.num_img_file:
            id = self.num_img_file - 1 # オーバーしているときは最後のindex

        self.ref_id = id
        self.load_image()

        self.entry_pagejump.delete(0, tk.END)


    def on_switch_btn_pressed(self):
        if self.isDrawable: # アノテーション画像が表示されている状態
            self.isDrawable = False
            # オリジナル画像の表示
            self.switch_btn_text.set("To Ann")
            self.show_org_image()

        else: # オリジナル画像が表示されている状態
            self.isDrawable = True
            # アノテーション画像の表示
            self.switch_btn_text.set("To Org")
            self.show_images()

    def load_image(self):
        """
        現在idの参照・アノテーション画像をキャンバスに表示する。
        アノテーション画像が無い場合は、新規に作成して保存。
        """
        if self.ref_id == None: return

        #表示用ラベルテキストの作成
        ref_filepath = self.get_reference_filepath()
        ann_filepath = self.get_annotation_filepath()
        self.label_text.set(os.path.basename(ref_filepath) + " ({}/{})".format(self.ref_id+1, self.num_img_file))

        #参照用画像の読み込み
        self.ref_image_org = Image.open(ref_filepath)
        self.ref_image_edit = self.ref_image_org.copy()

        # アノテーション用画像の読み込みまたは新規表示
        # 既に画像があれば、読み込んで表示。なければ新規作成
        if (os.path.exists(ann_filepath)):
            self.ann_image_org = Image.open(ann_filepath)
        else: # new open
            self.ann_image_org = Image.new("L", self.ref_image_org.size, self.COLORS['BG'])
            self.ann_image_org.save(ann_filepath) # 一旦保存
            #self.ann_image = Image.new("RGB", self.ref_image.size, (128,128,128))
        self.ann_image_edit = self.ann_image_org.copy()

        # maskによる合成
        highlight_img = Image.new("RGB", self.ref_image_org.size, self.COLORS['HIGHLIGHT'])
        self.ref_image_edit.paste(highlight_img, (0,0), self.ann_image_edit)
        self.show_images()

        # 読み込んだ画像に合わせて、canvasのサイズ変更
        self.canvas_ref.config(height=self.ref_image_org.height, width=self.ref_image_org.width)
        self.canvas_ann.config(height=self.ref_image_org.height, width=self.ref_image_org.width)


    def show_images(self):
        """
        参照画像、アノテーション画像をImageTkに変換して表示する
        """
        self.ref_image_display = ImageTk.PhotoImage(self.ref_image_edit)
        self.canvas_ref.create_image(0,0,anchor="nw",image=self.ref_image_display)

        self.ann_image_display = ImageTk.PhotoImage(self.ann_image_edit)
        self.canvas_ann.create_image(0,0,anchor="nw", image=self.ann_image_display)


    def show_org_image(self):
        """
        オリジナル画像をImageTkに変換して表示する。
        """
        self.ref_image_display = ImageTk.PhotoImage(self.ref_image_org)
        self.canvas_ref.create_image(0,0,anchor="nw",image=self.ref_image_display)


    def get_annotation_filepath(self):
        """
        現在idから、アノテーション画像ファイルのパスを返す。

        Returns
        --------
        filepath : String
            ファイルパス
        """
        ref_filename = self.data_list[self.ref_id].base_name
        return os.path.join(self.anno_dir, ref_filename)


    def get_reference_filepath(self):
        """
        現在idから、参照画像ファイルのパスを返す。

        Returns
        -------
        filepath : String
            ファイルパス
        """
        return self.data_list[self.ref_id].file_path


    def run(self):
        """
        アプリケーションの実行
        """
        self.mainloop()

        