# -*- coding: utf-8 -*-         apply abstract switch and bfo/bfts
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2011 CERN.
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
"""BibFormat element - Prints BibTeX meta-data"""


import re
import cgi
from invenio.search_engine import search_pattern
from invenio.search_engine import get_fieldvalues
from invenio.config import CFG_SITE_LANG
from invenio.bibformat_elements import bfe_report_numbers as bfe_repno
from invenio.bibformat import format_record

#from invenio.bibformat_engine import eval_format_element, get_format_element
#pubnoteFE = get_format_element('bfe_inspire_publi_info', with_built_in_params=True)

def format_element(bfo, width="50", show_abstract="False"):
    """
    Prints a full BibTeX record.

    'width' must be >= 30.
    This format element is an example of a large element, which does
    all the formatting by itself

    @param width the width (in number of characters) of the record
    """

    # Values of the note field which should not be displayed.
    # These are typically added programmatically, so stupid string matching is
    # ok. If this assumption changes, turn this into a list of regexps to apply
    # for a match test.
    note_values_skip = ["* Temporary entry *", "* Brief entry *"]

    width = int(width)
    if width < 30:
        width = 30
    name_width = 21
    value_width = width-name_width
    recID = bfo.control_field('001')

    # Initialize user output
    out = "@"
    erratum_note = ''
    displaycnt = 0
    def texified(name, value):
        """Closure of format_bibtex_field so we don't keep passing static data
    
        Saves a little bit of boilerplate.
        """
        return format_bibtex_field(name, value, name_width, value_width)

    #Print entry type
#    import invenio.bibformat_elements.bfe_collection as bfe_collection
#    collection = bfe_collection.format_element(bfo=bfo, kb="DBCOLLID2BIBTEX")

    #This is a sequence of boolean collection switches initialized as false, to test for and switch on one and only one collection 
    #type and make the transition from INSPIRE collection types, to bibtex collection labels. 

    collections = bfo.fields("980")
    col_swCP=False
    col_swT=False
    col_swP=False
    col_swB=False
#    col_swA=False  #perhaps for future use?

    if not collections:
        collection = "article"  #default will be article i.e. preprint
    else:
        for collection in collections:

            if "ConferencePaper" in collection['a']:
                col_swCP=True
            if "THESIS" in collection['a'] or "Thesis" in collection['a']:
                col_swT=True
            if "PROCEEDINGS" in collection['a'] or "Proceedings" in collection['a']:
                col_swP=True
            if "BOOK" in collection['a'] or "Book" in collection['a']:
                col_swB=True
#            if "arXiv" in collection['a']:
#                col_swA=True
            
        if col_swCP:
            collection = 'inproceedings'
        elif col_swT:
            collection = 'phdthesis'
        elif col_swP:
            collection = 'proceedings'
        elif col_swB:
            collection = 'book'
        else:
            collection = 'article'

    #Master thesis has to be identified    
    if collection == 'phdthesis' and bfo.field("502__b") == 'Master': 
        out += 'mastersthesis'
    else:
        out += collection
    out += "{"

    # BibTeX key
    import invenio.bibformat_elements.bfe_texkey as bfe_texkey
    key = bfe_texkey.format_element(bfo, harvmac=False)

    out += key + ','

        #If author cannot be found, print a field key=recID
    import invenio.bibformat_elements.bfe_INSPIRE_authors as bfe_authors
    authors = bfe_authors.format_element(bfo=bfo,
                                 limit="10",
                                 separator=" and ",
                                 extension=" and others",
                                 collaboration = "no",
                                 print_links="no",
                                 name_last_first = "yes",
                                 markup = "bibtex")

    #bibtex does authors a bit differently with spaces and initials so this sequence does some cleaning up
    if authors:
        asub1 = re.sub(r'([A-Z][a-z]{0,1}\.)',r'\1 ',authors)
        asub2 = re.sub(r'  (and)',r' \1',asub1)       
        asub3 = re.sub(r' ,',r',',asub2)
        asub4 = re.sub(r' $',r'',asub3)
    # Editors
    import invenio.bibformat_elements.bfe_editors as bfe_editors
    editors = bfe_editors.format_element(bfo=bfo, limit="10",
                                 separator=" and ",
                                 extension="",
                                 print_links="no")

    if editors:
        out += texified("editor", editors)
    elif authors:
        out += texified("author", asub4)

    # Title
    import invenio.bibformat_elements.bfe_INSPIRE_title_brief as bfe_title
    title = bfe_title.format_element(bfo=bfo, brief="yes")
    title = '{' + title + '}'
    out += texified("title", title)

    #This code sequence is for getting the conference paper's parent proceedings volume information
    if collection == "inproceedings":
        cnum = bfo.field("773__w")
        if cnum != "":
            cnum = cnum.replace("/", "-")
            search_res = search_pattern(p="111__g:" + str(cnum) + " and 980__a:CONFERENCES")
            if search_res:
                recID = list(search_res)[0]             
                booktitle = get_fieldvalues(recID,'773__x',repetitive_values=True)[0]
                if booktitle != "":
                    out += texified("booktitle", booktitle)

    # Institution
    if collection ==  "techreport":
        publication_name = bfo.field("269__b")
        out += texified("institution", publication_name)

    # Organization
    if collection == "inproceedings" or collection == "proceedings":
        organization = []
        organization_1 = bfo.field("260__b")
        if organization_1 != "":
            organization.append(organization_1)
        organization_2 = bfo.field("269__b")
        if organization_2 != "":
            organization.append(organization_2)
        out += texified("organization", ". ".join(organization))

    # Publisher
    if collection == "book" or \
           collection == "inproceedings" \
           or collection == "proceedings":
        publishers = []
        import invenio.bibformat_elements.bfe_publisher as bfe_publisher
        publisher = bfe_publisher.format_element(bfo=bfo)
        if publisher != "":
            publishers.append(publisher)
        publication_name = bfo.field("269__b")
        if publication_name != "":
            publishers.append(publication_name)
        imprint_publisher_name = bfo.field("933__b")
        if imprint_publisher_name != "":
            publishers.append(imprint_publisher_name)
        imprint_e_journal__publisher_name = bfo.field("934__b")
        if imprint_e_journal__publisher_name != "":
            publishers.append(imprint_e_journal__publisher_name)

        out += texified("publisher", ". ".join(publishers))

    # Collaboration
    collaborations = []
    for collaboration in bfo.fields("710__g"):
        if collaboration not in collaborations:
            trncd_collab = re.sub(r'(.+) [Cc]ollaboration',r'\1',collaboration)
            collaborations.append(trncd_collab)
    out += texified("collaboration", ", ".join(collaborations))

    # School
    if collection == "phdthesis":
        university = bfo.field("100__u")

        out += texified("school", university)

        thesisyear = bfo.field("502__d")
        if thesisyear != "":
            out += texified("year", thesisyear)


    # Address
    if collection == "book" or \
           collection == "inproceedings" or \
           collection == "proceedings" or \
           collection == "phdthesis" or \
           collection == "techreport":
        addresses = []
        publication_place = bfo.field("260__a")
        if publication_place != "":
            addresses.append(publication_place)
        publication_place_2 = bfo.field("269__a")
        if publication_place_2 != "":
            addresses.append(publication_place_2)
        imprint_publisher_place = bfo.field("933__a")
        if imprint_publisher_place != "":
            addresses.append(imprint_publisher_place)
        imprint_e_journal__publisher_place = bfo.field("934__a")
        if imprint_e_journal__publisher_place != "":
            addresses.append(imprint_e_journal__publisher_place)

        out += texified("address", ". ".join(addresses))

        pubyear = get_year(bfo.field("260__c"))
        if pubyear != "":
            out += texified("year", pubyear)
        url = bfo.field("8564_u")
        if url != "":
            out += texified("url", url)



    # Journal
    if collection == "article":


        journal_infos = bfo.fields("773__") 
        for journal_info in journal_infos:
            journal_source = cgi.escape(journal_info.get('p', ''))
            volume         = cgi.escape(journal_info.get('v', ''))
            year           = cgi.escape(journal_info.get('y', ''))
            number         = cgi.escape(journal_info.get('n', ''))
            pages          = cgi.escape(journal_info.get('c', ''))
            if year == "":
                year = get_year(bfo.field("269__c"))
            elif year == "":
                year = get_year(bfo.field("260__c"))
            elif year == "":
                year = get_year(bfo.field("502__c"))
            elif year == "":
                year = get_year(bfo.field("909C0y"))
            str773 = ''            
            if journal_source:
                jsub = re.sub(r'\.([A-Z])',r'. \1',journal_source)
                if not (volume or number or pages or doi):
                    str773 += 'Submitted to: ' + jsub
                else:
                    str773 += jsub
                if displaycnt == 0:
                    out += texified("journal", str773)
            if volume:       # preparing volume and appending it
                if re.search("JHEP", str773):
                    volume = re.sub(r'\d\d(\d\d)',r'\1',volume)
                str773 += volume
                if displaycnt == 0:
                    out += texified("volume", volume)
            if year and displaycnt == 0:
                out += texified("year", year)
            elif year:
                year = '(' + year + ')'                
            if number:       # preparing number; it's appended below
                number = ',no.' + number
                if displaycnt == 0:
                    out += texified("number", number)
            if pages:
                dashpos = pages.find('-') 
                if dashpos > -1:
                    pages = pages[:dashpos]
                if displaycnt == 0:
                    out += texified("pages", pages)
            str773 += number
            if pages:
                str773 += ',' + pages
            str773 += year

    #N.B. In cases where there is more than one journal in journals iteration the second pass is usually a cite for a translation or 
    #something else to appear in a note.  Therefore erratum_note is set to display this data later on.  

    # DOI
            
            if displaycnt == 0 and collection == "article":
                doi = bfo.field("0247_a") + bfo.field("773__a")
                out += texified("doi", doi)

            displaycnt += 1            
            if displaycnt > 1 :
                errata = '[' + str773 + ']'    
                erratum_note = texified("note", errata)

    # Number
    if collection == "techreport" or collection == "proceedings":
        numbers = []
        host_number = bfo.field("773__n")
        if host_number != "":
            numbers.append(host_number)
        number = bfo.field("909C4n")
        if number != "":
            numbers.append(number)
        out += texified("number", ". ".join(numbers))

    # Volume
    if collection == "book" or collection == "proceedings":

        volumes = []
        host_volume = bfo.field("773__v")
        if host_volume != "":
            volumes.append(host_volume)
        volume = bfo.field("909C4v")
        if volume != "":
            volumes.append(volume)
        volume = bfo.field("490__v")
        if volume != "":
            volumes.append(volume)

        out += texified("volume", ". ".join(volumes))

    # Series
    if collection == "book" or collection == "proceedings":
        series = bfo.field("490__a")
        out += texified("series", series)

    # Pages
    if collection == "inproceedings":
        pages = []
        host_pages = bfo.field("773c")
        if host_pages != "":
            pages.append(host_pages)
            nb_pages = bfo.field("909C4c")
            if nb_pages != "":
                pages.append(nb_pages)
                phys_pagination = bfo.field("300__a")
                if phys_pagination != "":
                    pages.append(phys_pagination)

        out += texified("pages", ". ".join(pages))
        doi = bfo.field("0247_a")
        if doi != "":
            out += texified("doi", doi)
        year = bfo.field("269__c")
        if year != "":
            year = re.sub(r'(\d{4})[-\d]*',r'\1',year)
            out += texified("year", year)

    #Erratum note stuff here

    out += erratum_note

    # Eprint (aka arxiv number)
    import invenio.bibformat_elements.bfe_INSPIRE_arxiv as bfe_arxiv
    eprints = bfe_arxiv.get_arxiv(bfo, category = "no")
    cats    = bfe_arxiv.get_cats(bfo)
    if eprints:
        eprint = eprints[0]
        if eprint.upper().startswith('ARXIV:'):
            eprint = eprint[6:]

        out += texified("eprint", eprint)
        out += texified("archivePrefix", "arXiv")
        if cats:
            out += texified("primaryClass", cats[0])
    else:
        # No eprints, but we don't want refs to eprints[0] to error out below
        # This makes everything work nicely without a lot of extra gating
        eprints=[None]


    # Other report numbers
    out += texified("note", 
                    bfe_repno.get_report_numbers_formatted(bfo, 
                                                           separator=', ', 
                                                           limit='1000', 
                                                           skip=eprints[0]))
#    if collection == "inproceedings" and :
#        pubnote = bfo.field("500__a")
#        out += texified("note", pubnote)

 
    # Add %%CITATION line
    import invenio.bibformat_elements.bfe_INSPIRE_publi_info_latex as bfe_pil
    import invenio.bibformat_elements.bfe_INSPIRE_publi_coden as bfe_coden
    cite_as = bfe_pil.get_cite_line(arxiv=eprints[0], 
                                    pubnote=bfe_coden.get_coden_formatted(bfo, ','),
                                    repno=bfe_repno.get_report_numbers_formatted(bfo, '', '1'),
                                    bfo=bfo)

    #bfe_repno appends "ETC." to last rept. no. if more than one.  We don't want that.
    cite_as = re.sub(r' ETC.',r'',cite_as)
    out += texified("SLACcitation", cite_as)

    #display abstract switch in cases of a user desiring to include an abstract 
    if show_abstract == "True":
        abstract = bfo.field("520__a")
        out += texified("abstract", abstract)

    #The very last element in the bibtex list ends in a comma which we don't want. 
    out = re.sub(r',$',r'',out)
    out +="\n}"
    return out


def format_bibtex_field(name, value, name_width=20, value_width=40):
    """
    Formats a name and value to display as BibTeX field.

    'name_width' is the width of the name of the field (everything before " = " on first line)
    'value_width' is the width of everything after " = ".

    6 empty chars are printed before the name, then the name and then it is filled with spaces to meet
    the required width. Therefore name_width must be > 6 + len(name)

    Then " = " is printed (notice spaces).

    So the total width will be name_width + value_width + len(" = ")
                                                               (3)

    if value is empty string, then return empty string.

    For example format_bibtex_field('author', 'a long value for this record', 13, 15) will
    return :
    >>
    >>      name    = "a long value
    >>                 for this record",
    """
    if name_width < 6 + len(name):
        name_width = 6 + len(name)
    if value_width < 2:
        value_width = 2
    if value is None or value == "":
        return ""

    #format name
    name = "\n      "+name
    name = name.ljust(name_width)

    #format value
    value = '"'+value+'"' #Add quotes to value
    value_lines = []
    last_cut = 0
    cursor = value_width -1 #First line is smaller because of quote
    increase = False
    while cursor < len(value):
        if cursor == last_cut: #Case where word is bigger than the max
                               #number of chars per line
            increase = True
            cursor = last_cut+value_width-1

        if value[cursor] != " " and not increase:
            cursor -= 1
        elif value[cursor] != " " and increase:
            cursor += 1
        else:
            value_lines.append(value[last_cut:cursor])
            last_cut = cursor
            cursor += value_width
            increase = False
    #Take rest of string
    last_line = value[last_cut:]
    if last_line != "":
        value_lines.append(last_line)

    tabs = "".ljust(name_width + 2)
    value = ("\n"+tabs).join(value_lines)

    return name + ' = ' + value + ","

def get_name(string):
    """
    Tries to return the last name contained in a string.

    In fact returns the text before any comma in 'string', whith
    spaces removed. If comma not found, get longest word in 'string'

    Behaviour inherited from old GET_NAME function defined as UFD in
    old BibFormat. We need to return the same value, to keep back
    compatibility with already generated BibTeX records.

    Eg: get_name("سtlund, عvind B") returns "سtlund".
    """
    names = string.split(',')

    if len(names) == 1:
        #Comma not found.
        #Split around any space
        longest_name = ""
        words = string.split()
        for word in words:
            if len(word) > len(longest_name):
                longest_name = word
        return longest_name
    else:
        return names[0].replace(" ", "")


def get_year(date, default=""):
    """
    Returns the year from a textual date retrieved from a record

    The returned value is a 4 digits string.
    If year cannot be found, returns 'default'
    Returns first value found.

    @param date the textual date to retrieve the year from
    @param default a default value to return if year not fount
    """
    year_pattern = re.compile(r'\d\d\d\d')
    result = year_pattern.search(date)
    if result is not None:
        return result.group()

    return default

def get_month(date, ln=CFG_SITE_LANG, default=""):
    """
    Returns the year from a textual date retrieved from a record

    The returned value is the 3 letters short month name in language 'ln'
    If year cannot be found, returns 'default'

    @param date the textual date to retrieve the year from
    @param default a default value to return if year not fount
    """
    from invenio.dateutils import get_i18n_month_name
    from invenio.messages import language_list_long

    #Look for textual month like "Jan" or "sep" or "November" or "novem"
    #Limit to CFG_SITE_LANG as language first (most probable date)
    #Look for short months. Also matches for long months
    short_months = [get_i18n_month_name(month).lower()
                    for month in range(1, 13)] # ["jan","feb","mar",...]
    short_months_pattern = re.compile(r'('+r'|'.join(short_months)+r')',
                                      re.IGNORECASE) # (jan|feb|mar|...)
    result = short_months_pattern.search(date)
    if result is not None:
        try:
            month_nb = short_months.index(result.group().lower()) + 1
            return get_i18n_month_name(month_nb, "short", ln)
        except:
            pass

    #Look for month specified as number in the form 2004/03/08 or 17 02 2004
    #(always take second group of 2 or 1 digits separated by spaces or - etc.)
    month_pattern = re.compile(r'\d([\s]|[-/.,])\
    +(?P<month>(\d){1,2})([\s]|[-/.,])')
    result = month_pattern.search(date)
    if result is not None:
        try:
            month_nb = int(result.group("month"))
            return get_i18n_month_name(month_nb, "short", ln)
        except:
            pass

    #Look for textual month like "Jan" or "sep" or "November" or "novem"
    #Look for the month in each language

    #Retrieve ['en', 'fr', 'de', ...]
    language_list_short = [x[0]
                           for x in language_list_long()]
    for lang in language_list_short: #For each language
        #Look for short months. Also matches for long months
        short_months = [get_i18n_month_name(month, "short", lang).lower()
                        for month in range(1, 13)] # ["jan","feb","mar",...]
        short_months_pattern = re.compile(r'('+r'|'.join(short_months)+r')',
                                          re.IGNORECASE) # (jan|feb|mar|...)
        result = short_months_pattern.search(date)
        if result is not None:
            try:
                month_nb = short_months.index(result.group().lower()) + 1
                return get_i18n_month_name(month_nb, "short", ln)
            except:
                pass

    return default
