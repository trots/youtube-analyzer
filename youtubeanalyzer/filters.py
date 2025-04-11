from datetime import (
    datetime,
    timedelta
)
from PySide6.QtCore import (
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
    ResultFields,
    ResultTableModel
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

    def filterAcceptsRow(self, source_row, source_parent):
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


class AbstractFilterWidget(QWidget, AbstractFilter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self._clear_button = QToolButton()
        self._clear_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton))
        self._clear_button.setAutoRaise(True)
        self.layout().addWidget(self._clear_button)

    def _set_control(self, control_widget):
        self.layout().insertWidget(0, control_widget)


class PublishedDateFilterWidget(AbstractFilterWidget):
    LastDay = 0
    LastWeek = 1
    LastMonth = 2
    LastHalfYear = 3
    LastYear = 4
    LastTwoYears = 5
    LastThreeYears = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self._published_date_filter_combo = QComboBox()
        self._published_date_filter_combo.setPlaceholderText(self.tr("Any published time"))
        self._published_date_filter_combo.addItem(self.tr("Last day"))
        self._published_date_filter_combo.addItem(self.tr("Last week"))
        self._published_date_filter_combo.addItem(self.tr("Last month"))
        self._published_date_filter_combo.addItem(self.tr("Last 6 months"))
        self._published_date_filter_combo.addItem(self.tr("Last year"))
        self._published_date_filter_combo.addItem(self.tr("Last 2 years"))
        self._published_date_filter_combo.addItem(self.tr("Last 3 years"))
        self._published_date_filter_combo.currentIndexChanged.connect(self._on_current_index_changed)
        self._set_control(self._published_date_filter_combo)
        self._clear_button.clicked.connect(lambda: self._published_date_filter_combo.setCurrentIndex(-1))

    def filter_accepts_row(self, source_row, source_parent):
        filter_type = self._published_date_filter_combo.currentIndex()
        if filter_type < 0:
            return True

        source_model: ResultTableModel = self._model.sourceModel()
        published_date_str = source_model.get_field_data(source_row, ResultFields.VideoPublishedTime)
        published_date = datetime.strptime(published_date_str, "%Y-%m-%d %H:%M:%S")
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

    def _on_current_index_changed(self, _):
        self._model.invalidateFilter()


class FiltersPanel(QGroupBox):
    def __init__(self, model: ResultSortFilterProxyModel, parent=None):
        super().__init__(parent)
        filters_layout = QHBoxLayout()

        publised_date_filter = PublishedDateFilterWidget()
        model.add_filter(publised_date_filter)
        filters_layout.addWidget(publised_date_filter)
        filters_layout.addStretch()
        self.setLayout(filters_layout)
