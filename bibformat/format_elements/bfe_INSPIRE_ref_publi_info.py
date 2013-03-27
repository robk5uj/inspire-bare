# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""BibFormat element - Prints all the publication information in one go

LaTeX formats require some elements to be displayed differently depending on 
whether other elements were present or not.  It wasn't obvious how to do that
in the Invenio templating system, so this format element is a facade for 
those others and handles the decision logic.
"""

from invenio.bibformat_elements import bfe_report_numbers, bfe_INSPIRE_publi_coden
from invenio.bibformat_engine import eval_format_element, get_format_element


pubnoteFE = get_format_element('bfe_inspire_publi_info',  with_built_in_params=True)
arxivFE   = get_format_element('bfe_inspire_arxiv',       with_built_in_params=True)


def format_element(bfo, pubnotestyle="eu", pubnotemark="html", pubnotepre="&nbsp;&nbsp;", pubnotesuf="", pubnotesep="&nbsp;&nbsp;", 
                        arxivlinks="no", arxivcategory="yes", arxivprepubnote="&nbsp;&nbsp;[", arxivsufpubnote="].", arxivprenopub="&nbsp;&nbsp;", arxivsufnopub=".",
                        reportpre="&nbsp;&nbsp;", reportsuf=".", reportlimit="9999", reportsep=", ", reportext=""):

"""    Aggregates pubnote, arxive, and %% CITATION %% display

       This is the BFE that has the logic used to satisfy the reference display requirement for determining whether or not report numbers display, 
       and showing eprint arXiv numbers (if available) in two different ways depending on whether or not there is a journal pub. reference.
       If pub. ref. or eprint number, no report number
       if pub ref. and eprint number, eprint number in []
       else if eprint number, no []
"""
    out       = ''
    pubnote   = ''
    pubnote_w = ''
    arxiv     = ''
    arxiv_w   = ''
    repno     = ''
    repno_w   = ''
    pcnt_pre  = arxivprenopub
    pcnt_suf  = ''

    # Get the pubnote, if any

    pubnote = eval_format_element(pubnoteFE, bfo, {'style': pubnotestyle, 'markup': pubnotemark, 'separator': pubnotesep })[0]

    pubnote_w = wrap(pubnote, pubnotepre, pubnotesuf)

    # Get the arxiv number, surrounding it differently if there is or isn't a pubnote
    arxiv = eval_format_element(arxivFE, bfo, {'links': arxivlinks, 'category': arxivcategory })[0]
    if pubnote:
        arxiv_w = wrap(arxiv, arxivprepubnote, arxivsufpubnote)
    else:
        arxiv_w = wrap(arxiv, arxivprenopub, arxivsufnopub)

    # Get the report number, if there's no pubnote or arxiv number
    if pubnote or arxiv:
        out = pubnote_w + arxiv_w
    else:
        repno   = bfe_report_numbers.get_report_numbers_formatted(bfo, reportsep, reportlimit, reportext)
        repno_w = wrap(repno, reportpre, reportsuf)
        out     = repno_w
    return out


def wrap(val, pre, suf):
    """Wrap value in prefix and suffix - but only if its non-empty.
    
    @param val A string to wrap
    @param pre The part to go in front of val
    @param suf The part to go in back of val
    """
    if val:
        return pre + val + suf
    else:
        return val

# we know the argument is unused, thanks
# pylint: disable-msg=W0613
def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
# pylint: enable-msg=W0613
