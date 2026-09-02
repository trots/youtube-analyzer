import csv
import os
import unittest
from datetime import timedelta
from youtubeanalyzer.model import (
    ResultFields,
    ResultTableModel,
    make_result_row
)
from youtubeanalyzer.export import (
    export_to_xlsx,
    export_to_csv,
    export_to_html,
    export_to_txt,
    get_exportable_columns
)


def create_test_model():
    result = []
    result.append(make_result_row("Video1", "8 hours ago", "00:34", 1234, "https://video1", "Channel1", "https://channel1",
                                  123, 12345, "2020-05-18", "https://preview1.jpg", "https://logo1.jpg",
                                  ["word1", "word2"], timedelta(seconds=34), 0, "shorts", []))
    result.append(make_result_row("Video2", "9 hours ago", "00:35", 1235, "https://video2", "Channel2", "https://channel2",
                                  124, 12346, "2020-05-19", "https://preview2.jpg", "https://logo2.jpg",
                                  ["word2", "word3"], timedelta(seconds=35), 1, "shorts", []))
    result.append(make_result_row("Video3", "10 hours ago", "00:36", 1236, "https://video3", "Channel3", "https://channel3",
                                  125, 12347, "2020-05-20", "https://preview3.jpg", "https://logo3.jpg",
                                  ["word3", "word4"], timedelta(seconds=36), 2, "shorts", []))
    model = ResultTableModel(None)
    model.set_data(result)
    return model


class TestExportModule(unittest.TestCase):

    def test_export_to_xlsx(self):
        file = "unit_test_file.xlsx"
        if os.path.isfile(file):
            os.remove(file)
        model = create_test_model()
        export_to_xlsx(file, model)
        self.assertGreater(os.path.getsize(file), 0)

    def test_export_to_csv(self):
        file = "unit_test_file.csv"
        if os.path.isfile(file):
            os.remove(file)
        model = create_test_model()
        export_to_csv(file, model)
        self.assertGreater(os.path.getsize(file), 0)

    def test_export_to_html(self):
        file = "unit_test_file.html"
        if os.path.isfile(file):
            os.remove(file)
        model = create_test_model()
        export_to_html(file, model)
        self.assertGreater(os.path.getsize(file), 0)

    def test_get_exportable_columns_matches_default_export_order(self):
        self.assertEqual(get_exportable_columns(), [
            ResultFields.VideoTitle,
            ResultFields.VideoPublishedTime,
            ResultFields.VideoDuration,
            ResultFields.VideoViews,
            ResultFields.VideoLink,
            ResultFields.ChannelTitle,
            ResultFields.ChannelLink,
            ResultFields.ChannelSubscribers,
            ResultFields.ViewRate,
            ResultFields.VideoRelevanceNumber,
        ])

    def test_export_to_csv_with_selected_columns_exports_only_subset(self):
        file = "unit_test_file_subset.csv"
        if os.path.isfile(file):
            os.remove(file)
        model = create_test_model()
        columns = [ResultFields.VideoTitle, ResultFields.VideoViews]

        export_to_csv(file, model, columns)

        with open(file, newline='', encoding='utf-8') as csvfile:
            rows = list(csv.reader(csvfile))
        self.assertEqual(rows[0], [model.FieldNames[ResultFields.VideoTitle], model.FieldNames[ResultFields.VideoViews]])
        self.assertEqual(rows[1], ["Video1", "1234"])
        self.assertEqual(rows[2], ["Video2", "1235"])
        self.assertEqual(rows[3], ["Video3", "1236"])
        os.remove(file)

    def test_export_to_txt(self):
        file = "unit_test_file.txt"
        if os.path.isfile(file):
            os.remove(file)
        model = create_test_model()
        export_to_txt(file, model)
        self.assertGreater(os.path.getsize(file), 0)
        os.remove(file)

    def test_export_to_txt_with_selected_columns_and_default_delimiter(self):
        file = "unit_test_file_subset.txt"
        if os.path.isfile(file):
            os.remove(file)
        model = create_test_model()
        columns = [ResultFields.VideoTitle, ResultFields.VideoViews]

        export_to_txt(file, model, columns)

        with open(file, encoding='utf-8') as txtfile:
            lines = txtfile.read().splitlines()
        self.assertEqual(lines[0], f"{model.FieldNames[ResultFields.VideoTitle]} {model.FieldNames[ResultFields.VideoViews]}")
        self.assertEqual(lines[1], "Video1 1234")
        self.assertEqual(lines[2], "Video2 1235")
        self.assertEqual(lines[3], "Video3 1236")
        os.remove(file)

    def test_export_to_txt_with_custom_delimiter(self):
        file = "unit_test_file_delimiter.txt"
        if os.path.isfile(file):
            os.remove(file)
        model = create_test_model()
        columns = [ResultFields.VideoTitle, ResultFields.VideoViews]

        export_to_txt(file, model, columns, delimiter="|")

        with open(file, encoding='utf-8') as txtfile:
            lines = txtfile.read().splitlines()
        self.assertEqual(lines[1], "Video1|1234")
        os.remove(file)

    def test_export_to_txt_does_not_escape_values_containing_the_delimiter(self):
        file = "unit_test_file_no_escaping.txt"
        if os.path.isfile(file):
            os.remove(file)
        result = [make_result_row("Video One", "8 hours ago", "00:34", 1234, "https://video1", "Channel1",
                                   "https://channel1", 123, 12345, "2020-05-18", "https://preview1.jpg",
                                   "https://logo1.jpg", ["word1"], timedelta(seconds=34), 0, "shorts", [])]
        model = ResultTableModel(None)
        model.set_data(result)
        columns = [ResultFields.VideoTitle, ResultFields.VideoViews]

        export_to_txt(file, model, columns, delimiter=" ")

        with open(file, encoding='utf-8') as txtfile:
            lines = txtfile.read().splitlines()
        # The title contains the delimiter itself and is neither quoted nor escaped.
        self.assertEqual(lines[1], "Video One 1234")
        os.remove(file)

    def test_export_to_txt_with_empty_delimiter_concatenates_columns(self):
        file = "unit_test_file_empty_delimiter.txt"
        if os.path.isfile(file):
            os.remove(file)
        model = create_test_model()
        columns = [ResultFields.VideoTitle, ResultFields.VideoViews]

        export_to_txt(file, model, columns, delimiter="")

        with open(file, encoding='utf-8') as txtfile:
            lines = txtfile.read().splitlines()
        self.assertEqual(lines[1], "Video11234")
        os.remove(file)

    def test_export_to_xlsx_with_header_excluded_omits_header_row(self):
        file_with_header = "unit_test_file_header.xlsx"
        file_without_header = "unit_test_file_no_header.xlsx"
        for file in (file_with_header, file_without_header):
            if os.path.isfile(file):
                os.remove(file)
        model = create_test_model()

        export_to_xlsx(file_with_header, model)
        export_to_xlsx(file_without_header, model, include_header=False)

        self.assertGreater(os.path.getsize(file_with_header), os.path.getsize(file_without_header))
        os.remove(file_with_header)
        os.remove(file_without_header)

    def test_export_to_csv_with_header_excluded_omits_header_row(self):
        file = "unit_test_file_no_header.csv"
        if os.path.isfile(file):
            os.remove(file)
        model = create_test_model()
        columns = [ResultFields.VideoTitle, ResultFields.VideoViews]

        export_to_csv(file, model, columns, include_header=False)

        with open(file, newline='', encoding='utf-8') as csvfile:
            rows = list(csv.reader(csvfile))
        self.assertEqual(rows[0], ["Video1", "1234"])
        self.assertEqual(len(rows), 3)
        os.remove(file)

    def test_export_to_html_with_header_excluded_omits_header_cells(self):
        file = "unit_test_file_no_header.html"
        if os.path.isfile(file):
            os.remove(file)
        model = create_test_model()

        export_to_html(file, model, include_header=False)

        with open(file, encoding='utf-8') as htmlfile:
            content = htmlfile.read()
        self.assertNotIn("<th>", content)
        os.remove(file)

    def test_export_to_txt_with_header_excluded_omits_header_line(self):
        file = "unit_test_file_no_header.txt"
        if os.path.isfile(file):
            os.remove(file)
        model = create_test_model()
        columns = [ResultFields.VideoTitle, ResultFields.VideoViews]

        export_to_txt(file, model, columns, include_header=False)

        with open(file, encoding='utf-8') as txtfile:
            lines = txtfile.read().splitlines()
        self.assertEqual(lines[0], "Video1 1234")
        self.assertEqual(len(lines), 3)
        os.remove(file)

    def test_export_functions_default_to_including_header_for_backward_compatibility(self):
        file = "unit_test_file_default_header.csv"
        if os.path.isfile(file):
            os.remove(file)
        model = create_test_model()
        columns = [ResultFields.VideoTitle, ResultFields.VideoViews]

        export_to_csv(file, model, columns)

        with open(file, newline='', encoding='utf-8') as csvfile:
            rows = list(csv.reader(csvfile))
        self.assertEqual(rows[0], [model.FieldNames[ResultFields.VideoTitle], model.FieldNames[ResultFields.VideoViews]])
        os.remove(file)


if __name__ == "__main__":
    unittest.main()
