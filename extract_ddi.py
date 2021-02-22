#!/usr/bin/env python3

from utils.ddi_utils import read_ddi
import argparse
import os


def parse_args(args: list[str] = None):
    # initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--src-path', required=True,
                        help='source ddi file path')

    # parse args
    args = parser.parse_args(args)
    src_path: str = os.path.normpath(args.src_path)
    assert os.path.isfile(src_path)

    src_dir, src_filename = os.path.split(src_path)
    src_name, src_ext = os.path.splitext(src_filename)
    dst_path = os.path.join(src_dir, src_name)
    if not os.path.isdir(dst_path):
        os.makedirs(dst_path)
    return src_path, dst_path


def main():
    src_path, dst_path = parse_args()
    with open(src_path, 'rb') as ddi_f:
        ddi_bytes = ddi_f.read()
    read_ddi(ddi_bytes, dst_path)


if __name__ == '__main__':
    main()
