import json, math
from moviepy import *
from tqdm import tqdm
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLineEdit, QLabel, QMessageBox,QRadioButton,QButtonGroup,QSpinBox
)
from moviepy import VideoFileClip, concatenate_videoclips
from moviepy.video.fx import MultiplySpeed

class MultiSyncApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synchronisation audio/Multiclips")
        self.resize(600, 200)

        #donne interne
        self.index = 0
        # Chemins
        self.beats_path = ""
        self.flags_path = ""



        #parametres
        self.label = QLabel("Parmétres : ")
        self.parametre1 = QRadioButton("Clip par Clip")
        self.parametre2 = QRadioButton("Rotaion parmi les clips")
         #si utilisateure choisi ce cas il doit inserer les k battement d'abord 
        self.video_Number_label = QLabel("Tous les K battements :")
        self.video_Number = QSpinBox()
        self.video_Number.setRange(0, 10)
        self.video_Number.setSingleStep (1)
        self.video_Number.setValue (0)
        
          #grouper les boutons
        self.group_btn = QButtonGroup()
        self.group_btn.addButton(self.parametre1,id=1)
        self.group_btn.addButton(self.parametre2,id=2)
        
        # Widgets
        self.btn_beats = QPushButton("Sélectionner beats.json")
        self.btn_flags = QPushButton("Sélectionner flags.json")
        self.output_name = QLineEdit()
        self.output_name.setPlaceholderText("Nom de sortie (sans .mp4)")
        self.btn_sync = QPushButton("Synchroniser")
        self.btn_sync.clicked.connect(self.verifie_checkbox)

        # Layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.parametre1)
        self.layout.addWidget(self.parametre2) 
        self.layout.addWidget(self.video_Number_label)
        self.layout.addWidget(self.video_Number)
        self.layout.addWidget(self.btn_beats)
        self.layout.addWidget(self.btn_flags)

        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Nom fichier :"))
        output_layout.addWidget(self.output_name)
        self.layout.addLayout(output_layout)
        self.layout.addWidget(self.btn_sync)
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        # Connexions
        self.btn_beats.clicked.connect(self.select_beats)
        self.btn_flags.clicked.connect(self.select_flags)
       # self.btn_sync.clicked.connect(self.run_synchronisation)


    def select_beats(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir beats.json", "", "JSON (*.json)")
        if path:
            self.beats_path = path
            self.btn_beats.setText(f"Succès !  {path.split('/')[-1]}")

    def select_flags(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir flags.json", "", "JSON (*.json)")
        if path:
            self.flags_path = path
            self.btn_flags.setText(f"Succès ! {path.split('/')[-1]}")
      


    def verifie_checkbox(self) :
        selcted_id=self.group_btn.checkedId()
        if selcted_id == 1:
            self.run_synchronisation_clip_par_clip()
        if selcted_id == 2:
            k = self.video_Number.value()
            if k <= 0:
               QMessageBox.warning(
               self,
               "Paramètre manquant",
               "Merci de saisir un nombre de battements (K) supérieur à 0."
               )
               return
            
            self.run_synchronisation_par_rotation(k)
            

    def run_synchronisation_clip_par_clip(self):
        if not self.beats_path or not self.flags_path or not self.output_name.text().strip():
            QMessageBox.warning(self, "Champs manquants", "Veuillez sélectionner les deux fichiers JSON et saisir un nom de sortie.")
            return

        try:
            BEATS_JSON = self.beats_path
            KEYS_JSON = self.flags_path
            VIDEO_OUT = self.output_name.text().strip()
            if not VIDEO_OUT.lower().endswith(".mp4"):
                VIDEO_OUT += ".mp4"
          
            #charger les donneés 
            beats = json.load(open(BEATS_JSON))["beats_seconds"]
            with open(KEYS_JSON,"r") as f:
                data = json.load(f)

            #repartition des beats (n beats pour chaque n images clés)
            sousliste_beats= []
            segments = []
            for i , info in enumerate(data):
              for key , video_info in info.items():
                #si y'a pas assez de beats pour les flags on arrete la boucle
                if len(video_info["flags"]) > len(beats)-self.index:
                    break 
                #on recupere les beats qu'il faut pour chaque video
                sousliste_beats=beats[self.index :  self.index + len(video_info["flags"])]
                video_in = video_info["video_path"]
                FPS = video_info["fps"]
                keys = video_info["flags"]
                VIDEO_IN = video_info["video_path"]
                self.index += len(video_info["flags"]) #mettre a jour l'index
               
                #convertir n° de frame -> temps vidéo
                key_times = [k / FPS for k in keys]
                 
                # charger la vidéo complète
                vid = VideoFileClip(VIDEO_IN)
                for i in tqdm(range(len(sousliste_beats)-1), desc="Traitement des segments"):
                    t_a0, t_a1 = sousliste_beats[i], sousliste_beats[i+1]
                    target_len = t_a1 - t_a0
                    t_v0, t_v1 = key_times[i], key_times[i+1]
        
                    # Extraction du segm
                   # ent et ajustement de durée
                    sub = vid.subclipped(t_v0, t_v1)
                    speed_effect = MultiplySpeed(sub, final_duration=target_len)
                    speed_adjusted = speed_effect.apply(sub)  # Application explicite de l'effet
               
                    segments.append(speed_adjusted)

                 # 4. concaténer et exporter
            print("export ...")
            final = concatenate_videoclips(segments, method="chain")
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

    def run_synchronisation_par_rotation(self,k_battement):
        if not self.beats_path or not self.flags_path or not self.output_name.text().strip():
            QMessageBox.warning(self, "Champs manquants", "Veuillez sélectionner les deux fichiers JSON et saisir un nom de sortie.")
            return

        try:
            BEATS_JSON = self.beats_path
            KEYS_JSON = self.flags_path
            VIDEO_OUT = self.output_name.text().strip()
            if not VIDEO_OUT.lower().endswith(".mp4"):
                VIDEO_OUT += ".mp4"
          
            #charger les donneés 
            beats = json.load(open(BEATS_JSON))["beats_seconds"]
            AudioFileClip
            with open(KEYS_JSON,"r") as f:
                data = json.load(f)

            #repartition des beats
            sousliste_beats= []
            segments = []
            clip_index = 0

            for i in range(0, len(beats) - 1, k_battement):
            # Choisir le bon bloc de beats
              sousliste_beats = beats[i:i + k_battement + 1]
              if len(sousliste_beats) < k_battement:
                break

              # Choisir le clip en rotation
              info = data[clip_index % len(data)]
              for key, video_info in info.items():
                 flags = video_info["flags"][:k_battement+1]
                 #supprimons les flags deja traité
                 video_info["flags"]=video_info["flags"][k_battement:]
                 fps = video_info["fps"]
                 video_path = video_info["video_path"]

                  # Pour ce bloc, on prend autant de flags que de beats
                 if len(flags) < len(sousliste_beats):
                     print("Pas assez de flags pour ce clip.")
                     continue
        
                 key_times = [f / fps for f in flags[:len(sousliste_beats)]]
                 vid = VideoFileClip(video_path)
 
                 for j in range(len(sousliste_beats) - 1):
                   t_a0, t_a1 = sousliste_beats[j], sousliste_beats[j+1]
                   target_len = t_a1 - t_a0
 
                   t_v0, t_v1 = key_times[j], key_times[j+1]
                   source_len = t_v1 - t_v0
                   if source_len <= 0 or target_len <= 0:
                     continue

                   sub = vid.subclipped(t_v0, t_v1)
                   speed_effect = MultiplySpeed(sub, final_duration=target_len)
                   speed_adjusted = speed_effect.apply(sub)  # Application explicite de l'effet
                   segments.append(speed_adjusted)
                 

              clip_index += 1  # passer au clip suivant

            # concaténer et exporter
            print("export ...")
            final = concatenate_videoclips(segments, method="chain")
            final.write_videofile(
                VIDEO_OUT,
                codec="libx264",
                fps=fps,
                audio_codec="aac",
                audio=json.load(open(BEATS_JSON))["audio_path"]
            )

            QMessageBox.information(self, "Terminé", f"Vidéo exportée :\n{VIDEO_OUT}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))


def main():
    app = QApplication(sys.argv)
    window = MultiSyncApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
   main()