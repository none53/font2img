import os
import glob
import argparse
import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

CAPS = [chr(i) for i in range(65, 65 + 26)]

def pil2num(pil_img):
    num_img = np.asarray(pil_img)
    num_img.flags.writeable = True
    return num_img

def num2pil(num_img):
    pil_img = Image.fromarray(np.uint8(num_img))
    return pil_img

def convert_binary_img(pil_img, threshold=128):
    num_img = pil2num(pil_img)
    for row_i in range(len(num_img)):
        for col_i in range(len(num_img[0])):
            if num_img[row_i][col_i] < threshold:
                num_img[row_i][col_i] = 0
            else:
                num_img[row_i][col_i] = 255
    binary_pil_img = num2pil(num_img)
    return binary_pil_img

def get_offset(pil_img, normal_canvas_size):
    num_img = pil2num(pil_img)
    canvas_size = len(num_img)
    canvas_offset = canvas_size - normal_canvas_size
    margins = {}
    # top
    for i in range(canvas_size):
        for j in range(canvas_size):
            if num_img[i][j] != 255:
                margins['top'] = i
                break
        if 'top' in margins:
            break
    # bottom
    for i in range(canvas_size):
        for j in range(canvas_size):
            if num_img[canvas_size - i - 1][j] != 255:
                margins['bottom'] = i - canvas_offset
                break
        if 'bottom' in margins:
            break
    # left
    for j in range(canvas_size):
        for i in range(canvas_size):
            if num_img[i][j] != 255:
                margins['left'] = j
                break
        if 'left' in margins:
            break
    # right
    for j in range(canvas_size):
        for i in range(canvas_size):
            if num_img[i][canvas_size - j - 1] != 255:
                margins['right'] = j - canvas_offset
                break
        if 'right' in margins:
            break
    x_offset = int((margins['right'] - margins['left']) / 2)
    y_offset = int((margins['bottom'] - margins['top']) / 2)
    offsets = (x_offset, y_offset)

    is_tb_maximum = margins['top'] + margins['bottom'] <= 0
    is_lr_maximum = margins['right'] + margins['left'] <= 0
    is_maximum = is_tb_maximum or is_lr_maximum
    return offsets, is_maximum

def draw_char(char, font_path, canvas_size, char_size, offsets=(0, 0)):
    font = ImageFont.truetype(font_path, size=char_size)
    img = Image.new('L', (canvas_size, canvas_size), 255)
    draw = ImageDraw.Draw(img)
    draw.text(offsets, char, 0, font=font)
    img = convert_binary_img(img)
    return img

def draw_char_center(char, font_path, canvas_size, char_size):
    no_offset_img = draw_char(char, font_path, canvas_size + 20, char_size)
    offsets, is_maximum = get_offset(no_offset_img, canvas_size)
    center_img = draw_char(char, font_path, canvas_size, char_size, offsets)
    return center_img, is_maximum

def draw_char_maximum(char, font_path, canvas_size):
    char_size = canvas_size
    while True:
        img, is_maximum = draw_char_center(char, font_path, canvas_size, char_size)
        print (char_size)
        if is_maximum:
            break
        char_size += 1
    return img

def get_filepaths(dirpath, findname):
    '''
    パスのディレクトリ内のファイルのパスを取得
    findnameでワイルドカード検索可能
    'foo/bar/', '*.png' => 'foo/bar/'内のpng画像のパスのリストを返す
    '''
    dirpath = os.path.normpath(dirpath)
    filepaths = glob.glob(dirpath + '/' + findname)
    return filepaths

def font2img(src_font_path, dst_dir_path, canvas_size, font_size, is_center=True, is_maximum=False):
    font_paths = get_filepaths(src_font_path, '*.ttf')
    for font_path in font_paths:
        for c in CAPS:
            img, maximum = draw_char_center(c, font_path, canvas_size, font_size)
            if img:
                img.save(os.path.join(dst_dir_path, c + ".png"))
                print ("proccessed: " + c)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='convert ttf/otf into png/jpg/etc')
    parser.add_argument('src_dir_path', action='store', type=str, help='Directory path where source files are located.')
    parser.add_argument('dst_dir_path', action='store', type=str, help='Directory path of destination.')
    parser.add_argument('canvas_size', action='store', type=int, help='Canvas size')
    parser.add_argument('--not-centering', dest='is_center', action='store_true', help='Centering or not')
    parser.add_argument('-m', '--maximum', dest='is_maximum', action='store_true', help='Maximum or not')
    parser.add_argument('-f', '--font-size', dest='font_size', action='store', type=int, help='Font point size')
    args = parser.parse_args()
    if args.font_size == None:
        font_size = args.canvas_size
    else:
        font_size = args.font_size
    font2img(args.src_dir_path, args.dst_dir_path, args.canvas_size, font_size)
