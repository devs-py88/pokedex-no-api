import sys, json, os
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidgetItem,
    QLabel, QPushButton, QWidget, QVBoxLayout
)
from PyQt6.QtGui import QPixmap, QIcon, QPalette, QColor, QFont
from PyQt6.QtCore import Qt, QSize

DATASET   = "dataset/pokemon_full.json"
EV_INDEX  = "dataset/evolution_index.json"
EV_DIR    = "dataset/evolutions"
IMAGE_DIR = "images"
POKEMON_HOME_ID = 1   # Pokémon #001


class Pokedex(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("pokedex.ui", self)

        self.load_data()
        self.setup_ui()
        self.populate_list()

    # ---------- FONT ----------
    def bold_font(self, size=10):
        f = QFont()
        f.setBold(True)
        f.setPointSize(size)
        return f

    # ---------- LOAD DATA ----------
    def load_data(self):
        with open(DATASET, encoding="utf-8") as f:
            self.data = json.load(f)
        self.keys = sorted(self.data.keys(), key=lambda k: self.data[k]["id"])

        if os.path.exists(EV_INDEX):
            with open(EV_INDEX, encoding="utf-8") as f:
                self.ev_index = json.load(f)
        else:
            self.ev_index = {}

    # ---------- UI SETUP ----------
    def setup_ui(self):
        # ===== LOGO CLICK =====
        # lblLogo phải tồn tại trong UI
        if hasattr(self, "lblLogo"):
            self.lblLogo.mousePressEvent = lambda event: self.jump_to_pokemon_id(POKEMON_HOME_ID)

        # ===== LIST =====
        self.pokemonList.setIconSize(QSize(64, 64))
        self.searchEdit.textChanged.connect(self.filter_list)
        self.pokemonList.currentItemChanged.connect(self.show_pokemon)

        # ===== STATS BARS =====
        bars = [
            (self.barHP, "HP"),
            (self.barATK, "Attack"),
            (self.barDEF, "Defense"),
            (self.barSPA, "Sp. Atk"),
            (self.barSPD, "Sp. Def"),
            (self.barSPE, "Speed"),
        ]
        for bar, name in bars:
            bar.setMaximum(15)
            bar.setFormat(f"{name}: %v / 15")
            bar.setFixedHeight(14)

        self.infoCard.setStyleSheet("""
            QFrame {
                background-color: #32a8d6;
                border-radius: 14px;
                padding: 12px;
            }
        """)

        for lbl in (
            self.lblHeight, self.lblWeight,
            self.lblGender, self.lblCategory,
            self.lblAbilities
        ):
            lbl.setStyleSheet("color:white;font-size:14px")
            lbl.setWordWrap(True)

        self.lblName.setFont(self.bold_font(22))
        self.lblName.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # ---------- UTILS ----------
    def stat_to_15(self, v):
        return round(v / 255 * 15) if v else 0

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def jump_to_pokemon_id(self, pid):
        for i in range(self.pokemonList.count()):
            it = self.pokemonList.item(i)
            name = it.data(Qt.ItemDataRole.UserRole)
            if self.data[name]["id"] == pid:
                self.pokemonList.setCurrentItem(it)
                self.pokemonList.scrollToItem(it)
                break

    # ---------- LIST ----------
    def populate_list(self):
        self.pokemonList.clear()
        for name in self.keys:
            p = self.data[name]
            it = QListWidgetItem(name.capitalize())
            it.setFont(self.bold_font(10))

            icon = f"{IMAGE_DIR}/{p['id']}.png"
            if os.path.exists(icon):
                it.setIcon(QIcon(icon))

            it.setData(Qt.ItemDataRole.UserRole, name)
            self.pokemonList.addItem(it)

    def filter_list(self, text):
        text = text.lower()
        for i in range(self.pokemonList.count()):
            it = self.pokemonList.item(i)
            it.setHidden(text not in it.text().lower())

    # ---------- DETAIL ----------
    def show_pokemon(self, current):
        if not current:
            return

        key = current.data(Qt.ItemDataRole.UserRole)
        p = self.data[key]

        self.lblName.setText(key.capitalize())

        img = f"{IMAGE_DIR}/{p['id']}.png"
        if os.path.exists(img):
            self.lblImage.setPixmap(QPixmap(img).scaled(
                220, 220,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))

        self.lblHeight.setText(f"Height\n{p.get('height','Unknown')}")
        self.lblWeight.setText(f"Weight\n{p.get('weight','Unknown')}")
        self.lblCategory.setText(f"Category\n{p.get('category','Unknown')}")

        g = p.get("gender", [])
        gender = "Unknown" if not g else " ".join("♂" if x == "male" else "♀" for x in g)
        self.lblGender.setText(f"Gender\n{gender}")

        ab = p.get("abilities", [])
        self.lblAbilities.setText(
            "Abilities\n" + (", ".join(a.replace("-", " ").title() for a in ab) if ab else "Unknown")
        )

        st = p.get("stats", {})
        self.barHP.setValue(self.stat_to_15(st.get("hp", 0)))
        self.barATK.setValue(self.stat_to_15(st.get("attack", 0)))
        self.barDEF.setValue(self.stat_to_15(st.get("defense", 0)))
        self.barSPA.setValue(self.stat_to_15(st.get("special-attack", 0)))
        self.barSPD.setValue(self.stat_to_15(st.get("special-defense", 0)))
        self.barSPE.setValue(self.stat_to_15(st.get("speed", 0)))

        self.clear_layout(self.typeLayout)
        self.clear_layout(self.weakLayout)

        for t in p.get("types", []):
            self.typeLayout.addWidget(self.make_badge(t))
        for w in p.get("weaknesses", []):
            self.weakLayout.addWidget(self.make_badge(w))

        self.load_evolution(p["id"])

    # ---------- BADGE ----------
    def badge_color(self, t):
        return {
            "fire":"#EE8130","water":"#6390F0","grass":"#7AC74C",
            "electric":"#F7D02C","ice":"#96D9D6","fighting":"#C22E28",
            "poison":"#A33EA1","ground":"#E2BF65","flying":"#A98FF3",
            "psychic":"#F95587","bug":"#A6B91A","rock":"#B6A136",
            "ghost":"#735797","dragon":"#6F35FC","dark":"#705746",
            "steel":"#B7B7CE","fairy":"#D685AD","normal":"#A8A77A"
        }.get(t, "#AAA")

    def make_badge(self, text):
        lbl = QLabel(text.capitalize())
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"""
            background:{self.badge_color(text)};
            color:white;
            padding:6px 14px;
            border-radius:10px;
            font-weight:bold;
        """)
        return lbl

    # ---------- EVOLUTION ----------
    def load_evolution(self, pid):
        self.clear_layout(self.evoLayout)
        cid = self.ev_index.get(str(pid))
        if not cid:
            return

        path = f"{EV_DIR}/{cid}.json"
        if not os.path.exists(path):
            return

        with open(path, encoding="utf-8") as f:
            chain = json.load(f)

        self.render_chain(chain)

    def render_chain(self, node):
        self.add_evo(node)
        for evo in node.get("evolves_to", []):
            arrow = QLabel("→")
            arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
            arrow.setFont(self.bold_font(22))
            arrow.setStyleSheet("padding:0 18px;color:#444;")
            self.evoLayout.addWidget(arrow)
            self.render_chain(evo)

    def add_evo(self, node):
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn = QPushButton()
        btn.setFlat(True)
        btn.setIconSize(QSize(96, 96))

        img = f"{IMAGE_DIR}/{node['id']}.png"
        if os.path.exists(img):
            btn.setIcon(QIcon(img))

        lbl = QLabel(node["name"].capitalize())
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(self.bold_font(13))

        lay.addWidget(btn)
        lay.addWidget(lbl)
        self.evoLayout.addWidget(box)

        btn.clicked.connect(lambda _, i=node["id"]: self.jump_to_pokemon_id(i))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # ===== PALETTE =====
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Highlight, QColor(76, 163, 224))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(palette)

    w = Pokedex()
    w.show()
    sys.exit(app.exec())