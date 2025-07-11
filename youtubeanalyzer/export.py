import xlsxwriter
import csv
from youtubeanalyzer.model import (
    ResultFields,
    ResultTableModel
)


def exception_column(column: ResultFields):
    if (column == ResultFields.ChannelViews or
            column == ResultFields.ChannelJoinedDate or
            column == ResultFields.VideoDurationTimedelta or
            column == ResultFields.VideoPreviewLink or
            column == ResultFields.ChannelLogoLink or
            column == ResultFields.VideoTags or
            column == ResultFields.VideoPreviewImage or
            column == ResultFields.VideoType):
        return True
    else:
        return False


def export_to_xlsx(file_path: str, model: ResultTableModel):
    workbook = xlsxwriter.Workbook(file_path)
    worksheet = workbook.add_worksheet()
    index = 0
    for column in range(ResultFields.MaxFieldsCount):
        if not exception_column(column):
            worksheet.write(0, index, model.FieldNames[column])
            index = index + 1

    for row in range(model.rowCount()):
        index = 0
        for column in range(ResultFields.MaxFieldsCount):
            if not exception_column(column):
                worksheet.write(row + 1, index, model.get_field_data(row, column))
                index = index + 1

    worksheet.autofit()
    workbook.close()


def export_to_csv(file_path: str, model: ResultTableModel):
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')

        header_csv = []
        for column in range(ResultFields.MaxFieldsCount):
            if not exception_column(column):
                header_csv.append(model.FieldNames[column])
        csv_writer.writerow(header_csv)

        result_csv = []
        for row in range(model.rowCount()):
            for column in range(ResultFields.MaxFieldsCount):
                if not exception_column(column):
                    result_csv.append(model.get_field_data(row, column))
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
    for column in range(ResultFields.MaxFieldsCount):
        if not exception_column(column):
            result_doc += th_o + str(model.FieldNames[column]) + th_c
    result_doc += tr_c
    for row in range(model.rowCount()):
        result_doc += tr_o
        for column in range(ResultFields.MaxFieldsCount):
            if not exception_column(column):
                result_doc += td_o + str(model.get_field_data(row, column)) + td_c
        result_doc += tr_c
    result_doc += table_c + body_c + html_c
    with open(file_path, 'w', encoding='utf-8') as htmlfile:
        htmlfile.write(result_doc)
        htmlfile.close()
