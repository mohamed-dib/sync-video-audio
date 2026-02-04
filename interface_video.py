import sys
import cv2
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QSlider,
    QVBoxLayout, QHBoxLayout, QWidget, QComboBox
)
import os
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QImage
import subprocess

class VideoImageSelecteur(QMainWindow):

    #constructeur de la class 
    def __init__(self, video_path):
        super().__init__()
        
     
        ## Conversion  de la vidéo en 640×360, H.264, 30 fps
        base, ext = os.path.splitext(video_path)
        converted = f"{base}_conv.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-vf", "scale=640:-2",           
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-r", "30",
            converted
        ], check=True)
        self.video_path = converted
       
        # Ouverture de la vidéo convertie
        self.cap = cv2.VideoCapture(self.video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.current_frame_idx = 0
        self.key_frames = set()
        self.play_speed = 1.0
        self.compteur = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)

        self.init_ui()
        self.display_frame(self.current_frame_idx)

        self.setWindowTitle("Sélecteur d’images ")
        self.adjustSize()
        self.show()

        print("key_frames : ", self.key_frames)

    def init_ui(self):
        #  Composants 

        #centré la vidéo dans le frame et fixé la taille du cadre 
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
      
        #slider pour faire passé la vidéo 
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, self.total_frames - 1)
        self.slider.valueChanged.connect(self.slider_changed)

        #bouton play 
        self.btn_play = QPushButton("▶", self)
        self.btn_play.clicked.connect(self.toggle_play)

        #bouton previous
        self.btn_prev = QPushButton("⬅", self)
        self.btn_prev.clicked.connect(self.prev_frame)

        #bouton next 
        self.btn_next = QPushButton("➡", self)
        self.btn_next.clicked.connect(self.next_frame)

        #bouton previous pour le flag 
        self.btn_prev_flag = QPushButton("<< 🚩", self)
        self.btn_prev_flag.clicked.connect(self.goto_previous_flag)

        #bouton next pour le flag 
        self.btn_next_flag = QPushButton("🚩 >>", self)
        self.btn_next_flag.clicked.connect(self.goto_next_flag)

        #bouton pour marqué le flag 
        self.btn_flag = QPushButton("🚩", self)
        self.btn_flag.clicked.connect(self.toggle_flag_current_frame)

        #bouton pour prédire le prochain flag 
        self.btn_predict_flag = QPushButton("Prédire 🚩", self)
        self.btn_predict_flag.clicked.connect(self.predict_next_flag)

        #menu pour choisir la stratégie de prédiction
        self.prediction_mode = QComboBox(self)
        self.prediction_mode.addItem("Dernier intervalle")
        self.prediction_mode.addItem("Moyenne des intervalles")

        # bouton pour ralentir la vitesse à 0.5x
        self.btn_speed_1 = QPushButton("x1", self)
        self.btn_speed_1.clicked.connect(lambda: self.set_speed(1))
       
       # bouton pour ralentir la vitesse à 0.5x
        self.btn_speed_05 = QPushButton("x0.5", self)
        self.btn_speed_05.clicked.connect(lambda: self.set_speed(0.5))

        # bouton pour ralentir la vitesse à 0.25x
        self.btn_speed_025 = QPushButton("x0.25", self)
        self.btn_speed_025.clicked.connect(lambda: self.set_speed(0.25))

        # bouton pour exporter les frames flagguées
        self.btn_export_flags = QPushButton("Exporter flags", self)
        self.btn_export_flags.clicked.connect(self.export_flagged_frames)

        #label compteru
        self.compteur_label = QLabel("nombre de flags : ")

        # Layouts : ##############################################

        #mise en place des composant dans la fenetre

        #video + slider
        video_layout = QVBoxLayout()
        video_layout.addWidget(self.video_label)
        video_layout.addWidget(self.slider)

        #les 3 boutons prev play et next 
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_play)
        nav_layout.addWidget(self.btn_next)
        

        #les  boutons pour les flags et la prediction
        flag_layout = QHBoxLayout()
        flag_layout.addWidget(self.btn_prev_flag)
        flag_layout.addWidget(self.btn_flag)
        flag_layout.addWidget(self.btn_next_flag)
        flag_layout.addWidget(self.prediction_mode)
        flag_layout.addWidget(self.btn_predict_flag)

      # Mise en place des boutons de ralentissement
        speed_layout = QHBoxLayout()
        speed_layout.addStretch()
        speed_layout.addWidget(self.btn_speed_025)
        speed_layout.addWidget(self.btn_speed_05)
        speed_layout.addWidget(self.btn_speed_1)
        speed_layout.addStretch()


        # layout pour le bouton d'export
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        export_layout.addWidget(self.btn_export_flags)
        export_layout.addStretch()

        # mise en place dans le frame principal
        main_layout = QVBoxLayout()
        main_layout.addLayout(video_layout)
        main_layout.addLayout(nav_layout)
        main_layout.addLayout(flag_layout)
        main_layout.addLayout(speed_layout)
        main_layout.addLayout(export_layout)
        main_layout.addWidget(self.compteur_label)
        
        

        #ajout du main layout dans la fenetre
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


 

    def display_frame(self, frame_idx):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        self.video_label.setPixmap(pixmap)
        self.slider.setValue(frame_idx)
        self.current_frame_idx = frame_idx

        #background color du bouton si la frame est marquée
        if frame_idx in self.key_frames:
            self.btn_flag.setStyleSheet("background-color: yellow")
        else:
            self.btn_flag.setStyleSheet("")

    #gestion du bouton play - pause 
    def toggle_play(self):
        if self.timer.isActive(): 
            self.timer.stop()
            self.btn_play.setText("▶")
        else:
            interval_ms = int(1000 / self.fps / self.play_speed)
            self.timer.start(interval_ms)
            self.btn_play.setText("⏸")

    #gestion de vitesse 
    def set_speed(self, speed):
        self.play_speed = speed
        if self.timer.isActive(): # Si la vidéo est en train de jouer 
            self.timer.stop()
            interval_ms = int(1000 / self.fps / self.play_speed)
            self.timer.start(interval_ms)

    #affichage de la prochaine image dans la vidéo 
    def next_frame(self):
        if self.current_frame_idx < self.total_frames - 1:
            self.display_frame(self.current_frame_idx + 1)
        else:
            self.timer.stop()

    #affichage de l'image précédente dans la vidéo 
    def prev_frame(self):
        if self.current_frame_idx > 0:
            self.display_frame(self.current_frame_idx - 1)

    #changement de l'image avec le slider
    def slider_changed(self):
        new_frame_idx = self.slider.value()
        self.display_frame(new_frame_idx)

    #ajouter ou retirer un flag sur la frame actuelle
    def toggle_flag_current_frame(self):
        if self.current_frame_idx in self.key_frames:
            self.key_frames.remove(self.current_frame_idx)
            self.compteur -=1
            self.compteur_label.setText(f"nombre de flags :{self.compteur}")
        else:
            self.key_frames.add(self.current_frame_idx)
            self.compteur +=1
            self.compteur_label.setText(f"nombre de flags :{self.compteur}")
        self.display_frame(self.current_frame_idx)

    #aller au flag suivant
    def goto_next_flag(self):
        flags_after = sorted(f for f in self.key_frames if f > self.current_frame_idx)
        if flags_after:
            self.display_frame(flags_after[0])

    #aller au flag précédent
    def goto_previous_flag(self):
        flags_before = sorted(f for f in self.key_frames if f < self.current_frame_idx)
        if flags_before:
            self.display_frame(flags_before[-1])


    #prediction du prochain flag en fonction du dernier ou de la moyenne des intervalles

    def predict_next_flag(self):
        if len(self.key_frames) < 2:
            print("Pas assez de flags pour prédire.")
        else:
            self.btn_predict_flag.setEnabled(True)

            sorted_flags = sorted(self.key_frames)
            mode = self.prediction_mode.currentText()

            if mode == "Dernier intervalle":
                interval = sorted_flags[-1] - sorted_flags[-2]
            elif mode == "Moyenne des intervalles":
                intervals = [
                    sorted_flags[i+1] - sorted_flags[i]
                    for i in range(len(sorted_flags) - 1)
                ]
                interval = int(sum(intervals) / len(intervals))
            else:
                print("Mode de prédiction inconnu.")
                return

            predicted_flag = sorted_flags[-1] + interval
            if predicted_flag >= self.total_frames:
                print("Prédiction hors des limites de la vidéo.")
                return

            self.key_frames.add(predicted_flag)
            self.btn_predict_flag.setEnabled(len(self.key_frames) >= 2)
            self.btn_predict_flag.setToolTip("")
            print(f"Flag prédit ({mode}) ajouté à la frame {predicted_flag}")
            self.display_frame(predicted_flag)


    
    #methode pour exporter les images dans dans un dossier avec un json pour nous indiquer les information sur la vidéo et les image sauvgardé 
    def export_flagged_frames(self):
        if not self.key_frames:
            print("Aucun flag à exporter.")
            return

        output_dir = "export_flags"
        os.makedirs(output_dir, exist_ok=True)

        export_data = {
            "video_path": self.video_path,
            "fps": self.fps,
            "flags": sorted(list(self.key_frames))
        }

        for frame_idx in sorted(self.key_frames):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            if ret:
                filename = os.path.join(output_dir, f"frame_{frame_idx:04d}.jpg")
                cv2.imwrite(filename, frame)
                print(f"Exporté : {filename}")
            else:
                print(f"Erreur lors de l'export de la frame {frame_idx}")

        json_path = os.path.join(output_dir, "flags.json")
        with open(json_path, "w") as f:
            json.dump(export_data, f, indent=4)

        print(f"\nexport terminé : {len(self.key_frames)} images et les données sauvegardées dans '{output_dir}/'")

    #gestion des touches clavier 
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Space:
            self.toggle_play()
        elif key == Qt.Key_Right:
            self.next_frame()
        elif key == Qt.Key_Left:
            self.prev_frame()
        elif key == Qt.Key_F:
            self.toggle_flag_current_frame()
        elif key == Qt.Key_N:
            self.goto_next_flag()
        elif key == Qt.Key_P:
            self.goto_previous_flag()
        elif key==Qt.Key_V:
            self.predict_next_flag()
        elif key==Qt.Key_E :
            self.export_flagged_frames()

def main():
    app = QApplication(sys.argv)
    window = VideoImageSelecteur()
    sys.exit(app.exec_())


