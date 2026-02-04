import os
import json
from tqdm import tqdm
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLineEdit, QLabel, QMessageBox
)
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
from moviepy.video.fx import MultiplySpeed

class SyncApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synchronisation audio/vidéo")
        self.resize(600, 200)

        # Chemins
        self.beats_path = ""
        self.flags_path = ""

        # Widgets
        self.btn_beats = QPushButton("Sélectionner beats.json")
        self.btn_flags = QPushButton("Sélectionner flags.json")
        self.output_name = QLineEdit()
        self.output_name.setPlaceholderText("Nom de sortie (sans .mp4)")
        self.btn_sync = QPushButton("Synchroniser")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.btn_beats)
        layout.addWidget(self.btn_flags)

        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Nom fichier :"))
        output_layout.addWidget(self.output_name)
        layout.addLayout(output_layout)

        layout.addWidget(self.btn_sync)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Connexions
        self.btn_beats.clicked.connect(self.select_beats)
        self.btn_flags.clicked.connect(self.select_flags)
        self.btn_sync.clicked.connect(self.run_synchronisation)

    def select_beats(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir beats.json", "", "JSON (*.json)")
        if path:
            self.beats_path = path
            self.btn_beats.setText(f"Succès ! {os.path.basename(path)}")

    def select_flags(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir flags.json", "", "JSON (*.json)")
        if path:
            self.flags_path = path
            self.btn_flags.setText(f"Succès ! {os.path.basename(path)}")

    def run_synchronisation(self):
        if not self.beats_path or not self.flags_path or not self.output_name.text().strip():
            QMessageBox.warning(self, "Champs manquants", "Veuillez sélectionner les deux fichiers JSON et saisir un nom de sortie.")
            return
        try:
            # 1) Chargement des JSON
            BEATS_JSON = self.beats_path
            KEYS_JSON = self.flags_path
            VIDEO_OUT = self.output_name.text().strip()
            if not VIDEO_OUT.lower().endswith(".mp4"):
                VIDEO_OUT += ".mp4"

            beats = json.load(open(BEATS_JSON))["beats_seconds"]
            keys = json.load(open(KEYS_JSON))["flags"]
            VIDEO_IN = json.load(open(KEYS_JSON))["video_path"]
            FPS = json.load(open(KEYS_JSON))["fps"]

            assert len(beats) >= 2, "Au moins deux beats requis"

            # 2) Chargement de la vidéo
            vid = VideoFileClip(VIDEO_IN)
            key_times = [k / FPS for k in keys]

            segments = []
            for i in tqdm(range(len(beats)-1), desc="Traitement des segments"):
                t_a0, t_a1 = beats[i], beats[i+1]
                target_len = t_a1 - t_a0

                if i >= len(key_times)-1:
                    break

                t_v0, t_v1 = key_times[i], key_times[i+1]
        
                # Extraction du segm
                # ent et ajustement de durée
                sub = vid.subclipped(t_v0, t_v1)
                speed_effect = MultiplySpeed(sub, final_duration=target_len)
                speed_adjusted = speed_effect.apply(sub)  # Application explicite de l'effet
                
                segments.append(speed_adjusted)



            # 3) Concaténation et export
            final = concatenate_videoclips(segments, method="compose")
            final.write_videofile(
                VIDEO_OUT,
                codec="libx264",
                fps=FPS,
                audio_codec="aac",
                audio=json.load(open(BEATS_JSON))["audio_path"]
            )

            QMessageBox.information(self, "Terminé", f"Vidéo exportée :\n{VIDEO_OUT}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

if __name__ == "__main__":
    app = QApplication([])
    win = SyncApp()
    win.show()
    app.exec_()