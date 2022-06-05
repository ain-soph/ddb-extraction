#!/usr/bin/env python3

from utils.ddi_utils import read_ddi
import argparse
import os


def parse_args(args: list[str] = None) -> tuple[str, str, bool, bool]:
    # initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--src_path', required=True,
                        help='source ddi file path')
    parser.add_argument('--save_temp', action='store_true',
                        help='save temp files')
    parser.add_argument('--cat_only', action='store_true',
                        help='only concat ddi.yml, assuming temp files exist.')

    # parse args
    args = parser.parse_args(args)
    src_path: str = os.path.normpath(args.src_path)
    assert os.path.isfile(src_path)

    src_dir, src_filename = os.path.split(src_path)
    src_name, src_ext = os.path.splitext(src_filename)
    dst_path = os.path.join(os.curdir, src_name)
    if not os.path.isdir(dst_path):
        os.makedirs(dst_path)
    return src_path, dst_path, args.save_temp, args.cat_only


def main():
    src_path, dst_path, save_temp, cat_only = parse_args()
    with open(src_path, 'rb') as ddi_f:
        ddi_bytes = ddi_f.read()
    read_ddi(ddi_bytes, dst_path,
             save_temp=save_temp, cat_only=cat_only)


if __name__ == '__main__':
    main()
