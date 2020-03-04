#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 09:37:21 2020

@author: pakitochus
"""
# ChangeLog
# ---------
#
# 2.12  Separeate the main library with the Scholar* helper classes and the 
#       main class, to be able to import them as libraries outside this 
#       script. 
#
# 2.11  The Scholar site seems to have become more picky about the
#       number of results requested. The default of 20 in scholar.py
#       could cause HTTP 503 responses. scholar.py now doesn't request
#       a maximum unless you provide it at the comment line. (For the
#       time being, you still cannot request more than 20 results.)
#
# 2.10  Merged a fix for the "TypError: quote_from_bytes()" problem on
#       Python 3.x from hinnefe2.
#
# 2.9   Fixed Unicode problem in certain queries. Thanks to smidm for
#       this contribution.
#
# 2.8   Improved quotation-mark handling for multi-word phrases in
#       queries. Also, log URLs %-decoded in debugging output, for
#       easier interpretation.
#
# 2.7   Ability to extract content excerpts as reported in search results.
#       Also a fix to -s|--some and -n|--none: these did not yet support
#       passing lists of phrases. This now works correctly if you provide
#       separate phrases via commas.
#
# 2.6   Ability to disable inclusion of patents and citations. This
#       has the same effect as unchecking the two patents/citations
#       checkboxes in the Scholar UI, which are checked by default.
#       Accordingly, the command-line options are --no-patents and
#       --no-citations.
#
# 2.5:  Ability to parse global result attributes. This right now means
#       only the total number of results as reported by Scholar at the
#       top of the results pages (e.g. "About 31 results"). Such
#       global result attributes end up in the new attrs member of the
#       used ScholarQuery class. To render those attributes, you need
#       to use the new --txt-globals flag.
#
#       Rendering global results is currently not supported for CSV
#       (as they don't fit the one-line-per-article pattern). For
#       grepping, you can separate the global results from the
#       per-article ones by looking for a line prefix of "[G]":
#
#       $ scholar.py --txt-globals -a "Einstein"
#       [G]    Results 11900
#
#                Title Can quantum-mechanical description of physical reality be considered complete?
#                  URL http://journals.aps.org/pr/abstract/10.1103/PhysRev.47.777
#                 Year 1935
#            Citations 12804
#             Versions 80
#              Cluster ID 8174092782678430881
#       Citations list http://scholar.google.com/scholar?cites=8174092782678430881&as_sdt=2005&sciodt=0,5&hl=en
#        Versions list http://scholar.google.com/scholar?cluster=8174092782678430881&hl=en&as_sdt=0,5
#
# 2.4:  Bugfixes:
#
#       - Correctly handle Unicode characters when reporting results
#         in text format.
#
#       - Correctly parse citation-only (i.e. linkless) results in
#         Google Scholar results.
#
# 2.3:  Additional features:
#
#       - Direct extraction of first PDF version of an article
#
#       - Ability to pull up an article cluster's results directly.
#
#       This is based on work from @aliparsai on GitHub -- thanks!
#
#       - Suppress missing search results (so far shown as "None" in
#         the textual output form.
#
# 2.2:  Added a logging option that reports full HTML contents, for
#       debugging, as well as incrementally more detailed logging via
#       -d up to -dddd.
#
# 2.1:  Additional features:
#
#       - Improved cookie support: the new --cookie-file options
#         allows the reuse of a cookie across invocations of the tool;
#         this allows higher query rates than would otherwise result
#         when invoking scholar.py repeatedly.
#
#       - Workaround: remove the num= URL-encoded argument from parsed
#         URLs. For some reason, Google Scholar decides to propagate
#         the value from the original query into the URLs embedded in
#         the results.
#
# 2.0:  Thorough overhaul of design, with substantial improvements:
#
#       - Full support for advanced search arguments provided by
#         Google Scholar
#
#       - Support for retrieval of external citation formats, such as
#         BibTeX or EndNote
#
#       - Simple logging framework to track activity during execution
#
# 1.7:  Python 3 and BeautifulSoup 4 compatibility, as well as printing
#       of usage info when no options are given. Thanks to Pablo
#       Oliveira (https://github.com/pablooliveira)!
#
#       Also a bunch of pylinting and code cleanups.
#
# 1.6:  Cookie support, from Matej Smid (https://github.com/palmstrom).
#
# 1.5:  A few changes:
#
#       - Tweak suggested by Tobias Isenberg: use unicode during CSV
#         formatting.
#
#       - The option -c|--count now understands numbers up to 100 as
#         well. Likewise suggested by Tobias.
#
#       - By default, text rendering mode is now active. This avoids
#         confusion when playing with the script, as it used to report
#         nothing when the user didn't select an explicit output mode.
#
# 1.4:  Updates to reflect changes in Scholar's page rendering,
#       contributed by Amanda Hay at Tufts -- thanks!
#
# 1.3:  Updates to reflect changes in Scholar's page rendering.
#
# 1.2:  Minor tweaks, mostly thanks to helpful feedback from Dan Bolser.
#       Thanks Dan!
#
# 1.1:  Made author field explicit, added --author option.
#
# Don't complain about missing docstrings: pylint: disable-msg=C0111
#
# Copyright 2010--2017 Christian Kreibich. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import optparse
import sys
from scholar import ScholarConf, ScholarUtils, ScholarQuerier, ScholarSettings
from scholar import ClusterScholarQuery, SearchScholarQuery
from scholar import citation_export, csv, citation_export_str, txt

def main():
    usage = """scholar.py [options] <query string>
A command-line interface to Google Scholar.

Examples:

# Retrieve one article written by Einstein on quantum theory:
scholar.py -c 1 --author "albert einstein" --phrase "quantum theory"

# Retrieve a BibTeX entry for that quantum theory paper:
scholar.py -c 1 -C 17749203648027613321 --citation bt

# Retrieve five articles written by Einstein after 1970 where the title
# does not contain the words "quantum" and "theory":
scholar.py -c 5 -a "albert einstein" -t --none "quantum theory" --after 1970"""

    fmt = optparse.IndentedHelpFormatter(max_help_position=50, width=100)
    parser = optparse.OptionParser(usage=usage, formatter=fmt)
    group = optparse.OptionGroup(parser, 'Query arguments',
                                 'These options define search query arguments and parameters.')
    group.add_option('-a', '--author', metavar='AUTHORS', default=None,
                     help='Author name(s)')
    group.add_option('-A', '--all', metavar='WORDS', default=None, dest='allw',
                     help='Results must contain all of these words')
    group.add_option('-s', '--some', metavar='WORDS', default=None,
                     help='Results must contain at least one of these words. Pass arguments in form -s "foo bar baz" for simple words, and -s "a phrase, another phrase" for phrases')
    group.add_option('-n', '--none', metavar='WORDS', default=None,
                     help='Results must contain none of these words. See -s|--some re. formatting')
    group.add_option('-p', '--phrase', metavar='PHRASE', default=None,
                     help='Results must contain exact phrase')
    group.add_option('-t', '--title-only', action='store_true', default=False,
                     help='Search title only')
    group.add_option('-P', '--pub', metavar='PUBLICATIONS', default=None,
                     help='Results must have appeared in this publication')
    group.add_option('--after', metavar='YEAR', default=None,
                     help='Results must have appeared in or after given year')
    group.add_option('--before', metavar='YEAR', default=None,
                     help='Results must have appeared in or before given year')
    group.add_option('--no-patents', action='store_true', default=False,
                     help='Do not include patents in results')
    group.add_option('--no-citations', action='store_true', default=False,
                     help='Do not include citations in results')
    group.add_option('-C', '--cluster-id', metavar='CLUSTER_ID', default=None,
                     help='Do not search, just use articles in given cluster ID')
    group.add_option('-c', '--count', type='int', default=None,
                     help='Maximum number of results')
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'Output format',
                                 'These options control the appearance of the results.')
    group.add_option('--txt', action='store_true',
                     help='Print article data in text format (default)')
    group.add_option('--txt-globals', action='store_true',
                     help='Like --txt, but first print global results too')
    group.add_option('--csv', action='store_true',
                     help='Print article data in CSV form (separator is "|")')
    group.add_option('--csv-header', action='store_true',
                     help='Like --csv, but print header with column names')
    group.add_option('--citation', metavar='FORMAT', default=None,
                     help='Print article details in standard citation format. Argument Must be one of "bt" (BibTeX), "en" (EndNote), "rm" (RefMan), or "rw" (RefWorks).')
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'Miscellaneous')
    group.add_option('--cookie-file', metavar='FILE', default=None,
                     help='File to use for cookie storage. If given, will read any existing cookies if found at startup, and save resulting cookies in the end.')
    group.add_option('-d', '--debug', action='count', default=0,
                     help='Enable verbose logging to stderr. Repeated options increase detail of debug output.')
    group.add_option('-v', '--version', action='store_true', default=False,
                     help='Show version information')
    parser.add_option_group(group)

    options, _ = parser.parse_args()

    # Show help if we have neither keyword search nor author name
    if len(sys.argv) == 1:
        parser.print_help()
        return 1

    if options.debug > 0:
        options.debug = min(options.debug, ScholarUtils.LOG_LEVELS['debug'])
        ScholarConf.LOG_LEVEL = options.debug
        ScholarUtils.log('info', 'using log level %d' % ScholarConf.LOG_LEVEL)

    if options.version:
        print('This is scholar.py %s.' % ScholarConf.VERSION)
        return 0

    if options.cookie_file:
        ScholarConf.COOKIE_JAR_FILE = options.cookie_file

    # Sanity-check the options: if they include a cluster ID query, it
    # makes no sense to have search arguments:
    if options.cluster_id is not None:
        if options.author or options.allw or options.some or options.none \
           or options.phrase or options.title_only or options.pub \
           or options.after or options.before:
            print('Cluster ID queries do not allow additional search arguments.')
            return 1

    querier = ScholarQuerier()
    settings = ScholarSettings()

    if options.citation == 'bt':
        settings.set_citation_format(ScholarSettings.CITFORM_BIBTEX)
    elif options.citation == 'en':
        settings.set_citation_format(ScholarSettings.CITFORM_ENDNOTE)
    elif options.citation == 'rm':
        settings.set_citation_format(ScholarSettings.CITFORM_REFMAN)
    elif options.citation == 'rw':
        settings.set_citation_format(ScholarSettings.CITFORM_REFWORKS)
    elif options.citation is not None:
        print('Invalid citation link format, must be one of "bt", "en", "rm", or "rw".')
        return 1

    querier.apply_settings(settings)

    if options.cluster_id:
        query = ClusterScholarQuery(cluster=options.cluster_id)
    else:
        query = SearchScholarQuery()
        if options.author:
            query.set_author(options.author)
        if options.allw:
            query.set_words(options.allw)
        if options.some:
            query.set_words_some(options.some)
        if options.none:
            query.set_words_none(options.none)
        if options.phrase:
            query.set_phrase(options.phrase)
        if options.title_only:
            query.set_scope(True)
        if options.pub:
            query.set_pub(options.pub)
        if options.after or options.before:
            query.set_timeframe(options.after, options.before)
        if options.no_patents:
            query.set_include_patents(False)
        if options.no_citations:
            query.set_include_citations(False)

    if options.count is not None:
        options.count = min(options.count, ScholarConf.MAX_PAGE_RESULTS)
        query.set_num_page_results(options.count)

    querier.send_query(query)

    if options.csv:
        csv(querier)
    elif options.csv_header:
        csv(querier, header=True)
    elif options.citation is not None:
        citation_export(querier)
    else:
        txt(querier, with_globals=options.txt_globals)

    if options.cookie_file:
        querier.save_cookies()

    return 0

if __name__ == "__main__":
    sys.exit(main())
