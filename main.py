# main.py (PyQt6)
# Запуск:  py main.py
# Требуется: PyQt6
#
# Ожидается, что у тебя есть service.py (или functions.py) с функциями:
#   create_entry(valence, arousal, energy, social, note, emotions, factors) -> entry_id
#   get_recent_entries() -> list[tuple]  (id, ts, valence, arousal, energy, social)
#   get_entry_details(entry_id) -> dict  {"entry": {...}, "emotions": [...], "factors": [...]}
#
# Если файл называется иначе (functions.py) — поменяй импорт ниже.

import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QSpinBox, QPlainTextEdit, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit
)

# --- твой сервис ---
from service import create_entry, get_recent_entries, get_entry_details  # поменяй на functions, если надо

# Чтобы подгружать справочники (emotions/factors) без дополнительных сервис-функций:
from mood_db import init_db, get_conn


def fetch_tag_names(table_name: str) -> list[str]:
    """Достаёт список name из emotions/factors."""
    con, cur = get_conn()
    try:
        cur.execute(f"SELECT name FROM {table_name} ORDER BY name;")
        return [r[0] for r in cur.fetchall()]
    finally:
        con.close()


class AddEntryTab(QWidget):
    def __init__(self, on_saved_callback):
        super().__init__()
        self.on_saved_callback = on_saved_callback
        self._build_ui()
        self.reload_tag_lists()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # --- Верх: поля ---
        form = QGridLayout()
        row = 0

        self.valence = QSpinBox()
        self.valence.setRange(-5, 5)
        self.valence.setValue(0)
        form.addWidget(QLabel("Valence (-5..5)"), row, 0)
        form.addWidget(self.valence, row, 1)

        self.arousal = QSpinBox()
        self.arousal.setRange(0, 5)
        self.arousal.setValue(2)
        form.addWidget(QLabel("Arousal (0..5)"), row, 2)
        form.addWidget(self.arousal, row, 3)
        row += 1

        self.energy = QSpinBox()
        self.energy.setRange(0, 5)
        self.energy.setValue(2)
        form.addWidget(QLabel("Energy (0..5)"), row, 0)
        form.addWidget(self.energy, row, 1)

        self.social = QSpinBox()
        self.social.setRange(0, 5)
        self.social.setValue(2)
        form.addWidget(QLabel("Social (0..5)"), row, 2)
        form.addWidget(self.social, row, 3)
        row += 1

        self.note = QPlainTextEdit()
        self.note.setPlaceholderText("Заметка (необязательно)")
        form.addWidget(QLabel("Note"), row, 0, 1, 4)
        row += 1
        form.addWidget(self.note, row, 0, 1, 4)
        row += 1

        root.addLayout(form)

        # --- Списки тегов ---
        lists = QHBoxLayout()

        emo_box = QVBoxLayout()
        emo_box.addWidget(QLabel("Эмоции (multi-select)"))
        self.emotions_list = QListWidget()
        self.emotions_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        emo_box.addWidget(self.emotions_list)

        # "Другое" для эмоций
        self.emotion_other = QLineEdit()
        self.emotion_other.setPlaceholderText("Другое (эмоции), через ; например: ком в груди; пустота")
        emo_box.addWidget(self.emotion_other)

        fac_box = QVBoxLayout()
        fac_box.addWidget(QLabel("Факторы (multi-select)"))
        self.factors_list = QListWidget()
        self.factors_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        fac_box.addWidget(self.factors_list)

        # "Другое" для факторов
        self.factor_other = QLineEdit()
        self.factor_other.setPlaceholderText("Другое (факторы), через ; например: перегруз; дедлайн")
        fac_box.addWidget(self.factor_other)

        lists.addLayout(emo_box, 1)
        lists.addLayout(fac_box, 1)

        root.addLayout(lists)

        # --- Кнопки ---
        btns = QHBoxLayout()
        self.btn_reload = QPushButton("Обновить списки")
        self.btn_save = QPushButton("Сохранить")
        btns.addWidget(self.btn_reload)
        btns.addStretch(1)
        btns.addWidget(self.btn_save)
        root.addLayout(btns)

        self.btn_reload.clicked.connect(self.reload_tag_lists)
        self.btn_save.clicked.connect(self.save_entry)

    def reload_tag_lists(self):
        self.emotions_list.clear()
        self.factors_list.clear()

        for name in fetch_tag_names("emotions"):
            self.emotions_list.addItem(QListWidgetItem(name))

        for name in fetch_tag_names("factors"):
            self.factors_list.addItem(QListWidgetItem(name))

    def _selected_names(self, lw: QListWidget) -> list[str]:
        return [item.text() for item in lw.selectedItems()]

    def _parse_other(self, text: str) -> list[str]:
        # Разрешаем несколько значений через ;
        parts = [p.strip() for p in text.split(";")]
        return [p for p in parts if p]

    def save_entry(self):
        emotions = self._selected_names(self.emotions_list) + self._parse_other(self.emotion_other.text())
        factors = self._selected_names(self.factors_list) + self._parse_other(self.factor_other.text())

        try:
            entry_id = create_entry(
                valence=self.valence.value(),
                arousal=self.arousal.value(),
                energy=self.energy.value(),
                social=self.social.value(),
                note=self.note.toPlainText().strip() or None,
                emotions=emotions,
                factors=factors,
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", str(e))
            return

        QMessageBox.information(self, "Готово", f"Сохранено! entry_id = {entry_id}")

        # Очистка формы (по-желанию)
        self.note.clear()
        self.emotion_other.clear()
        self.factor_other.clear()
        self.emotions_list.clearSelection()
        self.factors_list.clearSelection()

        # Теги могли добавиться (через "Другое") — обновим списки
        self.reload_tag_lists()

        # Сообщим главному окну, что надо обновить историю
        if self.on_saved_callback:
            self.on_saved_callback(entry_id)


class HistoryTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)

        top = QHBoxLayout()
        self.btn_refresh = QPushButton("Обновить")
        top.addWidget(self.btn_refresh)
        top.addStretch(1)
        root.addLayout(top)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Time", "Valence", "Arousal", "Energy", "Social"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self.table)

        self.btn_refresh.clicked.connect(self.refresh)
        self.table.itemDoubleClicked.connect(self.open_details)

    def refresh(self):
        try:
            rows = get_recent_entries()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки истории", str(e))
            return

        self.table.setRowCount(0)

        for r in rows:
            # ожидаем: (id, ts, valence, arousal, energy, social)
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

            for col, val in enumerate(r):
                item = QTableWidgetItem("" if val is None else str(val))
                if col in (0, 2, 3, 4, 5):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_idx, col, item)

    def open_details(self, item: QTableWidgetItem):
        row_idx = item.row()
        id_item = self.table.item(row_idx, 0)
        if not id_item:
            return

        entry_id = int(id_item.text())
        try:
            details = get_entry_details(entry_id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка деталей", str(e))
            return

        if not details:
            QMessageBox.information(self, "Нет данных", f"Запись {entry_id} не найдена.")
            return

        entry = details["entry"]
        emotions = ", ".join(details["emotions"]) if details["emotions"] else "—"
        factors = ", ".join(details["factors"]) if details["factors"] else "—"
        note = entry.get("note") or "—"

        text = (
            f"ID: {entry['id']}\n"
            f"Time: {entry['ts']}\n"
            f"Valence: {entry['valence']}\n"
            f"Arousal: {entry['arousal']}\n"
            f"Energy: {entry['energy']}\n"
            f"Social: {entry['social']}\n\n"
            f"Эмоции: {emotions}\n"
            f"Факторы: {factors}\n\n"
            f"Заметка:\n{note}"
        )
        QMessageBox.information(self, "Детали записи", text)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mood Tracker (Qt6)")
        self.resize(1100, 700)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        self.history_tab = HistoryTab()
        self.add_tab = AddEntryTab(on_saved_callback=self.on_entry_saved)

        tabs.addTab(self.add_tab, "Добавить")
        tabs.addTab(self.history_tab, "История")

    def on_entry_saved(self, _entry_id: int):
        # после сохранения — обновляем историю
        self.history_tab.refresh()


def main():
    # На всякий: создаём таблицы, если нет
    init_db()

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
