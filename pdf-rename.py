#!/usr/bin/python
# coding=utf8
import argparse
from nameparser import HumanName
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.high_level import extract_text
from pdfminer.pdftypes import PDFObjRef
import re
import subprocess

parser = argparse.ArgumentParser(description='Rename PDFs automatically \
                                to include author(s), year, and title.')
parser.add_argument('filename', metavar='filename', type=str,
                    help='PDF to rename')
parser.add_argument('--biblatex', action='store_true',
                    help='create biblatex entry')
parser.add_argument('--copy', action='store_true',
                    help='rename PDF file and keep original')
parser.add_argument('--rename', action='store_true',
                    help='rename PDF file and delete original')

args = parser.parse_args()

filename = vars(args)['filename']

with open(filename, 'rb') as f:
    parse = PDFParser(f)
    doc = PDFDocument(parse)

journals = ['BEHAVIORAL AND BRAIN',
            'J. Linguistics',
            'Journal of Comparative Germanic Linguistics',
            'Journal ofGermanic Linguistics',
            'Journal of Language Modelling',
            'Language, Volume',
            'Lingua',
            'Linguistic Inquiry',
            'Linguistic Typology',
            'Nat Lang Ling',
            'Nat Lang Semantics',
            'The Linguistic Review',
            'Theoretical Linguistics',
            'TO CITE THIS ARTICLE' # newer Glossa
            ]

def get_doi_from_text(text):
    """Extract DOI from text."""
    try:
        doi = re.search('(10.+?)( |$|,)', text[[text.index(x) for x in text if 'doi.org' in x or 'doi:' in x or 'DOI ' in x][0]]).group(1)
    except IndexError:
        doi = ""
    return(doi)

def tag_empty_items(list):
    """
    Replace empty strings ('') by strings of subsequent integers starting with 1.

    This allows addressing the items before and after because one can access
    the indexes of the strings of integers.
    """
    i = 1
    for item in list:
        if item == '':
            list[list.index(item)] = str(i)
            i = i+1
    return(list)

if 'Author' in doc.info[0] and doc.info[0]['Author'] != b'' and not type(doc.info[0]['Author'].decode('ISO-8859-1')) != str:
    author = doc.info[0]['Author'].decode('ISO-8859-1')

if 'Title' in doc.info[0] and doc.info[0]['Title'] != b'' and not type(doc.info[0]['Title'].decode('ISO-8859-1')) != str:
    title = re.sub(b'\\x84', b'---', doc.info[0]['Title']).decode('ISO-8859-1')
else:
    title = ""

if 'Subject' in doc.info[0] and not isinstance(doc.info[0]['Subject'], PDFObjRef) and doc.info[0]['Subject'] != b'' and 'Downloaded from' not in doc.info[0]['Subject'].decode('UTF-8'):
    subject = re.sub(b'\\x85', b'-', doc.info[0]['Subject']).decode('ISO-8859-1')
else:
    journalinfo = extract_text(filename, maxpages=1).split('\n')
    if any('Source: ' in line for line in journalinfo):
        # remove empty strings
        journalinfo = [str for str in journalinfo if str]
        subject = 'JSTOR'
    else:
        subject = [line for line in journalinfo if any(journal in line for journal in journals)][0]

if subject == 'JSTOR':
    values_one = re.search('Source: (.+?),.+?Vol. (\d{1,2})', journalinfo[[journalinfo.index(x) for x in journalinfo if 'Source: ' in x][0]])
    journaltitle = values_one.group(1)
    if journaltitle == "Linguistic Inquiry":
        shortjournaltitle = "LI"
    elif journaltitle == "Natural Language & Linguistic Theory":
        journaltitle = "Natural Language \& Linguistic Theory"
        shortjournaltitle = "NLLT"
    else:
        shortjournaltitle = journaltitle
    volume = values_one.group(2)
    values_two = re.search('No. (\d{1}).+?(\d{4}).+?pp. (\d{1,4})-(\d{1,4})', journalinfo[[journalinfo.index(x) for x in journalinfo if 'Source: ' in x][0]])
    number = values_two.group(1)
    year = values_two.group(2)
    page_start = values_two.group(3)
    page_end = values_two.group(4)
    author_field_index = [journalinfo.index(x) for x in journalinfo if 'Author(s): ' in x][0]
    title = journalinfo[author_field_index-1].strip(' \$')
    author = journalinfo[author_field_index].strip('Author(s):').strip()
    authors = author.split(' and ')
    doi = get_doi_from_text(journalinfo)
    eid = ""

if 'BEHAVIORAL AND BRAIN' in subject:
    journaltitle = "Behavioral and Brain Sciences"
    shortjournaltitle = "Behav. Brain Sci."
    if 'Page' in journalinfo[0]:
        values = re.search('BEHAVIORAL AND BRAIN SCIENCES \((\d{4})\), Page (\d{1}) of (\d{1,3})', journalinfo[0])
        page_start = values.group(2)
        page_end = values.group(3)
        eid = re.search('doi:.+?e(\d{1,3})', journalinfo[1]).group(1)
    else:
        values = re.search('BEHAVIORAL AND BRAIN SCIENCES \((\d{4})\) (\d{1,2}), (\d{1,3}) –(\d{1,3})', journalinfo[0])
        page_start = values.group(3)
        page_end = values.group(4)
        eid = ""
    year = values.group(1)
    volume = str(int(year)-1977)
    number = ""
    doi = get_doi_from_text(journalinfo)
    # Empty strings ('') are replaced by subsequent numbers starting
    # from 1 by tag_empty_strings.
    #
    # The title is then the list of strings from the index of '1'+1 to the
    # index of '2'; the list of authors starts at that '2'+1 and goes on to n+1
    # where n is the final original empty string before the field containing
    # the string 'Abstract:'.
    tag_empty_items(journalinfo)
    title = ' '.join(journalinfo[journalinfo.index('1')+1:journalinfo.index('2')])
    authors = []
    author_end = int(journalinfo[[journalinfo.index(x) for x in journalinfo if 'Abstract:' in x][0]-1])
    for n in range(2, author_end):
        authors.append(journalinfo[journalinfo.index(str(n))+1])

if 'Cognition' in subject:
    journalinfo = extract_text(filename, maxpages=1).split('\n')
    journaltitle = "Cognition"
    shortjournaltitle = "Cognition"
    values = re.search('Cognition, (\d{1,3}) \((\d{4})\) (\d{1,6})', doc.info[0]['Subject'].decode('UTF-8'))
    volume = values.group(1)
    number = ""
    year = values.group(2)
    page_start = "1"
    page_end = ""
    eid = values.group(3)
    doi = get_doi_from_text(journalinfo)
    tag_empty_items(journalinfo)
    title = journalinfo[journalinfo.index('4')+1]
    author_start = int(journalinfo.index('5')-1)
    author_end = int(journalinfo.index('6')-1)
    try: author
    except NameError: author = re.sub('(\*)|(\d)|( [a-z],)', '', journalinfo[author_start] + journalinfo[author_end])
    authors = author.split(', ')

if 'Cognitive Science' in subject:
    journalinfo = extract_text(filename, maxpages=1).split('\n')
    journaltitle = "Cognitive Science"
    shortjournaltitle = "Cognitive Science"
    values = re.search('Cognitive Science (\d{1,4}).(\d{1,2}):(\d{1,4})-(\d{1,4})', doc.info[0]['Subject'].decode('UTF-8'))
    year = values.group(1)
    volume = values.group(2)
    number = ""
    page_start = values.group(3)
    page_end = values.group(4)
    eid = ""
    if doc.info[0]['WPS-ARTICLEDOI'] != "":
        doi = doc.info[0]['WPS-ARTICLEDOI'].decode('UTF-8')
    else:
        doi = get_doi_from_text(journalinfo)
    author = journalinfo[journalinfo.index('')+3]
    author = re.sub('u¨', 'ü', author)
    author = re.sub('o¨', 'ö', author)
    authors = author.split(', ')

if 'Comparative Germanic Linguistics' in subject:
    journaltitle = "The Journal of Comparative Germanic Linguistics"
    shortjournaltitle = "JCGL"
    values = re.search('Journal of Comparative Germanic Linguistics (\d{1,3}): (\d{1,4})–(\d{1,4}), (\d{4})', subject)
    volume = values.group(1)
    number = ""
    year = values.group(4)
    page_start = values.group(2)
    page_end = values.group(3)
    if values == None:
        journalinfo = extract_text(filename, maxpages=1).split('\n')
        subject = [line for line in journalinfo if 'Comp German' in line][0]
        values = re.search('J Comp German Linguistics \((\d{4})\) (\d{1,3}):(\d{1,4})–(\d{1,4})', subject)
        volume = values.group(2)
        number = ""
        year = values.group(1)
        page_start = values.group(3)
        page_end = values.group(4)
    eid = ""
    doi = get_doi_from_text(journalinfo)
    try:
        if author == "":
            author = re.sub('\d', '', journalinfo[11])
        else:
            author = re.sub('ˇc', 'č', journalinfo[7])
            author = re.sub('1$', '', author)
    except NameError:
        author = ""
    authors = author.split(' and ')

if 'J. Linguistics' in subject:
    journaltitle = "Journal of Linguistics"
    shortjournaltitle = "JoL"
    values = re.search('J. Linguistics (\d{1,2}) \((\d{4})\), (\d{1,4})–(\d{1,4})', subject)
    volume = values.group(1)
    number = ""
    year = values.group(2)
    page_start = values.group(3)
    page_end = values.group(4)
    doi = get_doi_from_text(journalinfo)
    # title starts after a newline
    title_start = journalinfo[journalinfo.index('')+1]
    # title ends before the first author's name in upper case
    title_end = journalinfo[[journalinfo.index(author) for author in journalinfo[:15] if author.isupper()][0]-1]
    if title_start != title_end:
        title = re.sub('1$', '', title_start + ' ' + title_end)
    else:
        title = re.sub('1$', '', title_start)
    authors = [re.sub(' ', '', author).title() for author in journalinfo[:15] if author.isupper()]
    eid = ""

if 'Journal ofGermanic Linguistics' in subject:
    journaltitle = "Journal of Germanic Linguistics"
    shortjournaltitle = "Journal of Germanic Linguistics"
    values = re.search('Journal ofGermanic Linguistics (\d{1,3}).(\d{1}) \((\d{4})\):(\d{1,4})-(\d{1,4})', subject)
    volume = values.group(1)
    number = values.group(2)
    year = values.group(3)
    page_start = values.group(4)
    page_end = values.group(5)
    eid = ""
    doi = "" #get_doi_from_text(journalinfo)
    title = journalinfo[journalinfo.index('')+1].strip(' ')
    authors = author.split(' and ')

if 'Glossa' in subject:
    #author = HumanName(doc.info[0]['Author'].decode('ISO-8859-1'))
    journaltitle = "Glossa: a journal of general linguistics"
    shortjournaltitle = "Glossa"
    year = re.search('\d{4}', subject).group(0)
    glossa = re.search('([A-Za-z].*) (\d)\((\d{1,2})\): (\d{1,2}).+?(\d)-(\d{1,2}).+?(\d.*)', subject)
    volume = glossa.group(2)
    number = glossa.group(3)
    eid = glossa.group(4)
    page_start = glossa.group(5)
    page_end = glossa.group(6)
    doi = glossa.group(7)
    authors = author.split(' and ')

if 'TO CITE THIS ARTICLE' in subject:
    journaltitle = "Glossa: a journal of general linguistics"
    shortjournaltitle = "Glossa"
    journalinfo = journalinfo[journalinfo.index('TO CITE THIS ARTICLE:'):]
    journalinfo = ''.join(journalinfo[1:journalinfo.index('')])
    # Lau, Elaine and Nozomi Tanaka. 2021. The subject advantage in relative
    # clauses: A review. Glossa: a journal of general linguistics 6(1): 34.
    # 1–34. DOI:
    glossa = re.search('([A-Za-z].*). (\d{4}). (.+?). ' +
                       'Glossa: a journal of general linguistics ' +
                       '(\d{1,2})\((\d{1})\): (\d{1,3}). (\d{1})–(\d{1,3}). ' +
                       'DOI: https://doi.org/(.*)', journalinfo)
    author = glossa.group(1)
    year = glossa.group(2)
    title = glossa.group(3)
    volume, number = glossa.group(4), glossa.group(5)
    eid = glossa.group(6)
    page_start, page_end = glossa.group(7), glossa.group(8)
    doi = glossa.group(9)
    authors = author.split(' and ')

if "Journal of Language Modelling" in subject:
    journaltitle = "Journal of Language Modelling"
    shortjournaltitle = "Journal of Language Modelling"
    values = re.search('Journal of Language Modelling Vol (\d{1,2}), No (\d{1}) \((\d{4})\), pp. (\d{1,3})–(\d{1,3})', subject)
    volume, number, year = values.group(1), values.group(2), values.group(3)
    page_start, page_end = values.group(4), values.group(5)
    title = ' '.join(journalinfo[:journalinfo.index('')])
    author = re.sub('\d', '', journalinfo[journalinfo.index('')+1])
    authors = author.split(' and ')
    doi = ""
    eid = ""

if "Language, Volume" in subject:
    journaltitle = "Language"
    shortjournaltitle = "Lg"
    lg_info = journalinfo[:10]
    values = re.search('.+? Volume (\d{1,3}), Number (\d{1}), .+? (\d{4}), pp. (e|)(\d{1,4})-(e|)(\d{1,4})',
            subject)
    volume, number, year = values.group(1), values.group(2), values.group(3)
    page_start, page_end = values.group(4)+values.group(5), values.group(6)+values.group(7)
    doi = get_doi_from_text(lg_info)
    eid = ""
    if 'þÿ' in title:
        title_list = title.split('þÿ')[1].split('\x00')
        title = ''
        for char in title_list:
            title = title + char
    if 'þÿ' in author:
        author_list = author.split('þÿ')[1].split('\x00')
        author = ''
        for char in author_list:
            author = author + char
    authors = author.split(', ')

if "Language and Linguistics Compass" in subject:
    journaltitle = "Language and Linguistics Compass"
    shortjournaltitle = "Lang Linguist Compass"
    llc = extract_text(filename, maxpages=1).split('\n')
    if 'wileyonlinelibrary.com/journal/lnc3' in llc:
        llc_info = llc[[llc.index(x) for x in llc if 'Lang Linguist' in x or 'Lang. Linguist.' in x][0]]
        # llc_info: 'Lang. Linguist. Compass. year; vol: pfirst-plast
        values = re.search('.+? (\d{4}); (\d{1,3}): (\d{1,4})–(\d{1,4})', llc_info)
        year = values.group(1)
        volume = values.group(2)
        number = ""
        page_start, page_end = values.group(3), values.group(4)
        doi = doc.info[0]['WPS-ARTICLEDOI'].decode('UTF-8')
    else:
        llc_info = llc[:[llc.index(x) for x in llc if 'Abstract' in x][0]]
        # llc_info: ['journaltitle volume/number (year): pfirst-plast, doi',
        # '', 'title', '', 'author(s)', ...]
        author = re.sub('(\*)|(\d)', '', llc_info[[llc_info.index(x) for x in llc_info if '*' in x][0]])
        values = re.search('.+? (\d{1,2})/(\d{1}).+?\((\d{4})\): (\d{1,4})–(\d{1,4}), (.*)', llc_info[0])
        year = values.group(3)
        volume, number = values.group(1), values.group(2)
        page_start, page_end = values.group(4), values.group(5)
        doi = values.group(6)
    eid = ""
    if 'þÿ' in title:
        title_list = title.split('þÿ')[1].split('\x00')
        title = ''
        for char in title_list:
            title = title + char
    authors = author.split(' and ')

if 'Lingua' in subject:
    journaltitle = "Lingua"
    shortjournaltitle = "Lingua"
    values = re.search('Lingua (\d{1,3}) \((\d{4})\) (\d{1,4})–(\d{1,4})', journalinfo[0])
    volume = values.group(1)
    number = ""
    year = values.group(2)
    page_start = values.group(3)
    page_end = values.group(4)
    doi = get_doi_from_text(journalinfo)
    eid = ""
    title = journalinfo[4]
    author = re.sub('(\*)|(\d)', '', journalinfo[6])
    authors = author.split(', ')

if 'Linguistic Inquiry' in subject:
    # LI is messy: we're looking directly at the text of the first page,
    # reading it in as a list of strings.
    li_text = extract_text(filename, maxpages=1).split('\n')
    li_info = li_text[0:10] + li_text[-9:-2]
    # Get the item which includes "Linguistic Inquiry"
    info = li_info[[li_info.index(x) for x in li_info if 'Linguistic Inquiry' in x][0]]
    values = re.search('.+?(\d{1,2}).+?(\d{1,2}).+?(\d{4})', info)
    volume = values.group(1)
    number = values.group(2)
    year = values.group(3)
    journaltitle = "Linguistic Inquiry"
    shortjournaltitle = "LI"
    # The page numbers are one item further than info
    pages = li_info[[li_info.index(x) for x in li_info if 'Linguistic Inquiry' in x][0]+1]
    page_start, page_end = re.search('(\d{1,3})(–|-)(.*)', pages).group(1), re.search('(\d{1,3})(–|-)(.*)', pages).group(3)
    if 'Remarks' in li_info[0]:
        li_info = li_info[li_info.index('')+1:]
    title = ' '.join(li_info[0:li_info.index('')])
    authors = li_info[li_info.index('')+1:]
    authors = authors[:authors.index('')]
    doi = get_doi_from_text(li_text)
    eid = ""

if "Linguistic Typology 2" in subject:
    journaltitle = "Linguistic Typology"
    shortjournaltitle = "Linguistic Typology"
    tag_empty_items(journalinfo)
    title = ' '.join(journalinfo[journalinfo.index('1')+2:journalinfo.index('2')])
    values = re.search('Linguistic Typology (\d{4}); (\d{1,2})\((\d{1})\): (\d{1,4})–(\d{1,4})', subject)
    volume, number, year = values.group(2), values.group(3), values.group(1)
    page_start, page_end = values.group(4), values.group(5)
    eid = ""
    doi = get_doi_from_text(journalinfo)
    author = re.sub('\*', '', journalinfo[journalinfo.index('1')+1])
    authors = author.split(' and ')

if 'Nat Lang Ling' in subject:
    # NLLT
    journaltitle = "Natural Language \& Linguistic Theory"
    shortjournaltitle = "NLLT"
    if 'doi' in doc.info[0]:
        doi = doc.info[0]['doi'].decode('UTF-8')
    else:
        doi = get_doi_from_text(journalinfo)
    info = extract_text(filename, maxpages=1).split('\n')[:10]
    nllt = re.search('.+?\((\d{4})\) (\d{1,2}):( |)(\d{1,4})(–|\^)(\d{1,4})', info[0])
    year = nllt.group(1)
    volume = nllt.group(2)
    number = ""
    if title == "":
        title = info[[info.index(x) for x in info if 'Received' in x][0]-4].strip(' ')
    eid = ""
    page_start = nllt.group(4)
    page_end = nllt.group(6)
    author = info[[info.index(x) for x in info if 'Received' in x][0]-2]
    author = re.sub('\d', '', author)
    author = re.sub('¸s', 'ş', author)
    authors = author.split(' · ')

if 'Nat Lang Semantics' in subject:
    # NLLT
    journaltitle = "Natural Language Semantics"
    shortjournaltitle = "Nat Lang Semantics"
    if 'doi' in doc.info[0]:
        doi = doc.info[0]['doi'].decode('UTF-8')
    else:
        doi = get_doi_from_text(journalinfo)
    info = extract_text(filename, maxpages=1).split('\n')[:10]
    nllt = re.search('.+?\((\d{4})\) (\d{1,2}):( |)(\d{1,4})(–|\^)(\d{1,4})', info[0])
    year = nllt.group(1)
    volume = nllt.group(2)
    number = ""
    if title == "":
        title = info[info.index('')+1:]
        title = ' '.join(title[:title.index('')])
    eid = ""
    page_start = nllt.group(4)
    page_end = nllt.group(6)
    author = info[info.index('')+1:]
    author = author[author.index('')+1:]
    author = author[:author.index('')][0]
    author = re.sub('\d', '', author)
    author = re.sub('¸s', 'ş', author)
    author = re.sub('a´', 'á', author)
    authors = author.split(' · ')

if 'Syntax' in subject:
    # Syntax
    journaltitle = "Syntax"
    shortjournaltitle = "Syntax"
    syntax = extract_text(filename, maxpages=1).split('\n')
    syntax_info = syntax[:[syntax.index(x) for x in syntax if 'Abstract' in x][0]]
    # syntax_info: ['Name Volume:Number, Month Year, PageFirst–PageLast', '', 'TITLE', 'Author(s)', '']
    author = syntax_info[-2]
    if 'þÿ' in title:
                title_list = title.split('þÿ')[1].split('\x00')
                title = ''
                for char in title_list:
                    title = title + char
    values = re.search('.+? (\d{1,2}):(\d{1}).+?(\d{4}), (\d{1,4})–(\d{1,4})',
            syntax_info[0])
    volume, number, year = values.group(1), values.group(2), values.group(3)
    page_start, page_end = values.group(4), values.group(5)
    if 'WPS-ARTICLEDOI' in doc.info[0]:
        doi = doc.info[0]['WPS-ARTICLEDOI'].decode('UTF-8')
    else:
        doi = ""
    eid = ""
    authors = authors.split(' and ')

if "The Linguistic Review" in subject:
    # TLR
    journaltitle = "The Linguistic Review"
    shortjournaltitle = "TLR"
    author = journalinfo[journalinfo.index('')+1:journalinfo.index('Abstract')-1]
    title = ' '.join(journalinfo[:journalinfo.index('')])
    values = re.search('The Linguistic Review (\d{1,2}) \((\d{4})\), (\d{1,4})–(\d{1,4})',
            journalinfo[-7])
    volume, year = values.group(1), values.group(2)
    number = ''
    page_start, page_end = values.group(3), values.group(4)
    doi = get_doi_from_text(journalinfo)
    eid = ""
    if len(author) > 1:
        authors = author[0].split(', ') + [author[1]]
        authors = [re.sub(' AND', '', auth) for auth in authors]
        authors = [re.sub(' and', '', auth) for auth in authors]
    elif type(author) == list:
        authors = author[0].split(' AND ')
        authors = author[0].split(' and ')
    else:
        authors = author.split(' AND ')
        authors = author.split(' and ')

if "Theoretical Linguistics" in subject:
    journaltitle = "Theoretical Linguistics"
    shortjournaltitle = "Theoretical Linguistics"
    title = journalinfo[journalinfo.index(subject)+3]
    values = re.search('Theoretical Linguistics (\d{4}); (\d{1,2})\((\d{1}–\d{1})\): (\d{1,4}) – (\d{1,4})', subject)
    volume, number, year = values.group(2), values.group(3), values.group(1)
    page_start, page_end = values.group(4), values.group(5)
    eid = ""
    doi = get_doi_from_text(journalinfo)
    author = re.sub('\*', '', journalinfo[journalinfo.index(subject)+2])
    authors = author.split(' and ')

title = re.sub(' \x10', '-', title)
subtitle = ''
if ': ' in title:
    subtitle = title.split(': ')[1].capitalize()
    title = title.split(':')[0]
if '_' in title:
    subtitle = title.split('_ ')[1]
    title = title.split('_')[0]

citekey = ''
names_file = ''
names_full = ''
def pad(name):
    """Add a space if name is a non-empty string."""
    if name != '':
        return ' ' + name
    else:
        return ''

def name_authors(author_list):
    """Create list of authors separated by ',' and 'and'."""
    if len(author_list) > 1:
        citekey = ''
        names_file = ''
        names_full = ''
        for author in author_list:
            citekey = citekey + HumanName(author).last.title().replace(' ', '')
        for i in range(len(author_list)-1):
            names_file = names_file + HumanName(author_list[i]).last.title() + ', '
            names_full = names_full + HumanName(author_list[i]).last.title() + ', ' + \
                    HumanName(author_list[i]).first.title() + pad(HumanName(author_list[i]).middle) + ' and '
        names_file = names_file + HumanName(author_list[-1]).last.title()
        names_full = names_full + HumanName(author_list[-1]).last.title() + ', ' + \
                HumanName(author_list[-1]).first.title() + pad(HumanName(author_list[-1]).middle)
    else:
        author = HumanName(author_list[0])
        citekey = author.last.title()
        names_file = author.last.title()
        names_full = author.last.title() + ", " + author.first.title() + pad(author.middle)

    return [citekey, names_file, names_full]

def write_bibentry():
    entry = "@article{" + name_authors(authors)[0] + year + ",\n" \
            + "    author = {" + name_authors(authors)[2] + "},\n" \
            + "    title = {" + title + "},\n" \
            + "    subtitle = {" + subtitle + "},\n" \
            + "    year = {" + year + "},\n" \
            + "    journaltitle = {" + journaltitle + "},\n" \
            + "    shortjournaltitle = {" + shortjournaltitle + "},\n" \
            + "    volume = {" + volume + "},\n" \
            + "    number = {" + number + "},\n" \
            + "    pages = {" + page_start + "--" + page_end + "},\n" \
            + "    doi = {" + doi + "},\n" \
            + "    eid = {" + eid + "},\n" \
            + "}"

    print(entry)

if vars(args)['copy']:
    print("We're looking at", "“" + title + "”", "by", name_authors(authors)[1], "from", year,
        "in", shortjournaltitle + ".\n")
    # rename file
    print("Okay, renaming file to (keeping original):", name_authors(authors)[1] + " (" + year + ")" + " - " + title + ".pdf\n")
    subprocess.run(['cp', filename, name_authors(authors)[1] + ' (' + year + ')' + ' - ' + title + '.pdf'])

if vars(args)['rename']:
    print("We're looking at", "“" + title + "”", "by", name_authors(authors)[1], "from", year,
        "in", shortjournaltitle + ".\n")
    # rename file
    print("Okay, renaming file to:", name_authors(authors)[1] + " (" + year + ")" + " - " + title + ".pdf\n")
    subprocess.run(['mv', filename, name_authors(authors)[1] + ' (' + year + ')' + ' - ' + title + '.pdf'])

if vars(args)['biblatex']:
    # write biblatex entry
    write_bibentry()
