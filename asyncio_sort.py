import datetime
import os
import sys
from asyncio import gather
import asyncio
from aiopath import AsyncPath
import aioshutil


CATEGORIES = {'images': ('JPEG', 'PNG', 'JPG', 'SVG'), 'documents': ('DOC', 'DOCX', 'TXT', 'PDF', 'XLSX', 'PPTX'),
              'audio': ('MP3', 'OGG', 'WAV', 'AMR'), 'video': ('AVI', 'MP4', 'MOV', 'MKV'), 'archives': ('ZIP', 'GZ', 'TAR')}

file_log = []


async def main(base_path):
    files_list = await sort_files(base_path)
    for file_path_list in files_list:
        moves = (move_files(file_path) for file_path in file_path_list)
        await gather(*moves)
    await remove_folders(base_path)
    await log()


async def rename_exists_files(name):
    return name + '_edit_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')


async def log():
    final_dict = {}
    for i in file_log:
        for k, v in i.items():
            final_dict.setdefault(k, []).append(v)
    for k, v in final_dict.items():
        print(f'---{k}---')
        print(', '.join(v))
    print(f"Sorting in the {base_path} catalog has been completed successfully.")


async def ignore_list():
    ignore = []
    for k in CATEGORIES.keys():
        ignore.append(k)
    return ignore


async def remove_folders(path):
    folders = list(os.walk(path))
    for path, _, _ in folders[::-1]:
        if len(os.listdir(path)) == 0:
            os.rmdir(path)


async def move_files(file_path):
    dirname, fname = os.path.split(file_path)
    extension = os.path.splitext(fname)[1].upper().replace('.', '')
    for k, v in CATEGORIES.items():
        if extension in v:
            os.makedirs(base_path + '/' + k, exist_ok=True)
            apath = AsyncPath(os.path.join(base_path + '/' + k, fname))
            if await apath.exists():
                new_f_renamed = await rename_exists_files(os.path.splitext(fname)[0]) + os.path.splitext(fname)[1]
                await aioshutil.move(os.path.join(file_path), os.path.join(base_path + '/' + k, new_f_renamed))
                file_log.append({k: new_f_renamed})
            else:
                await aioshutil.move(os.path.join(file_path), os.path.join(base_path + '/' + k, fname))
                file_log.append({k: fname})


async def sort_files(path):
    subfolders = []
    files = []
    ignore = await ignore_list()
    for i in os.scandir(path):
        if i.is_dir():
            if i.name not in ignore:
                old_path = os.path.dirname(i.path)
                os.rename(os.path.join(old_path, i.name), os.path.join(old_path, i.name))
                subfolders.append(os.path.join(old_path, i.name))
        if i.is_file():
            old_path = os.path.dirname(i.path)
            os.rename(os.path.join(old_path, i.name), os.path.join(old_path, i.name))
            files.append(os.path.join(old_path, i.name))
    for dir in list(subfolders):
        sf, i = await sort_files(dir)
        subfolders.extend(sf)
        files.extend(i)

    return subfolders, files


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Takes only one argument!')
    else:
        if os.path.exists(sys.argv[1]):
            base_path = sys.argv[1]
            asyncio.run(main(base_path))
        else:
            print('Wrong path!')