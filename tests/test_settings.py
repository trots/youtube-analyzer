import os
import shutil
import unittest
from youtubeanalyzer.settings import (
    Settings,
    CurrentSettingsVersion
)


class TestSettingsModule(unittest.TestCase):

    def test_settings_keys_persistance(self):
        self.assertEqual(Settings.MainWindowGeometry.key, "main_window_geometry")
        self.assertEqual(Settings.RequestLimit.key, "request_limit")
        self.assertEqual(Settings.LastSaveDir.key, "last_save_dir")
        self.assertEqual(Settings.DontAskAgainExit.key, "dont_ask_again_exit")
        self.assertEqual(Settings.YouTubeApiKey.key, "youtube_api_key")
        self.assertEqual(Settings.Language.key, "language")
        self.assertEqual(Settings.Theme.key, "theme")
        self.assertEqual(Settings.MainSplitterState.key, "main_splitter_state")
        self.assertEqual(Settings.DetailsVisible.key, "details")
        self.assertEqual(Settings.LastActiveDetailsTab.key, "last_active_details_tab")
        self.assertEqual(Settings.AnalyticsFollowTableSelect.key, "analytics_follow_table_select")
        self.assertEqual(Settings.LastActiveChartIndex.key, "last_active_chart_index")
        self.assertEqual(Settings.RequestTimeoutSec.key, "request_timeout_sec")
        self.assertEqual(Settings.MainTableHeaderState.key, "main_table_header_state")
        self.assertEqual(Settings.MainTabsArray.key, "main_tabs")
        self.assertEqual(Settings.TabWorkspaceIndex.key, "tab_workspace_index")
        self.assertEqual(Settings.ActiveTabIndex.key, "active_tab_index")
        self.assertEqual(Settings.Version.key, "version")
        self.assertEqual(Settings.TrendsRegion.key, "trends_region")
        self.assertEqual(Settings.TrendsVideoCategoryId.key, "trends_video_category_id")
        self.assertEqual(Settings.RequestPageLimit.key, "request_page_limit")
        self.assertEqual(Settings.FiltersVisible.key, "filters")
        self.assertEqual(Settings.PublishedTimeFilter.key, "published_time_filter")

    def test_upgrade_from_version_1(self):
        etalon_test_file = "tests/data/settings_version_1.ini"
        target_test_file = "settings.ini"
        shutil.copyfile(etalon_test_file, target_test_file)
        settings = Settings("test", target_test_file)
        # Check removed keys
        self.assertEqual(int(settings.get(Settings.RequestLimit)), 10)
        self.assertEqual(int(settings.get(Settings.LastActiveChartIndex)), 0)
        self.assertEqual(int(settings.get(Settings.LastActiveDetailsTab)), 0)
        self.assertTrue(settings.get(Settings.MainTableHeaderState).isEmpty())
        # Check main tab converting
        settings.begin_read_array(Settings.MainTabsArray)
        settings.set_array_index(0)
        self.assertEqual(int(settings.get(Settings.RequestLimit)), 30)
        self.assertEqual(int(settings.get(Settings.LastActiveChartIndex)), 2)
        self.assertEqual(int(settings.get(Settings.LastActiveDetailsTab)), 1)
        self.assertFalse(settings.get(Settings.MainTableHeaderState).isEmpty())
        settings.end_array()
        self.assertEqual(int(settings.get(Settings.ActiveTabIndex)), 0)
        # Check version
        self.assertEqual(int(settings.get(Settings.Version)), CurrentSettingsVersion)

    @classmethod
    def tearDownClass(cls):
        os.remove("settings.ini")


if __name__ == "__main__":
    unittest.main()
