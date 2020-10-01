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
#parser.add_argument('filename', metavar='filename', type=str,
#                    help='PDF to rename')
parser.add_argument('filename', nargs='*', metavar='filename', type=str,
                    help='PDF to rename')
parser.add_argument('--rename', action='store_true',
                    help='rename PDF file')
parser.add_argument('--biblatex', action='store_true',
                    help='create biblatex entry')
parser.add_argument('--li', action='store_true',
                    help='rename a PDF from Linguistic Inquiry')

args = parser.parse_args()

filenames = vars(args)['filename']

def write_bibentry(st=0):
    if st == 1:
        entry = "@article{" + citekey + year + ",\n" \
                + "    author = {" + names_full + "},\n" \
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
    else:
        entry = "@article{" + citekey + year + ",\n" \
                + "    author = {" + names_full + "},\n" \
                + "    title = {" + title + "},\n" \
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

for filename in filenames:
    with open(filename, 'rb') as f:
        parse = PDFParser(f)
        doc = PDFDocument(parse)

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
        if len(authors) > 1:
            author1 = HumanName(authors[0])
            author2 = HumanName(authors[1])
            citekey = ''
            names_file = ''
            names_full = ''
            for author in authors:
                citekey = citekey + HumanName(author).last.replace(' ', '')
            for i in range(len(authors)-1):
                names_file = names_file + HumanName(authors[i]).last + ' and '
                names_full = names_full + HumanName(authors[i]).last + ', ' + HumanName(authors[i]).first + ' and '
            names_file = names_file + HumanName(authors[-1]).last
            names_full = names_full + HumanName(authors[-1]).last + ', ' + HumanName(authors[-1]).first
        else:
            author = HumanName(authors[0])
            citekey = author.last
            names_file = author.last
            names_full = author.last + ", " + author.first
        doi = re.search('(10.*)', li_info[-1]).group(1)
        eid = ""
    else:
        title = doc.info[0]['Title'].decode('ISO-8859-1')
        subject = re.sub(b'\\x85', b'-', doc.info[0]['Subject']).decode('ISO-8859-1')
        if 'Nat Lang' in subject:
            author = HumanName(doc.info[0]['Author'].decode('ISO-8859-1'))
            # NLLT
            journaltitle = "Natural Language & Linguistic Theory"
            shortjournaltitle = "NLLT"
            doi = doc.info[0]['doi'].decode('UTF-8')
            info = extract_text(filename, maxpages=1).split('\n')[:6]
            nllt = re.search('.+?\((\d{4})\) (\d{1,2}):(\d{1,4})–(\d{1,4})', info[0])
            year = nllt.group(1)
            volume = nllt.group(2)
            number = ""
            eid = ""
            page_start = nllt.group(3)
            page_end = nllt.group(4)
            author = info[5]
            if '·' in author:
                author1 = HumanName(re.search('([A-Za-z].+?)(\d| ·)', author).group(1))
                author2 = HumanName(re.search('· (.+?)(\d)', author).group(1))
                citekey = author1.last + author2.last
                names_file = author1.last + " and " + author2.last
                names_full = author1.last + ", " + author1.first + " and " + author2.last + ", " + author2.first
            else:
                author = HumanName(author)
                citekey = author.last
                names_file = author.last
                names_full = author.last

        if 'Glossa' in subject:
            # Glossa
            author = HumanName(doc.info[0]['Author'].decode('ISO-8859-1'))
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
            author = doc.info[0]['Author'].decode('ISO-8859-1')
            if ' and ' in author:
                author1 = HumanName(re.search('([A-Za-z].+?) and', author).group(1))
                author2 = HumanName(re.search('and (.*)', author).group(1))
                citekey = author1.last + author2.last
                names_file = author1.last + " and " + author2.last
                names_full = author1.last + ", " + author1.first + " and " + author2.last + ", " + author2.first
            else:
                author = HumanName(author)
                citekey = author.last
                names_file = author.last
                names_full = author.last + ", " + author.first

        if 'Syntax' in subject:
            # Syntax
            journaltitle = "Syntax"
            shortjournaltitle = "Syntax"
            syntax = extract_text(filename, maxpages=1).split('\n')
            syntax_info = syntax[:[syntax.index(x) for x in syntax if 'Abstract' in x][0]]
            # syntax_info: ['Name Volume:Number, Month Year, PageFirst–PageLast',
            # '', 'TITLE', 'Author(s)', '']
            author = syntax_info[-2]
            title_list = title.split('þÿ')[1].split('\x00')
            title = ''
            for char in title_list:
                title = title + char
            values = re.search('.+? (\d{1,2}):(\d{1}).+?(\d{4}), (\d{1,4})–(\d{1,4})',
                    syntax_info[0])
            volume, number, year = values.group(1), values.group(2), values.group(3)
            page_start, page_end = values.group(4), values.group(5)
            doi = doc.info[0]['WPS-ARTICLEDOI'].decode('UTF-8')
            eid = ""
            if ' and ' in author:
                author1 = HumanName(re.search('([A-Za-z].+?) and', author).group(1))
                author2 = HumanName(re.search('and (.*)', author).group(1))
                citekey = author1.last + author2.last
                names_file = author1.last + " and " + author2.last
                names_full = author1.last + ", " + author1.first + " and " + author2.last + ", " + author2.first
            else:
                author = HumanName(author)
                citekey = author.last
                names_file = author.last
                names_full = author.last + ", " + author.first

    title = re.sub(' \x10', '-', title)
    subtitle = None
    if ':' in title:
        subtitle = title.split(': ')[1]
        title = title.split(':')[0]

    print("We're looking at", "“" + title + "”", "by", names_file, "from", year,
            "in", shortjournaltitle + ".\n")

    if vars(args)['biblatex']:
        # write biblatex entry
        if subtitle:
            write_bibentry(st=1)
        else:
            write_bibentry(st=0)

    if vars(args)['rename']:
        # rename file
        print("Okay, renaming file to:", names_file + " (" + year + ")" + " - " + title + ".pdf\n")
        subprocess.run(['cp', filename, names_file + ' (' + year + ')' + ' - ' + title + '.pdf'])
