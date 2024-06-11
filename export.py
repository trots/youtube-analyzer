import xlsxwriter
import csv
from model import (
    ResultFields,
    ResultTableModel
)


def exception_column(column: ResultFields):
    if column == ResultFields.ChannelViews or column == ResultFields.ChannelJoinedDate:
        return True
    else:
        return False


def export_to_xlsx(file_path: str, model: ResultTableModel):
    workbook = xlsxwriter.Workbook(file_path)
    worksheet = workbook.add_worksheet()
    index = 0
    for column in range(len(model.header)):
        if not exception_column(column):
            worksheet.write(0, index, model.header[column])
            index = index + 1

    for row in range(len(model.result)):
        index = 0
        for column in range(len(model.header)):
            if not exception_column(column):
                worksheet.write(row + 1, index, model.result[row][column])
                index = index + 1

    worksheet.autofit()
    workbook.close()


def export_to_csv(file_path: str, model: ResultTableModel):
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')

        header_csv = []
        for column in range(len(model.header)):
            if not exception_column(column):
                header_csv.append(model.header[column])
        csv_writer.writerow(header_csv)

        result_csv = []
        for row in range(len(model.result)):
            for column in range(len(model.header)):
                if not exception_column(column):
                    result_csv.append(model.result[row][column])
            csv_writer.writerow(result_csv)
            result_csv.clear()


def export_to_html(file_path: str, model: ResultTableModel):
    html_o = "<html>"
    html_c = "</html>"
    body_o = "<body>"
    body_c = "</body>"
    table_o = "<table border=""1"">"
    table_c = "</table>"
    tr_o = "<tr>"
    tr_c = "</tr>"
    th_o = "<th>"
    th_c = "</th>"
    td_o = "<td>"
    td_c = "</td>"

    result_doc = html_o + body_o + table_o
    result_doc += tr_o
    for column in range(len(model.header)):
        if not exception_column(column):
            result_doc += th_o + str(model.header[column]) + th_c
    result_doc += tr_c
    for row in range(len(model.result)):
        result_doc += tr_o
        for column in range(len(model.header)):
            if not exception_column(column):
                result_doc += td_o + str(model.result[row][column]) + td_c
        result_doc += tr_c
    result_doc += table_c + body_c + html_c
    with open(file_path, 'w', encoding='utf-8') as htmlfile:
        htmlfile.write(result_doc)
        htmlfile.close()
