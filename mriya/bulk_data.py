
__author__ = "Yaroslav Litvinov"
__copyright__ = "Copyright 2016, Rackspace Inc."
__email__ = "yaroslav.litvinov@rackspace.com"

from StringIO import StringIO
from opcsv import CsvWriter
from opcsv import CsvReader
from collections import namedtuple

BulkData = namedtuple('BulkData', ['fields', 'rows'])

def csv_from_list_of_dicts(list_of_dicts_data):
    output = StringIO()
    csv_writer = CsvWriter(output, False)
    txt = ''
    for name in sorted(list_of_dicts_data[0].keys()):
        if txt:
            txt += ','
        txt += name
    txt += '\n'
    rows = []
    for dict_data in list_of_dicts_data:
        row = []
        for key in sorted(dict_data.keys()):
            row.append(dict_data[key])
        rows.append(row)
    csv_writer.write_csv(rows)
    output.seek(0)
    txt += output.getvalue()
    output.close()
    csv_writer.close()
    return txt

def csv_from_bulk_data(bulk_data):
    output = StringIO()
    csv_writer = CsvWriter(output, False)
    txt = ''
    for name in bulk_data.fields:
        if txt:
            txt += ','
        txt += name
    txt += '\n'
    csv_writer.write_csv(bulk_data.rows)
    output.seek(0)
    txt += output.getvalue()
    output.close()
    csv_writer.close()
    return txt


def get_stream_from_csv_rows_list(csv_rows_list):
    istream = StringIO()
    # put data into stream for handling
    for csv_row in csv_rows_list:
        istream.write(csv_row)
        istream.write('\n')
    istream.seek(0)
    return istream

def get_bulk_data_from_csv_stream(istream):
    csv_reader = CsvReader(istream)
    fields = None
    rows = []
    while True:
        rec_tuple = csv_reader.read_record()
        if not rec_tuple:
            break
        if not fields:
            fields = rec_tuple
            rec_tuple = None
            continue
        row = []
        for row_item in rec_tuple:
            row.append(row_item)
        rows.append(tuple(row))
    csv_reader.close()
    return BulkData(fields, rows)


def parse_batch_res_data(csv_rows_list):
    istream = get_stream_from_csv_rows_list(csv_rows_list)
    return get_bulk_data_from_csv_stream(istream)