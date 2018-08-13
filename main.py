# coding:utf-8
from urllib import request
import os, time, shutil
import json
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3
import re


CACHE_FOLDER = r'C:\Users\xxx\AppData\Local\Netease\CloudMusic\Cache\Cache\\'
OUTPUT_FOLDER = r'E:\Netease\\'
MAX_RETRY = 5
INFO_API = r'https://api.imjad.cn/cloudmusic/?type=detail&id='


def decrypt(myinputfile, myoutputfile):
    if not os.path.exists(myinputfile):
        exit(100)
    if os.path.exists(myoutputfile):
        os.remove(myoutputfile)
    with open(myinputfile, 'rb') as f:
        bt_array = bytearray(f.read())
    with open(myoutputfile, 'wb') as out:
        for i, j in enumerate(bt_array):
            bt_array[i] = j ^ 0xa3
        out.write(bytes(bt_array))


def get_tags(myinputfile):
    if not os.path.exists(myinputfile):
        exit(100)
    tag_info = {}
    (filepath, filename) = os.path.split(myinputfile)
    arr = filename.split('-')
    mp3_id = arr[0]
    info_url = INFO_API + mp3_id
    retry_num = 0
    while retry_num < MAX_RETRY:
        try:
            page = request.Request(info_url)
            page_html = request.urlopen(page).read().decode('utf-8')
            myjsondata = json.loads(page_html)
            song_name = myjsondata['songs'][0]['name']
            tag_info['song_name'] = song_name
            artist_name = myjsondata['songs'][0]['ar'][0]['name']
            tag_info['artist_name'] = artist_name
            album_name = myjsondata['songs'][0]['al']['name']
            tag_info['album_name'] = album_name
            pic_url = myjsondata['songs'][0]['al']['picUrl']
            tag_info['album_pic'] = download_pic(pic_url)
            song_no = myjsondata['songs'][0]['no']
            tag_info['song_no'] = str(song_no).zfill(2)
            timeStamp = str(myjsondata['songs'][0]['publishTime'])[:-3]
            timeArray = time.localtime(abs(int(timeStamp)))
            album_year = time.strftime("%Y", timeArray)
            tag_info['album_year'] = album_year
            return tag_info
        except Exception as e:
            print(e)
            retry_num = retry_num + 1
        else:
            break
    exit(500)


def download_pic(myurl):
    filename = myurl.split('/')[-1]
    download_file = CACHE_FOLDER+filename
    if os.path.exists(download_file):
        os.remove(download_file)
    pic_resource = request.urlopen(myurl, timeout=5)
    with open(download_file, 'wb') as f:
        f.write(pic_resource.read())
    return download_file


def write_tags(myinputfile, mytags):
    if not os.path.exists(myinputfile):
        exit(100)
    if len(mytags) == 0:
        exit(200)
    audio = MP3(myinputfile, ID3=EasyID3)
    audio['title'] = mytags['song_name']
    audio['album'] = mytags['album_name']
    audio['albumartist'] = mytags['artist_name']
    audio['artist'] = mytags['artist_name']
    audio['date'] = mytags['album_year']
    audio['tracknumber'] = mytags['song_no']
    audio.save(v2_version=3)
    audio = MP3(myinputfile, ID3=ID3)
    audio.tags.add(
        APIC(
            encoding=3,
            mime='image/jpg',
            type=3,
            desc=u'Cover',
            data=open(mytags['album_pic'], 'rb').read()
        )
    )
    audio.save(v2_version=3)  # to display properties in the win
    os.remove(mytags['album_pic'])


def organize_file(myinputfile, mytags, myoutputfolder):
    if not os.path.exists(myinputfile):
        exit(100)
    if len(mytags) == 0:
        exit(200)
    if not os.path.exists(myoutputfolder):
        exit(300)
    artist_folder = myoutputfolder + re.sub('[\/:*?"<>|]', '', mytags['artist_name'])
    if not os.path.exists(artist_folder):
        os.mkdir(artist_folder)
    album_folder = artist_folder + '\\' + mytags['album_year'] + '_' + re.sub('[\/:*?"<>|]', '', mytags['album_name'])
    if not os.path.exists(album_folder):
        os.mkdir(album_folder)
    audio_file = album_folder + '\\' + mytags['song_no'] + '.' + re.sub('[\/:*?"<>|]', '', mytags['song_name']) + '.mp3'
    if os.path.exists(audio_file):
        print('--Skip ' + audio_file)
        os.remove(myinputfile)
        return
    print(audio_file)
    shutil.move(myinputfile, audio_file)


def main():
    print("----------------Started at " + time.asctime(time.localtime(time.time())) + " !----------------")
    if not os.path.exists(CACHE_FOLDER):
        exit(100)
    if not os.path.exists(OUTPUT_FOLDER):
        exit(200)
    for root, dirs, files in os.walk(CACHE_FOLDER):
        for name in files:
            filename = os.path.join(root, name)
            fileext = os.path.splitext(os.path.basename(filename))[1]
            if fileext == ".uc":
                org_file = filename
                tran_file = org_file + '.mp3'
                decrypt(org_file, tran_file)
                file_tags = get_tags(org_file)
                write_tags(tran_file, file_tags)
                organize_file(tran_file, file_tags, OUTPUT_FOLDER)
    print("----------------Finished at " + time.asctime(time.localtime(time.time())) + " !----------------")


if __name__ == '__main__':
    main()
