import os
import unittest
from datetime import timedelta
from youtubeanalyzer.model import (
    ResultTableModel,
    make_result_row
)
from youtubeanalyzer.export import (
    export_to_xlsx,
    export_to_csv,
    export_to_html
)


def create_test_model():
    result = []
    result.append(make_result_row("Video1", "8 hours ago", "00:34", 1234, "https://video1", "Channel1", "https://channel1",
                                  123, 12345, "2020-05-18", "https://preview1.jpg", "https://logo1.jpg",
                                  ["word1", "word2"], timedelta(seconds=34), 0, "shorts"))
    result.append(make_result_row("Video2", "9 hours ago", "00:35", 1235, "https://video2", "Channel2", "https://channel2",
                                  124, 12346, "2020-05-19", "https://preview2.jpg", "https://logo2.jpg",
                                  ["word2", "word3"], timedelta(seconds=35), 1, "shorts"))
    result.append(make_result_row("Video3", "10 hours ago", "00:36", 1236, "https://video3", "Channel3", "https://channel3",
                                  125, 12347, "2020-05-20", "https://preview3.jpg", "https://logo3.jpg",
                                  ["word3", "word4"], timedelta(seconds=36), 2, "shorts"))
    model = ResultTableModel(None)
    model.setData(result)
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


if __name__ == "__main__":
    unittest.main()
