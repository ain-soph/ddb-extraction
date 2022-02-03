#!/usr/bin/env python3

import argparse
import os
import zipfile
import yaml

from typing import Sequence


def parse_args(args: Sequence[str] = None) -> str:
    # initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--work_dir', required=True,
                        help='working directory containing '
                        '"ddi.yml" and "wav.zip".')

    # parse args
    args_result = parser.parse_args(args)
    work_dir: str = os.path.normpath(args_result.work_dir)
    return work_dir


def main():
    work_dir = parse_args()
    ddi_yml_path = os.path.join(work_dir, 'ddi.yml')
    wav_zip_path = os.path.join(work_dir, 'wav.zip')
    with open(ddi_yml_path, 'r') as yml_f:
        ddi = yaml.load(yml_f, Loader=yaml.FullLoader)
        ddi: dict[str, dict[str, list[dict[str, str | list[str]]]]]
    wav = zipfile.ZipFile(wav_zip_path, mode='r')
    wav_renamed = zipfile.ZipFile(os.path.join(work_dir, 'wav_renamed.zip'),
                                  'w', compression=zipfile.ZIP_STORED)
    counter = 1
    for part, part_dict in ddi.items():
        for name, name_list in part_dict.items():
            for i, name_dict in enumerate(name_list):
                name = name.replace('\\', '%5c')
                print(f'{counter:5d}  {part}/{name}_{i}')
                fname: str = name_dict['snd']
                wav_renamed.writestr(f'{part}/{name}_{i}.wav',
                                     wav.read(f'wav/{fname}.wav'))
                counter += 1

    wav_renamed.close()
    wav.close()


if __name__ == '__main__':
    main()
