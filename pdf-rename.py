#!/usr/bin/python
# coding=utf8
import argparse
from nameparser import HumanName
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.high_level import extract_text
import re
import subprocess

parser = argparse.ArgumentParser(description='Rename PDFs automatically \
                                to include author(s), year, and title.')
parser.add_argument('filename', metavar='filename', type=str,
                    help='PDF to rename')
parser.add_argument('--rename', action='store_true',
                    help='rename PDF file')
parser.add_argument('--biblatex', action='store_true',
                    help='create biblatex entry')
parser.add_argument('--li', action='store_true',
                    help='rename a PDF from Linguistic Inquiry')

args = parser.parse_args()

filename = vars(args)['filename']

with open(filename, 'rb') as f:
    parse = PDFParser(f)
    doc = PDFDocument(parse)

journals = ['Lingua', 'Language']
def get_doi_from_text(text):
    doi = re.search('(10.*)', text[[text.index(x) for x in text if 'doi.org' in x or 'doi:' in x][0]]).group(1)
    return(doi)

if vars(args)["li"]:
    # LI is messy: we're looking directly at the text of the first page,
    # reading it in as a list of strings.
    li_text = extract_text(filename, maxpages=1).split('\n')
    li_info = li_text[0:10] + li_text[-9:-4]
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
    page_start = re.search('(\d.+?)–', pages).group(1)
    page_end = re.search('(\d.+?)–(.*)', pages).group(2)
    title = ' '.join(li_info[0:li_info.index('')])
    authors = li_info[li_info.index('')+1:]
    authors = authors[:authors.index('')]
    doi = re.search('(10.*)', li_info[-1]).group(1)
    eid = ""
else:
    if 'Author' in doc.info[0]:
        author = doc.info[0]['Author'].decode('ISO-8859-1')
    title = re.sub(b'\\x84', b'---', doc.info[0]['Title']).decode('ISO-8859-1')
    if 'Subject' in doc.info[0]:
        subject = re.sub(b'\\x85', b'-', doc.info[0]['Subject']).decode('ISO-8859-1')
    else:
        journalinfo = extract_text(filename, maxpages=1).split('\n')
        #subject = [journal for journal in journals if journal in [line for line in journalinfo if any(journal in line for journal in journals)][0]][0]
        subject = [line for line in journalinfo if any(journal in line for journal in journals)][0]

    if 'Glossa' in subject:
        # Glossa
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

    if "Language" in subject:
        journaltitle = "Language"
        shortjournaltitle = "Lg"
        lg_info = journalinfo[:10]
        values = re.search('.+? Volume (\d{1,3}), Number (\d{1}), June (\d{4}), pp. (\d{1,4})-(\d{1,4})',
                subject)
        volume, number, year = values.group(1), values.group(2), values.group(3)
        page_start, page_end = values.group(4), values.group(5)
        #doi = re.search('(10.*)', lg_info[[lg_info.index(x) for x in lg_info if 'doi.org' in x][0]]).group(1)
        doi = get_doi_from_text(lg_info)
        eid = ""
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

    if 'Nat Lang' in subject:
        # NLLT
        journaltitle = "Natural Language \& Linguistic Theory"
        shortjournaltitle = "NLLT"
        doi = doc.info[0]['doi'].decode('UTF-8')
        info = extract_text(filename, maxpages=1).split('\n')[:10]
        nllt = re.search('.+?\((\d{4})\) (\d{1,2}):(\d{1,4})–(\d{1,4})', info[0])
        year = nllt.group(1)
        volume = nllt.group(2)
        number = ""
        eid = ""
        page_start = nllt.group(3)
        page_end = nllt.group(4)
        author = info[[info.index(x) for x in info if 'Received' in x][0]-2]
        author = re.sub('\d', '', author)
        authors = author.split(' · ')

    if 'Syntax' in subject:
        # Syntax
        journaltitle = "Syntax"
        shortjournaltitle = "Syntax"
        syntax = extract_text(filename, maxpages=1).split('\n')
        syntax_info = syntax[:[syntax.index(x) for x in syntax if 'Abstract' in x][0]]
        # syntax_info: ['Name Volume:Number, Month Year, PageFirst–PageLast',
        # '', 'TITLE', 'Author(s)', '']
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
        authors = author.split(' and ')

title = re.sub(' \x10', '-', title)
subtitle = ''
if ':' in title:
    subtitle = title.split(': ')[1]
    title = title.split(':')[0]

citekey = ''
names_file = ''
names_full = ''
def name_authors(author_list):
    if len(author_list) > 1:
        citekey = ''
        names_file = ''
        names_full = ''
        for author in author_list:
            citekey = citekey + HumanName(author).last.replace(' ', '')
        for i in range(len(author_list)-1):
            names_file = names_file + HumanName(author_list[i]).last + ' and '
            names_full = names_full + HumanName(author_list[i]).last + ', ' + \
                    HumanName(author_list[i]).first + ' ' + HumanName(author_list[i]).middle + ' and '
        names_file = names_file + HumanName(author_list[-1]).last
        names_full = names_full + HumanName(author_list[-1]).last + ', ' + \
                HumanName(author_list[-1]).first + ' ' + HumanName(author_list[-1]).middle
    else:
        author = HumanName(author_list[0])
        citekey = author.last
        names_file = author.last
        names_full = author.last + ", " + author.first + ' ' + author.middle

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

print("We're looking at", "“" + title + "”", "by", name_authors(authors)[1], "from", year,
        "in", shortjournaltitle + ".\n")

if vars(args)['rename']:
    # rename file
    print("Okay, renaming file to:", name_authors(authors)[1] + " (" + year + ")" + " - " + title + ".pdf\n")
    subprocess.run(['cp', filename, name_authors(authors)[1] + ' (' + year + ')' + ' - ' + title + '.pdf'])

if vars(args)['biblatex']:
    # write biblatex entry
    write_bibentry()
