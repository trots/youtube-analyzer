import os
import shutil
import unittest
from youtubeanalyzer.settings import (
    Settings,
    SettingsKey,
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
        self.assertEqual(Settings.TabWorkspaceUid.key, "tab_workspace_uid")
        self.assertEqual(Settings.ActiveTabIndex.key, "active_tab_index")
        self.assertEqual(Settings.Version.key, "version")
        self.assertEqual(Settings.TrendsRegion.key, "trends_region")
        self.assertEqual(Settings.TrendsVideoCategoryId.key, "trends_video_category_id")
        self.assertEqual(Settings.RequestPageLimit.key, "request_page_limit")
        self.assertEqual(Settings.PublishedTimeFilter.key, "published_time_filter")
        self.assertEqual(Settings.ActiveToolPanelIndex.key, "active_tool_panel_index")
        self.assertEqual(Settings.VideoTableMode.key, "video_table_mode")
        self.assertEqual(Settings.PreviewScaleIndex.key, "preview_scale_index")

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

    def test_global_key_isolated_from_active_array_context(self):
        # Regression test for the bug fixed by SettingsKey.is_global: reading/writing a
        # global (non-array) key while begin_read_array/begin_write_array + set_array_index
        # is active on the same Settings object must still resolve to the top-level key,
        # not get nested under the currently active "main_tabs/<index>/" group.
        test_file = "test_settings_global_key_isolation.ini"
        if os.path.isfile(test_file):
            os.remove(test_file)
        settings = Settings("test", test_file)
        settings._impl.clear()
        settings._global_impl.clear()
        try:
            global_key = SettingsKey("test_global_key_isolation", "default", is_global=True)

            # Write the global key while a write-array context with an active index is open.
            settings.begin_write_array(Settings.MainTabsArray)
            settings.set_array_index(0)
            settings.set(global_key, "written_during_array")
            settings.end_array()

            self.assertEqual(settings.get(global_key), "written_during_array")

            # Reading it back while a read-array context with an active index is open must
            # also resolve to the top-level key, not silently fall back to the default.
            settings.begin_read_array(Settings.MainTabsArray)
            settings.set_array_index(0)
            value_during_read = settings.get(global_key)
            settings.end_array()

            self.assertEqual(value_during_read, "written_during_array")
        finally:
            if os.path.isfile(test_file):
                os.remove(test_file)

    @classmethod
    def tearDownClass(cls):
        os.remove("settings.ini")


if __name__ == "__main__":
    unittest.main()
