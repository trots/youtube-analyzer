from datetime import (
    datetime,
    timedelta
)
from PySide6.QtCore import (
    QModelIndex,
    QSortFilterProxyModel
)
from PySide6.QtWidgets import (
    QWidget,
    QGroupBox,
    QToolButton,
    QComboBox,
    QStyle,
    QHBoxLayout
)
from youtubeanalyzer.model import (
    PublishedDateFormat,
    ResultFields,
    ResultTableModel
)
from youtubeanalyzer.settings import (
    Settings,
    StateSaveable
)


class AbstractFilter:
    def __init__(self):
        self._model = None

    def set_model(self, model: QSortFilterProxyModel):
        self._model = model

    def filter_accepts_row(self, source_row, source_parent):
        raise "AbstractFilter.filter_accepts_row not implemented"


class ResultSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filters: list[AbstractFilter] = []
        self.setSortRole(ResultTableModel.SortRole)

    def add_filter(self, filter: AbstractFilter):
        filter.set_model(self)
        self._filters.append(filter)
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        for filter in self._filters:
            if not filter.filter_accepts_row(source_row, source_parent):
                return False
        return super().filterAcceptsRow(source_row, source_parent)

    def has_data(self):
        return self.rowCount() > 0

    def get_field_data(self, proxy_row: int, result_field: ResultFields):
        if proxy_row is None or proxy_row < 0 or proxy_row >= self.rowCount():
            return None
        proxy_index = self.index(proxy_row, 0)
        source_index = self.mapToSource(proxy_index)
        return self.sourceModel().result[source_index.row()][result_field] if source_index else None


class AbstractFilterWidget(QWidget, AbstractFilter, StateSaveable):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self._reset_button = QToolButton()
        self._reset_button.setToolTip(self.tr("Reset the filter"))
        self._reset_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton))
        self._reset_button.setAutoRaise(True)
        self.layout().addWidget(self._reset_button)

    def _set_control(self, control_widget: QWidget):
        self.layout().insertWidget(0, control_widget)


class PublishedDateFilterWidget(AbstractFilterWidget):
    LastDay = "d"
    LastWeek = "w"
    LastMonth = "m"
    LastHalfYear = "hy"
    LastYear = "y"
    LastTwoYears = "y2"
    LastThreeYears = "y3"

    def __init__(self, settings: Settings, parent=None):
        super().__init__(settings, parent)
        self._published_date_filter_combo = QComboBox()
        self._published_date_filter_combo.setToolTip(self.tr("Select table filtering by video publication time"))
        self._published_date_filter_combo.setPlaceholderText(self.tr("Any published time"))
        self._published_date_filter_combo.addItem(self.tr("Last day"), PublishedDateFilterWidget.LastDay)
        self._published_date_filter_combo.addItem(self.tr("Last week"), PublishedDateFilterWidget.LastWeek)
        self._published_date_filter_combo.addItem(self.tr("Last month"), PublishedDateFilterWidget.LastMonth)
        self._published_date_filter_combo.addItem(self.tr("Last 6 months"), PublishedDateFilterWidget.LastHalfYear)
        self._published_date_filter_combo.addItem(self.tr("Last year"), PublishedDateFilterWidget.LastYear)
        self._published_date_filter_combo.addItem(self.tr("Last 2 years"), PublishedDateFilterWidget.LastTwoYears)
        self._published_date_filter_combo.addItem(self.tr("Last 3 years"), PublishedDateFilterWidget.LastThreeYears)
        self._published_date_filter_combo.currentIndexChanged.connect(self._on_current_index_changed)
        self._set_control(self._published_date_filter_combo)
        self._reset_button.clicked.connect(lambda: self._published_date_filter_combo.setCurrentIndex(-1))

    def filter_accepts_row(self, source_row: int, source_parent: QModelIndex):
        filter_type = self._published_date_filter_combo.currentData()
        if not filter_type:
            return True

        source_model: ResultTableModel = self._model.sourceModel()
        published_date_str = source_model.get_field_data(source_row, ResultFields.VideoPublishedTime)
        if not published_date_str:
            return True

        published_date = datetime.strptime(published_date_str, PublishedDateFormat)
        if filter_type == PublishedDateFilterWidget.LastDay:
            past_date = datetime.now() - timedelta(days=1)
        elif filter_type == PublishedDateFilterWidget.LastWeek:
            past_date = datetime.now() - timedelta(days=7)
        elif filter_type == PublishedDateFilterWidget.LastMonth:
            past_date = datetime.now() - timedelta(days=30)
        elif filter_type == PublishedDateFilterWidget.LastHalfYear:
            past_date = datetime.now() - timedelta(days=180)
        elif filter_type == PublishedDateFilterWidget.LastYear:
            past_date = datetime.now() - timedelta(days=365)
        elif filter_type == PublishedDateFilterWidget.LastTwoYears:
            past_date = datetime.now() - timedelta(days=730)
        else:
            past_date = datetime.now() - timedelta(days=1095)
        return published_date > past_date

    def load_state(self):
        index = self._published_date_filter_combo.findData(self._settings.get(Settings.PublishedTimeFilter))
        self._published_date_filter_combo.setCurrentIndex(index)

    def save_state(self):
        self._settings.set(Settings.PublishedTimeFilter, self._published_date_filter_combo.currentData())

    def _on_current_index_changed(self, _):
        self._model.invalidateFilter()


class FiltersPanel(QGroupBox, StateSaveable):
    def __init__(self, settings: Settings, model: ResultSortFilterProxyModel, parent=None):
        super().__init__(parent)
        self._filter_widgets: list[AbstractFilterWidget] = []

        filters_layout = QHBoxLayout()

        publised_date_filter = PublishedDateFilterWidget(settings)
        model.add_filter(publised_date_filter)
        filters_layout.addWidget(publised_date_filter)
        self._filter_widgets.append(publised_date_filter)

        filters_layout.addStretch()
        self.setLayout(filters_layout)

    def load_state(self):
        for filter_widget in self._filter_widgets:
            filter_widget.load_state()

    def save_state(self):
        for filter_widget in self._filter_widgets:
            filter_widget.save_state()
