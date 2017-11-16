#!/usr/bin/env python3

import os
import argparse
import random
import shutil

parser = argparse.ArgumentParser(description='Generates test case data for RDBMS')
parser.add_argument('--size', choices=('10M', '100M'), help='the size of the dataset')
parser.add_argument('path', nargs='*', default='.', help='the directory in which to create the tests')
args = parser.parse_args()

DATA_SIZES = {
  '10M': 10000000,
  '100M': 100000000,
}

data_size = DATA_SIZES[args.size]
root_path = args.path[0]
path = os.path.join(root_path, 'project_tests_%s' % args.size)

if not os.path.exists(path):
  shutil.copytree('project_tests', path)

with open(os.path.join(path, 'data1.csv'), 'w') as fp:
  fp.write('db1.tbl1.col1\n')
  for i in range(0, data_size):
    fp.write('%d\n' % i)

with open(os.path.join(path, 'data2.csv'), 'w') as fp:
    fp.write('db1.tbl2.col1,db1.tbl2.col2,db1.tbl2.col3,db1.tbl2.col4\n')
    for i in range(0, data_size):
        fp.write('%d,%d,%d,%d\n' % (i, i + 1, i + 2, random.randint(100000000, 200000000)))