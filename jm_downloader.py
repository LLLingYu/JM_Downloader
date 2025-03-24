from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, Message
from nonebot.params import CommandArg
import img2pdf
import os
import shutil
from jmcomic import JmOption
from jmcomic import *
import jmcomic, os, time, yaml
from PIL import Image

#配置说明
#使用前请修改配置文件路径
#配置文件的base_dir路径为图片下载和缓存的路径，可以随意修改

#定义配置文件路径
option = jmcomic.create_option_by_file('D:\somefiles\Bot\JMBot\JmBot\jmbot\plugins\config.json')
config = "D:\somefiles\Bot\JMBot\JmBot\jmbot\plugins\config.json"

# 定义命令处理器，命令为 "jm"或"jm下载"或"JM"
download = on_command("jm", aliases={"jm下载","JM"}, priority=5)

#图片转换PDF
def all2PDF(input_folder, pdfpath, pdfname):
    start_time = time.time()
    paht = input_folder
    zimulu = []  # 子目录（里面为image）
    image = []  # 子目录图集
    sources = []  # pdf格式的图

    with os.scandir(paht) as entries:
        for entry in entries:
            if entry.is_dir():
                zimulu.append(int(entry.name))
    # 对数字进行排序
    zimulu.sort()

    for i in zimulu:
        with os.scandir(paht + "/" + str(i)) as entries:
            for entry in entries:
                if entry.is_dir():
                    print("这一级不应该有自录")
                if entry.is_file():
                    image.append(paht + "/" + str(i) + "/" + entry.name)

    if "jpg" in image[0]:
        output = Image.open(image[0])
        image.pop(0)

    for file in image:
        if "jpg" in file:
            img_file = Image.open(file)
            if img_file.mode == "RGB":
                img_file = img_file.convert("RGB")
            sources.append(img_file)

    pdf_file_path = pdfpath + "/" + pdfname
    if pdf_file_path.endswith(".pdf") == False:
        pdf_file_path = pdf_file_path + ".pdf"
    output.save(pdf_file_path, "pdf", save_all=True, append_images=sources)
    end_time = time.time()
    run_time = end_time - start_time
    print("运行时间：%3.2f 秒" % run_time)

#下载事件处理
@download.handle()
async def handle_first_receive(bot: Bot, event: Event, args: Message = CommandArg()):
    jm_code = args.extract_plain_text().strip()
    if not jm_code.isdigit():
        await download.finish("请提供要下载的 JM 号。")
  
    # 下载漫画
    try:
        await download.send(f"开始下载 JM 号 {jm_code} 的漫画，请稍候...")
        manhua = {jm_code}
        for id in manhua:
            jmcomic.download_album(id,option)

        with open(config, "r", encoding="utf8") as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            path = data["dir_rule"]["base_dir"]

        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_dir():
                    if os.path.exists(os.path.join(path +'/' +entry.name + ".pdf")):
                        print("文件：《%s》 已存在，跳过" % entry.name)
                        continue
                    else:
                        print("开始转换：%s " % entry.name)
                        all2PDF(path + "/" + entry.name, path, entry.name)
    except Exception as e:
        await download.finish(f"下载失败：{e}")

    # 发送 PDF 文件到群聊
    pdf_file_path = path + "/" + entry.name + ".pdf" 
    album_dir = path + "/" + entry.name
    try:
        await bot.call_api("upload_group_file",
                           group_id=event.group_id,
                           file=pdf_file_path,
                           name=os.path.basename(pdf_file_path))
    except Exception as e:
        await download.send(f"文件发送失败：{e}")
    finally:
        # 清理下载的文件和生成的 PDF
        if os.path.exists(pdf_file_path):
            os.remove(pdf_file_path)
        if os.path.exists(album_dir):
            shutil.rmtree(album_dir)
