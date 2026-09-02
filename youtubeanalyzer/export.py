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
            column == ResultFields.VideoPreviewSizes or
            column == ResultFields.VideoType):
        return True
    else:
        return False


def get_exportable_columns() -> list[int]:
    return [column for column in range(ResultFields.MaxFieldsCount) if not exception_column(column)]


def export_to_xlsx(file_path: str, model: ResultTableModel, columns: list[int] = None, include_header: bool = True):
    if columns is None:
        columns = get_exportable_columns()
    workbook = xlsxwriter.Workbook(file_path)
    worksheet = workbook.add_worksheet()
    row_offset = 0
    if include_header:
        for index, column in enumerate(columns):
            worksheet.write(0, index, model.FieldNames[column])
        row_offset = 1

    for row in range(model.rowCount()):
        for index, column in enumerate(columns):
            worksheet.write(row + row_offset, index, model.get_field_data(row, column))

    worksheet.autofit()
    workbook.close()


def export_to_csv(file_path: str, model: ResultTableModel, columns: list[int] = None, include_header: bool = True):
    if columns is None:
        columns = get_exportable_columns()
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')

        if include_header:
            header_csv = [model.FieldNames[column] for column in columns]
            csv_writer.writerow(header_csv)

        result_csv = []
        for row in range(model.rowCount()):
            for column in columns:
                result_csv.append(model.get_field_data(row, column))
            csv_writer.writerow(result_csv)
            result_csv.clear()


def export_to_html(file_path: str, model: ResultTableModel, columns: list[int] = None, include_header: bool = True):
    if columns is None:
        columns = get_exportable_columns()
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
    if include_header:
        result_doc += tr_o
        for column in columns:
            result_doc += th_o + str(model.FieldNames[column]) + th_c
        result_doc += tr_c
    for row in range(model.rowCount()):
        result_doc += tr_o
        for column in columns:
            result_doc += td_o + str(model.get_field_data(row, column)) + td_c
        result_doc += tr_c
    result_doc += table_c + body_c + html_c
    with open(file_path, 'w', encoding='utf-8') as htmlfile:
        htmlfile.write(result_doc)
        htmlfile.close()


def export_to_txt(file_path: str, model: ResultTableModel, columns: list[int] = None, delimiter: str = " ",
                   include_header: bool = True):
    if columns is None:
        columns = get_exportable_columns()
    with open(file_path, 'w', encoding='utf-8') as txtfile:
        if include_header:
            txtfile.write(delimiter.join(str(model.FieldNames[column]) for column in columns) + "\n")

        for row in range(model.rowCount()):
            txtfile.write(delimiter.join(str(model.get_field_data(row, column)) for column in columns) + "\n")
