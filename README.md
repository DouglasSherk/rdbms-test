# RDBMS Test

RDBMS Test (rdbms-test) is a system testing framework for testing a RDBMS
against a series of DSL (.dsl) scripts and their associated expected (.exp)
output. It is designed to be lightweight, simple to use, and explicative.

## Motivations

It is very tedious to compare a RDBMS project's output by diff to a series of
expected outputs; even more-so when there are more than a few tests. This tool
solves this problem by running the entire RDBMS test suite on a project all at
once and reporting the results in a way that is quick to assess (PASS/FAIL).

## Features

RDBMS Test has the following features:

* Automatic detection of missing files (project root, tests, binaries, etc.)
  and clear error messages explaining the problem.
* Quick switching between different datasets by environment variable.
* Spins up and down both the client and server, so you don't have to manage
  these processes yourself.
* Clear error messages with diffs and truncating to show you exactly how the
  tests failed.
* Colorful output to make it very quick to assess the test suite outcome.
* Performance tests which ensure that performance-focused features such as
  shared scans and B-tree indexes are working.
* Detection and test failure when the client should have shut down but didn't,
  and when the server shut down and shouldn't have, or stayed up and shouldn't
  have.
* Warnings when tests are passing functionally but are not serving their
  intended purpose.
* More to come.

In addition, RDBMS Test will be improved over time, including the addition of
more granular tests for later tasks. Make sure to update periodically so that
you can take advantage of updates.

## Getting Started

Clone the repo to the machine in which you wish to test the RDBMS:

```
cd ~
git clone https://github.com/DouglasSherk/rdbms-test.git
```

The only prerequisite package for RDBMS Test is python3. On any Debian-based
OS, you can install python3 as follows:

```
sudo apt-get install python3
```

## Configuring

There are two optional environment variables which you can set:

* `RDBMS_ROOT`: The root RDBMS project directory (defaults to pwd)
* `RDBMS_DEBUG`:
  * 0, 1 - run tests from "$RDBMS\_ROOT/project\_tests"
  * 2 - run tests from "$RDBMS\_ROOT/project\_tests\_1M"
  * 3 - run tests from "$RDBMS\_ROOT/project\_tests\_100M"

## Running the tests

**Make sure to set your current working directory to your RDBMS project
root---not the RDBMS test root.** It's possible to have your CWD set elsewhere,
but it is more difficult to configure that way.

Running the tests is simple:

```
python3 ~/rdbms-test/test.py
```

You should receive output similar to the following---though your
errors/successes will be different:
![RDBMS Test output with a test failure](/img/output.png?raw=true "RDBMS Test output with a test failure")

## Performance tests

**To be able to run performance tests, you must have a `project_tests_1M`
folder in your RDBMS project root.** You should add this folder, and some tests
and test data, if you do not have it.

To run performance tests, you must set `RDBMS_DEBUG` to either `2` or `3`. The
reason for this requirement is that performance tests require large amounts of
data for their results to be meaningful.

Performance tests currently run on tests 11 through 16. The shared parallel
scan tests are expected to perform faster than a series of single sequential
scans would. The expected speeds are not tuned very well yet, so don't fret if
you have implemented parallel scanning and your tests are still failing. Please
let me know though, so that we can tune them more appropriately!

## Supported tests

RDBMS Test currently supports all of the tests from 1 to 16. It will
theoretically work for every single test, but performance tests and other
domain-specific requirements have not been tuned for any tests past 16.

## Spinning up and spinning down the client and server

RDBMS Test automatically spins up and down the client and server. You should
not need to do anything before or after the tests have run to either prepare or
clean up. Make sure that the server is not already running when you run the
test suite, or your client may connect to the wrong server.

## Planned features

* More performance tests for the tests after 16.
* Suggested improvements and possible causes for problems in your code,
  including performance issues.
* Automatic generation of 100M record datasets.
* Creating new tests on-the-fly to stress test your project.
* Detecting when tests are running too fast and possibly skipping essential
  steps.

## Recommended project changes

It is recommended that you change your RDBMS to support reading the
`RDBMS_DEBUG` environment variable and rewrite paths to the correct directory.
Making this addition to your code will allow you to very quickly switch between
different types of tests just by running RDBMS Test with a different
environment variable. Some sample code illustrating how to make this change
follows:

```c
/**
 * Replaces path in place if `RDBMS_DEBUG` env var is set.
 * @param  path   An absolute or relative path to a file.
 * @return A path to the same file with a relative path.
 * NOTE: Assumes that there is space to replace the
 * absolute path with a relative path.
 */
char* path_rewrite(char* path) {
  const char* debug = getenv("RDBMS_DEBUG");
  int debug_level = 0;
  if (debug) {
    debug_level = atoi(debug);
  }
  if (debug_level < 1 || debug_level > 3) {
    // We're in production (the test machines); return the path directly.
    return path;
  }

  char* file_name = NULL;
  for (char* end = &path[strlen(path) - 1]; end != path; end--) {
    if (*end == '/') {
      file_name = end;
      break;
    }
  }

  // It's just a file without a path. Return it directly.
  if (file_name == NULL) {
    return path;
  }

  char replace_path[64];
  switch (debug_level) {
    case 1:
      strcpy(replace_path, "project_tests/");
      break;
    case 2:
      strcpy(replace_path, "project_tests_1M/");
      break;
    case 3:
      strcpy(replace_path, "project_tests_100M/");
      break;
    default:
      break;
  }
  char* start = file_name - strlen(replace_path);

  // Don't copy the null terminator.
  for (size_t i = 0; i < strlen(replace_path); i++) {
    start[i] = replace_path[i];
  }

  return start;
}
```

## Diagnosing problems

If you misconfigure RDBMS Test, or your RDBMS has problems, the script should
explain the problem and possible causes.

## Questions and comments

You can reach me at doug (at) sherk (dot) me, or via the issue tracker here on
GitHub.
