#!/usr/bin/env python3

import subprocess
import os
import difflib
import sys
import time
import atexit
import datetime
import argparse

parser = argparse.ArgumentParser(description='Runs tests for RDBMS')
parser.add_argument('--start', type=int, default=1, choices=range(1, 42), help='the test at which to start')
parser.add_argument('--end', type=int, default=41, choices=range(1, 42), help='the test at which to end')
parser.add_argument('--timing-only', action='store_true', help='output only times; continue on when tests fail')
parser.add_argument('path', nargs='*', default='.', help='the root project directory from which to run the tests')
args = parser.parse_args()

RDBMS_ROOT = args.path[0]
RDBMS_DEBUG = os.environ['RDBMS_DEBUG'] if 'RDBMS_DEBUG' in os.environ else '0'

START_TEST = args.start
END_TEST = args.end

RUN_PERF_TESTS = RDBMS_DEBUG in ['2', '3']

RED   = "\033[1;31m"  
BLUE  = "\033[1;34m"
CYAN  = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD    = "\033[;1m"
REVERSE = "\033[;7m"

TESTS_PATHS = {
    '0': 'project_tests',
    '1': 'project_tests',
    '2': 'project_tests_1M',
    '3': 'project_tests_10M',
    '4': 'project_tests_100M'
}

if RDBMS_DEBUG is not None and RDBMS_DEBUG not in TESTS_PATHS:
    sys.stdout.write(RED + '`RDBMS_DEBUG` must be a number from 0-3 or be unset (currently ' + RDBMS_DEBUG + ').\n' + RESET)
    sys.stdout.flush()
    exit()

SHUTDOWN_TESTS = ['test01', 'test02', 'test10', 'test18', 'test19', 'test24', 'test25', 'test30']

PARALLEL_PERF_REFERENCE_TEST = 'test16'

PARALLEL_PERF_FUZZ = 1.2

PARALLEL_PERF_TESTS = {
    'test17': 0.5,
}

TESTS_PATH = os.path.join(RDBMS_ROOT, TESTS_PATHS[RDBMS_DEBUG])
SRC_PATH = os.path.join(RDBMS_ROOT, 'src')
CLIENT_PATH = os.path.join(SRC_PATH, 'client')
SERVER_PATH = os.path.join(SRC_PATH, 'server')

if not os.path.exists(RDBMS_ROOT):
    sys.stdout.write(RED + 'Project root ' + RDBMS_ROOT + ' does not exist.\n' + RESET)
    sys.stdout.write('Possible reasons for this:\n')
    sys.stdout.write('    1) You are not running this tool from the RDBMS project root directory.\n')
    sys.stdout.write('    2) Your path argument directory is set incorrectly.\n')
    sys.stdout.write('    3) You have not checked out your code on this machine.\n')
    sys.stdout.write('Please fix the problem and try again.\n')
    sys.stdout.flush()
    exit()

if not os.path.exists(TESTS_PATH):
    sys.stdout.write(RED + 'Tests directory ' + TESTS_PATH + ' does not exist.\n' + RESET)
    sys.stdout.write('Possible reasons for this:\n')
    sys.stdout.write('    1) You are not running this tool from the RDBMS project root directory.\n')
    sys.stdout.write('    2) Your path argument directory is set incorrectly.\n')
    sys.stdout.write('    3) Your `RDBMS_DEBUG` setting is configured incorrectly (try a different number from 0-3).\n')
    sys.stdout.write('    4) You have not created a directory called ' + TESTS_PATHS[RDBMS_DEBUG] + ' in your RDBMS project root directory.\n')
    sys.stdout.write('Please fix the problem and try again.\n')
    sys.stdout.flush()
    exit()

def error_no_binary(name, path):
    sys.stdout.write(RED + 'Project binary "' + name + '" at ' + path + ' does not exist.\n' + RESET)
    sys.stdout.write('Possible reasons for this:\n')
    sys.stdout.write('    1) You have not compiled the binary.\n')
    sys.stdout.write('    2) There was a compilation error the last time you built your project.\n')
    sys.stdout.write('    3) You are not running this tool from the RDBMS project root directory.\n')
    sys.stdout.write('    4) Your path argument directory is set incorrectly.\n')
    sys.stdout.write('Please fix the problem and try again.\n')
    sys.stdout.flush()
    exit()

if not os.path.exists(CLIENT_PATH):
    error_no_binary('client', CLIENT_PATH)

if not os.path.exists(SERVER_PATH):
    error_no_binary('server', SERVER_PATH)

tests_dir_files = os.listdir(TESTS_PATH)

test_files = [x.rsplit('.', 1)[0] for x in tests_dir_files if x.endswith('.dsl')]
test_files.sort()

sys.stdout.write('\n')
sys.stdout.write('---\n')
sys.stdout.write(BOLD + 'Welcome to rdbms-test.\n' + RESET)
sys.stdout.write('Copyleft Douglas Sherk, 2017. Licensed under GPL v2. See LICENSE file for details.\n')
sys.stdout.write('---\n\n')
sys.stdout.write('Your current working directory is ' + os.path.abspath(RDBMS_ROOT) + '\n')
sys.stdout.write('\n')
sys.stdout.write('    Optional environment variables:\n')
sys.stdout.write('    - RDBMS_DEBUG: 0, 1 - run tests from "$RDBMS_ROOT/project_tests"\n')
sys.stdout.write('                   2 - run tests from "$RDBMS_ROOT/project_tests_1M"\n')
sys.stdout.write('                       you can find these tests online\n')
sys.stdout.write('                   3 - run tests from "$RDBMS_ROOT/project_tests_10M"\n')
sys.stdout.write('                       you can generate these tests using generate.py\n')
sys.stdout.write('                   4 - run tests from "$RDBMS_ROOT/project_tests_100M"\n')
sys.stdout.write('                       you can generate these tests using generate.py\n')
sys.stdout.write('\n')
sys.stdout.write('Tests will be run on .dsl files in `' + TESTS_PATH + '` on the following files:\n')
sys.stdout.write(str(test_files) + '\n\n')
sys.stdout.flush()

if not RUN_PERF_TESTS:
    sys.stdout.write(CYAN + 'WARNING:' + RESET + ' Performance tests are only possible with `RDBMS_DEBUG` set to 2 or 3\n')
    sys.stdout.write('as lots of data is needed to be able to accurately judge execution times.\n')
    sys.stdout.write('Performance tests are ' + RED + 'disabled' + RESET + '.\n\n')
    sys.stdout.flush()

if args.timing_only:
    sys.stdout.write(CYAN + 'NOTICE:' + RESET + ' Tests running in timing-only mode.\n')
    sys.stdout.write('Failure reports will be truncated, and failing tests will not end the tests.\n\n')
    sys.stdout.flush()

def strip_commented_lines(text):
    return [x for x in text if not x.startswith('--')]

def print_failure(test_file, time, reason):
    color = RED if not args.timing_only else BLUE
    sys.stdout.write('[' + color + 'FAIL' + RESET + '] ' + test_file + '.dsl in ' + str(time) + ' ms\n\n')
    count = 0
    for line in reason.splitlines():
        sys.stdout.write('    ' + line + '\n')
        count += 1
        if count >= 20 or args.timing_only:
            sys.stdout.write('\n    ... failure report truncated')
            break
    sys.stdout.write('\n')
    sys.stdout.flush()
    if not args.timing_only:
        exit()

def print_success(test_file, time):
    sys.stdout.write('[' + GREEN + 'PASS' + RESET + '] ' + test_file + '.dsl in ' + str(time) + ' ms\n')
    sys.stdout.flush()

def print_warning(test_file, time, warning):
    sys.stdout.write('[' + BLUE + 'WARN' + RESET + '] ' + test_file + '.dsl in ' + str(time) + ' ms\n')
    sys.stdout.write('\n')
    sys.stdout.write('    ' + warning + '\n')
    sys.stdout.write('\n')
    sys.stdout.flush()

def popen_server():
    return subprocess.Popen([SERVER_PATH], stdout=subprocess.PIPE)

test = None
server = None
client = None
server = None

parallel_perf_reference_time = None

def close_processes():
    server.kill()

atexit.register(close_processes)

def error_no_reference_output(file_name, path):
    sys.stdout.write(RED + 'Test "' + file_name + '" at ' + path + ' has no matching .exp file.\n' + RESET)
    sys.stdout.write('Please fix this problem and try again.')
    sys.stdout.flush()
    exit()

def check_performance(test_file, test_time):
    if not RUN_PERF_TESTS or test_file not in PARALLEL_PERF_TESTS:
        return

    expected_time_mul = PARALLEL_PERF_TESTS[test_file]
    expected_time = parallel_perf_reference_time * expected_time_mul
    if test_time > expected_time * PARALLEL_PERF_FUZZ:
        print_failure(test_file,
                      test_time,
                      'Expected to take %d ms at most (%s * %.2f); did you implement parallel scanning?' %
                        (expected_time, PARALLEL_PERF_REFERENCE_TEST, expected_time_mul))

current_test = 0

for test_file in test_files:
    current_test += 1
    # The first test is imperative because it creates the DB.
    if current_test != 1 and (current_test < START_TEST or current_test > END_TEST):
        continue

    if server is None or server.poll() is not None:
        server = popen_server() 

    start_time = datetime.datetime.now()

    test_path = os.path.join(TESTS_PATH, '%s.dsl' % test_file)

    test = subprocess.Popen(['cat', test_path], stdout=subprocess.PIPE)
    client = subprocess.Popen([CLIENT_PATH], stdout=subprocess.PIPE, stdin=test.stdout)
    output_stream = client.communicate()

    test.wait()
    end_time = datetime.datetime.now()

    test_time = int((end_time - start_time).total_seconds() * 1000)

    if test_file == PARALLEL_PERF_REFERENCE_TEST:
        parallel_perf_reference_time = test_time

    check_performance(test_file, test_time)

    # Needed because the server sometimes takes a moment after the client has
    # exited for it to exit itself.
    time.sleep(0.01)

    if test_file in SHUTDOWN_TESTS:
        if server.poll() is None:
            print_failure(test_file, test_time, 'Server should have shut down, but did not')
    elif server.poll() is not None:
        print_failure(test_file, test_time, 'Server shut down, but should not have')

    if client.poll() is None:
        print_failure(test_file, test_time, 'Client should have shut down, but did not')

    if client.poll() != 0:
        print_failure(test_file, test_time, 'Client exited with code %d' % client.poll())

    if server.poll() not in [None, 0]:
        print_failure(test_file, test_time, 'Server exited with code %d' % server.poll())

    reference_path = os.path.join(TESTS_PATH, '%s.exp' % test_file)

    if not os.path.exists(reference_path):
        error_no_reference_output(test_file, reference_path)

    with open(reference_path, 'r') as reference_output_file:
        reference_output = reference_output_file.readlines()
        reference_output = [x.replace('\n', '') for x in reference_output]
        test_output = output_stream[0].decode('utf-8').splitlines()
        test_output = strip_commented_lines(test_output)

        diffs = difflib.unified_diff(reference_output, test_output, fromfile='reference', tofile='test', lineterm='', n=0)

        if next(diffs, None) is not None:
            reason = ''
            line_count = 0
            for line in diffs:
                for prefix in ('---', '+++', '@@'):
                    if line.startswith(prefix):
                        break
                else:
                    reason = reason + line + '\n'

                line_count += 1
                if line_count >= 50:
                    break

            print_failure(test_file, test_time, reason)
        else:
            if not RUN_PERF_TESTS and test_file in PARALLEL_PERF_TESTS:
                print_warning(test_file, test_time, ('This is a performance '
                    'test, but performance tests are not running. See '
                    '"WARNING" message at top of output.'))
            else:
                print_success(test_file, test_time)
        sys.stdout.flush()
