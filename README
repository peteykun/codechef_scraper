# Usage

Run the script scrape.py, for instance if you want to scrape C programs for the problem
with problem code CLEANUP, run:

    $ python scrape.py CLEANUP C

The language selected may be one of C, JAVA, PYTH or PYTH3. For more command line options,
run `python scrape.py` without any arguments. The results are written to an sqlite database,
the default filename of the resulting database is `default.db`.

Exponential backoff is used with a multiplier of 1 second and a maximum wait time of 10 seconds
for any requests for each page requested, up to 10 requests.

# Dependecies

Install the following packages:

    $ pip install --user retrying requests
