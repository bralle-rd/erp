
import base64
from io import BytesIO, StringIO, TextIOWrapper
import csv

def _read_csv_attachment(attachment):
    decoded_datas = base64.decodebytes(attachment)
    encoding = "utf-8"
    f = TextIOWrapper(BytesIO(decoded_datas), encoding=encoding)
    reader = csv.reader(f, delimiter=',', quotechar='"')
    fields = next(reader)
    data = [row for row in reader]
    return fields, data

def _short_unique_array (array):
        result = []
        for item in array:
            if item not in result:
                result.append(item)
        return result