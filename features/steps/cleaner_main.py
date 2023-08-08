# Copyright © 2021, 2022, 2023 Pavel Tisnovsky, Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Implementation of test steps that run Insights Aggregator Cleaner and check its output."""

import subprocess
from src.process_output import process_generated_output

from behave import then, when


# default name of file generated by Insights Aggregator Cleaner during testing
test_output = "test"


@when("I run the cleaner to display all records older than {age}")
def run_cleaner_for_older_records(context, age):
    """Start the cleaner to retrieve list of older records."""
    out = subprocess.Popen(
        [
            "insights-results-aggregator-cleaner",
            "--output",
            test_output,
            "--max-age",
            age,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # check if subprocess has been started and its output caught
    assert out is not None

    context.add_cleanup(out.terminate)

    # it is expected that exit code will be 0
    process_generated_output(context, out, 0)


@when("I run the cleaner with the {flag} command line flag")
def run_cleaner_with_flag(context, flag):
    """Start the cleaner with given command-line flag."""
    out = subprocess.Popen(
        ["insights-results-aggregator-cleaner", flag],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # check if subprocess has been started and its output caught
    assert out is not None

    context.add_cleanup(out.terminate)

    # it is expected that exit code will be 0 or 2
    process_generated_output(context, out, 2)


@when("I run the cleaner with command to delete cluster {cluster}")
def run_cleaner_to_cleanup_cluster(context, cluster):
    """Start the cleaner clean up given cluster."""
    out = subprocess.Popen(
        ["insights-results-aggregator-cleaner", "--cleanup", "--clusters", cluster],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # check if subprocess has been started and its output caught
    assert out is not None

    context.add_cleanup(out.terminate)

    # it is expected that exit code will be 0
    process_generated_output(context, out, 0)


@when("I instruct the cleaner to vacuum database")
def start_db_vacuum(context):
    """Start the cleaner to vacuum database."""
    out = subprocess.Popen(
        ["insights-results-aggregator-cleaner", "-vacuum"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # check if subprocess has been started and its output caught
    assert out is not None

    context.add_cleanup(out.terminate)

    # it is expected that exit code will be 0
    process_generated_output(context, out, 0)


@then("I should see information about vacuuming process")
def check_db_vacuuming(context):
    """Check if DB vacuuming were started and finished."""
    # preliminary checks
    assert context.output is not None
    assert type(context.output) is list, "wrong type of output"

    expected_messages = (
        "DB connection configuration",
        "driverName",
        "postgres",
        "Vacuuming started",
        "Vacuuming finished",
    )

    # iterate over all expected messages and try to find them in caught output
    for expected_message in expected_messages:
        for line in context.output:
            if expected_message in line:
                break
        else:
            raise Exception(f"Message '{expected_message}' was not printed during vacuuming")


def check_help_from_cleaner(context):
    """Check if help is displayed by cleaner."""
    expected_output = """Clowder is not enabled, skipping init...
Usage of insights-results-aggregator-cleaner:
  -authors
        show authors
  -cleanup
        perform database cleanup
  -clusters string
        list of clusters to cleanup
  -fill-in-db
        fill-in database by test data
  -max-age string
        max age for displaying old records
  -multiple-rule-disable
        list clusters with the same rule(s) disabled by different users
  -output string
        filename for old cluster listing
  -show-configuration
        show configuration
  -summary
        print summary table after cleanup
  -vacuum
        vacuum database
  -version
        show cleaner version"""

    assert context.stdout is not None
    stdout = context.stdout.decode("utf-8").replace("\t", "    ")

    # preliminary checks
    assert stdout is not None, "stdout object should exist"
    assert type(stdout) is str, "wrong type of stdout object"

    # check the output
    assert stdout.strip() == expected_output.strip(), "{} != {}".format(
        stdout, expected_output
    )


def check_version_from_cleaner(context):
    """Check if version info is displayed by cleaner."""
    # preliminary checks
    assert context.output is not None
    assert type(context.output) is list, "wrong type of output"

    # check the output
    assert (
        "Insights Results Aggregator Cleaner version 1.0" in context.output
    ), "Caught output: {}".format(context.output)


def check_authors_info_from_cleaner(context):
    """Check if information about authors is displayed by cleaner."""
    # preliminary checks
    assert context.output is not None
    assert type(context.output) is list, "wrong type of output"

    # check the output
    assert (
        "Pavel Tisnovsky, Red Hat Inc." in context.output
    ), "Caught output: {}".format(context.output)


@then("I should see info about configuration displayed by cleaner on standard output")
def check_cleaner_configuration(context):
    """Check if information about actual configuration is displayed by cleaner."""
    # preliminary checks
    assert context.output is not None
    assert type(context.output) is list, "wrong type of output"

    expected_messages = (
        "DB connection configuration",
        "Storage configuration",
        "Logging configuration",
        "Cleaner configuration",
    )

    # iterate over all expected messages and try to find them in caught output
    for expected_message in expected_messages:
        for line in context.output:
            if f'"message":"{expected_message}"' in line:
                break
        else:
            raise Exception(f"Message '{expected_message}' was not found in configuration")


@then("I should see empty list of records")
def check_empty_list_of_records(context):
    """Check if the cleaner displays empty list of records."""
    with open(test_output, "r") as fin:
        content = fin.read()
        assert content == "", "expecting empty list of clusters"


@then("I should see the following clusters")
def check_non_empty_list_of_records(context):
    """Check if the cleaner displays the suggested clusters."""
    # set of expected clusters
    expected_clusters = set(item["cluster"] for item in context.table)

    # set of actually found clusters
    found_clusters = set()

    # check content of file generated during testing by Cleaner tool
    with open(test_output, "r") as fin:
        assert fin is not None
        for line in fin:
            assert line is not None
            items = line.split(",")
            cluster_name = items[0]
            found_clusters.add(cluster_name)

    # compare both sets
    assert expected_clusters == found_clusters, "Difference: {}".format(
        expected_clusters ^ found_clusters
    )
