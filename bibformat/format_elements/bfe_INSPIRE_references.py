# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2010 CERN, SLAC
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

"""BibFormat element - Prints references
   "references" is set equal to bib format object method "fields."  In this script, "fields" gets all the 999 
   fields in an inspire record and loads them into a list of dictionaries called references.  The data structure heierarchy is 
   List-->dictionary-->list (of values for a given key).  This explains the syntax for getting and using list elements and 
   dictionary values.  "List" has elements (dictionaries), one for each 999 field.  "dictionary" is a set of key:value pairs, 
   one for each subfield in a 999 field.  key is the subfield letter and value is its contents.  Within a dictionary, if a 
   subfield repeats, the value for that subfield key:value pair is "list," i.e. a list of contents of the repeating subfields.
   N.B. There is always a list for value when there are repeatable subfields, even if list has only one element [0].
   see:  http://invenio-software.org/code-browser/invenio.bibformat_engine.BibFormatObject-class.html#fields

   The script therefore executes a for loop, looping through reference in references and in each iteration all of a 999 
   field's data is available via its dictionary, making for minimal loop nesting.

"""
from invenio.search_engine import search_unit
from invenio.search_engine import search_unit_refersto
from invenio.search_engine import perform_request_search
from invenio.bibformat import format_record
import re
import string

#The first regex is used to separate out journal title, volume and number and the second one is used in moving letters in the 
#volume number to the end of the journal title because some databases like crossref and ADS use them there.

regexp = re.compile(r"(?P<j>.+)?,(?P<v>.+)?,(?P<p>.+)?")
volregex = re.compile(r"(?P<let>[A-Z])(?P<num>.*)")

#ajs is a dictionary of standard journal abbrev.keys and ADS title code values.  Used to create ADS URLs

ajs = {'Astrophys.J.Suppl.': 'ApJS', 'Astron.J.': 'AJ', 'Astropart.Phys.': 'APh', 'Astrophys.J.': 'ApJ', 'Astron.Astrophys.': 'A%26A', 'Mon.Not.Roy.Astron.Soc.': 'MNRAS', 'Acta Astron.': 'AcA', 'Acta Astron.Sin.': 'AcASn', 'Acta Astronaut.': 'AcAau', 'Acta Astrophys.Sin.': 'AcApS', 'Adv.Astron.Astrophys.': 'AdA&A', 'AIAA J.': 'AIAAJ', 'Amer.Astron.Soc.Meeting': 'AAS', 'Ann.Rev.Astron.Astrophys.': 'ARA&A', 'Annales Astrophys.': 'AnAp', 'Ark.Mat.Astron.Fys.': 'ArA', 'ASP Conf.Ser.': 'ASPC', 'Astrofiz.': 'Afz', 'Astron.Astrophys.Rev.': 'A&ARv', 'Astron.Astrophys.Suppl.Ser.': 'A&AS', 'Astron.Astrophys.Trans.': 'A&AT', 'Astron.Express': 'AExpr', 'Astron.Geophys.': 'A&G', 'Astron.Nachr.': 'AN', 'Astron.Rep.': 'ARep', 'Astron.Zh.': 'AZh', 'Astrophys.Bull.': 'AstBu', 'Astrophys.Lett.': 'ApL', 'Astrophys.Lett.Commun.': 'ApL&C', 'Astrophys.Nor.': 'ApNr', 'Astrophys.Space Sci.': 'Ap&SS', 'Astrophysics': 'Ap', 'Baltic Astron.': 'BaltA', 'Bol.A.A.Astron.': 'BAAA', 'Bull.Astron.Soc.India': 'BASI', 'Celestial Mech.': 'CeMDA', 'Chin.Astron.Astrophys.': 'ChA&A', 'Comments Astrophys.': 'ComAp', 'Exper.Astron.': 'ExA', 'Geophys.Astrophys.Fluid Dynamics': 'GApFD', 'Highlights Astron.': 'HiA', 'IAU Circ.': 'IAUC', 'IAU Symp.': 'IAUS', 'Irish Astron.J.': 'IrAJ', 'J.Astronaut.Sci.': 'JAnSc', 'J.Astrophys.Astron.': 'JApA', 'J.Hist.Astron.': 'JHA', 'J.Korean Astron.Soc.': 'JKAS', 'J.Roy.Astron.Soc.Canada': 'JRASC', 'Mem.Roy.Astron.Soc.': 'MmRAS', 'Mem.Soc.Ast.It.': 'MmSAI', 'Nauchnye Inform.Astron.Sov.Akad Nauk SSR': 'NInfo', 'New Astron.': 'NewA', 'Proc.Astron.Soc.Austral.': 'PASAu', 'Publ.Astron.Soc.Austral.': 'PASA', 'Publ.Astron.Soc.Jap.': 'PASJ', 'Publ.Astron.Soc.Pac.': 'PASP', 'Publ.Dominion Astrophys.Obs.': 'PDO', 'Q.J.Roy.Astron.Soc.': 'QJRAS', 'Rev.Mex.Astron.Astrof.Ser.Conf.': 'RMxAC', 'Rev.Mex.Astron.Astrofis.': 'RMxAA', 'Rev.Mod.Astron.': 'RvMA', 'Serb.Astron.J.': 'SerAJ', 'Sov.Astron.': 'SvA', 'Vistas Astron.': 'VA'}

def format_element(bfo, reference_prefix, reference_suffix):
    """
    Prints the references of this record

    @param reference_prefix a prefix displayed before each reference
    @param reference_suffix a suffix displayed after each reference
    """
    references = bfo.fields("999C5", escape=1, repeatable_subfields_p=True)

    out = ""
    last_o = ""

    if not references:
        return out

    out += "<table>"
    for reference in references:
        ref_out = []
        ref_out.append('<tr><td valign="top">')

        display_journal = ''
        display_report = ''
        clean_report = ''
        clean_journal = ''
        hits = []

#key o is the bracketed reference numbers displayed out to the left margin on the ref html page.
#Users typically number their paper's references [1][2]etc.
#This first if makes sure you don't have more than one reference number that is the same so we don't look stupid.

        if reference.has_key('o') and not reference['o'][0] == last_o:
            temp_ref = reference['o'][0].replace('.', '')
            if '[' in temp_ref and ']' in temp_ref:
                ref_out.append("<small>" + temp_ref + "</small> ")
            else:
                ref_out.append("<small>[" + temp_ref + "] </small> ")
            last_o = temp_ref
        ref_out.append("</td><td>")

        if reference_prefix:
            ref_out.append(reference_prefix)
#s is journal reference
        if reference.has_key('s'):
            display_journal = reference['s'][0]
            clean_journal = reference['s'][0]
#r is either an arXiv number or an institution report number
        if reference.has_key('r'):
            if "[" in reference['r'][0] and "]" in reference['r'][0]:
                breaknum = reference['r'][0].find('[')
                newreference = reference['r'][0][:breaknum].strip()
                display_report = newreference
                clean_report = newreference
            else:
                display_report = reference['r'][0]
                clean_report = reference['r'][0]
        if clean_report:
            hits = search_unit(f='reportnumber', p=clean_report)
        if clean_journal and len(hits)!=1:
            hits = search_unit(f='journal', p=clean_journal)
#a is a DOI
        if reference.has_key('a') and len(hits)!=1:
            hits = search_unit(f='doi', p=reference['a'][0])
        if len(hits) == 1:
            refersto_rec = str(list(hits)[0])

##ref_out.append('whats in refersto_rec: ' + str(refersto_rec) + 'real stuff: ')
##hits is a list (IIRC) called (and of data type?) intbitset, i.e. intbitset['<rec.no.>']
##and is the record number of the reference in inspire

##c_count is citation count

            c_count = str(len(search_unit_refersto('recid' + ':' + refersto_rec)))
            ref_out.append('<small>' + format_record(list(hits)[0],'hs2') + '  [' + "<a href=\"/search?ln=en&amp;p=refersto%3Arecid%3A" + refersto_rec + "\">" + c_count + "</a>"  + ' citations in HEP]</small>')
        else:
#else if the reference is not in inspire:
            if reference.has_key('a'):
                ref_out.append("<small> <a href=\"http://dx.doi.org/" + reference['a'][0] + "\">" + reference['a'][0]+ "</a></small>")
#h is author
            if reference.has_key('h'):
                ref_out.append("<small> " + reference['h'][0] + ",</small>")
#t is title
            if reference.has_key('t'):
                ref_out.append("<small> " + reference['t'][0] + "</small> -")
#p is publisher
            if reference.has_key('p'):
                ref_out.append("<small> " + reference['p'][0] + ".</small>")
#y is year
            if reference.has_key('y'):
                ref_out.append("<small> " + reference['y'][0] + ".</small>")
#m is miscellaneous i.e. anything refextract dumps because it doesn't know what else to do
            if reference.has_key('m'):
                ref_out.append("<small> "+ reference['m'][0].replace(']]', ']') + ".</small>")
#u is various URLs
            if reference.has_key('u'):
                ref_out.append("<small> <a href=" + reference['u'][0] + ">" + \
                reference['u'][0] + "</a></small>")
#i is ISBNs
            if reference.has_key('i'):
                for r in reference['i']:
                    ref_out.append("<small> <a href=\"/search?ln=en&amp;p=020__a%3A"+r+"\">"+r+"</a></small>")
            ref_out.append('<small>')

#sequence of if then else to create URLs for cite count, ADS, APS DOIs, and crossref links by priority

            if display_journal:
                search_arg = '999C5:' + clean_journal
                c_count = str(len(perform_request_search(p=search_arg)))
                ref_out.append(display_journal)
                ref_out.append('  [' + "<a href=\"/search?ln=en&amp;p=fin" + "+" + "c" + "+" + clean_journal + "\">" + c_count + "</a>" + ' citations in HEP]')
                jname = regexp.search(clean_journal)
                jn = str(jname.group('j'))
                vol = str(jname.group('v'))
                pp  = str(jname.group('p'))
                if ajs.has_key(jn):
                    ads_name = str(ajs[jn])
                    ref_out.append('  [' + "<a href=\"http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?bibstem=" + ads_name + "&amp;volume=" + vol + "&amp;page=" + pp + "\">" + 'ADS' + "</a>" + ']')
                if re.search("^Phys\.Rev\.$", jn) or re.search("^Phys\.Rev\.Lett\.$", jn) or re.search("$Rev\.Mod\.Phys\.$", jn):
                    letnum = volregex.search(vol)
                    apsjn = jn.replace('.','')                        
                    if letnum:
                        l = letnum.group('let')
                        n = letnum.group('num')
                        ref_out.append('  [' + "<a href=\"http://dx.doi.org/10.1103/" + apsjn + l + '.' + n + '.' + pp + "\">" + 'DOI' + "</a>" + ']')
                    else:
                        ref_out.append('  [' + "<a href=\"http://dx.doi.org/10.1103/" + apsjn + '.' + vol + '.' + pp + "\">" + 'DOI' + "</a>" + ']')
                else:
                    letnum = volregex.search(vol)
                    if letnum:
                        l = letnum.group('let')
                        n = letnum.group('num')
                        ref_out.append('  [' + "<a href=\"http://crossref.org/guestquery/?title=" + str(jn) + l + "&amp;volume=" + n + "&amp;page=" + pp + "\">" + 'CrossRef' + "</a>" + ']')
                    else:
                        ref_out.append('  [' + "<a href=\"http://crossref.org/guestquery/?title=" + str(jn) + "&amp;volume=" + vol + "&amp;page=" + pp + "\">" + 'CrossRef' + "</a>" + ']')

#sequence for report numbers: rept. no. cite count if no other way to get it, link to arXiv if rept. no. is eprint number, and 
#remember, all this is only if it is not in INSPIRE, and finally if nothing else works, let Google try it. 

            if display_report:
                ref_out.append(' ' + display_report)
                if not display_journal:
                   search_arg = '999C5:' + clean_report
                   c_count = str(len(perform_request_search(p=search_arg)))
                   ref_out.append('  [' + "<a href=\"/search?ln=en&amp;p=fin" + "+" + "c" + "+" + clean_report + "\">" + c_count + "</a>" + ' citations in HEP]')
                if re.search("\d{4}\.\d{4}", clean_report) or re.search("\/\d{7}", clean_report): 
                   ref_out.append('  [' + "<a href=\"http://arxiv.org/abs/" + clean_report + "\">" + 'arXiv' + "</a>" + ']')
                else:
                   ref_out.append('  [' + "<a href=\"http://www.google.com/&#35;hl=en&amp;output=search&amp;sclient=psy-ab&amp;q=%22" + clean_report + "%22\">" + 'Google' + "</a>" + ']')
                   
            ref_out.append("</small>")
        if reference_suffix:
            ref_out.append(reference_suffix)
        ref_out.append("</td></tr>")
        out += ' '.join(ref_out)
#The script loops through references creating a long string represented by "out"
    return out + "</table>"

#if re.search("^[A-Z].*", vol):

# we know the argument is unused, thanks
# pylint: disable-msg=W0613
def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
# pylint: enable-msg=W0613
