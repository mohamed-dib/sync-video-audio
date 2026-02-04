import os
import sys
import numpy as np
import librosa
import pyqtgraph as pg
import json
import soundfile as sd 
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,QHBoxLayout ,QSlider,
     QVBoxLayout, QPushButton, QFileDialog,QSpinBox,QLabel,QComboBox,QStyle
)
from PyQt5.QtCore import Qt,QUrl,QTimer
from PyQt5.QtMultimedia import QMediaPlayer , QMediaContent,QSoundEffect
from pathlib import Path
from pydub  import AudioSegment 

class AutoDetect(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Affichage audio")
        self.resize(1000, 700)

        #données internes
        self.file_name = None
        self.beat_lignes = []
        self.beat_times = []
        self.liste_beats_ms = []
        self.duree=0.0
 
        self.player = QMediaPlayer(self)
        self.player.setNotifyInterval(1)  # mise à jour toutes les 1ms
        self.player.positionChanged.connect(self.on_position)
        self.player.durationChanged.connect(self.on_duration_changed)


        # === slider synchronisé ===
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.slider_moved)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_slider)
        self.time_label = QLabel("00:00 / 00:00")

       #charger le click 
        click_path =Path(__file__).parent /"mouse_click_20ms.wav"
        self.click = AudioSegment.from_file(click_path)

        # === Boutons ===
        self.load_bttn = QPushButton("Charger le fichier audio")
        self.load_bttn.clicked.connect(self.load_audio)
        self.load_final_json = QPushButton("Exporte le fichier audio avec les click")
        self.load_final_json.clicked.connect(self.Exporte_nouvel_audio)
        
        
        self.btn_player = QPushButton("Play")
        self.btn_player.clicked.connect(self.playAudio)
        self.btn_player.setEnabled(False)

        self.btn_prev = QPushButton("⏮ Previous")
        self.btn_prev.clicked.connect(self.goto_previous_beat)

        self.btn_next = QPushButton("Next ⏭")
        self.btn_next.clicked.connect(self.goto_next_beat)

        self.bttn_detect = QPushButton("Commencer la détection")
        self.bttn_detect.clicked.connect(self.appel_detect_beat)
      

        # === Paramètres ===

        #la debut de l'extrait
        self.debut_bttn_label=QLabel("Début de l'extrait")
        self.debut_bttn = QSpinBox()
        self.debut_bttn.setRange(0, 9999)
        self.debut_bttn.setValue(0)
        #la durée
        self.duration_bttn_label=QLabel("Duration de l'audio")
        self.duration_bttn = QSpinBox()
        self.duration_bttn.setRange(0, 9999)
        self.duration_bttn.setValue(60)
        
        #RMS
        self.pourcentage_box_label=QLabel("Seuil RMS (% max)")
        self.pourcentage_box = QSpinBox()
        self.pourcentage_box.setRange(10, 100)
        self.pourcentage_box.setValue(50)

        #RESOLUTION TEMPORELLE
        self.hop_length_label=QLabel("Résolution temporelle :")
        self.hop_length = QComboBox(self)
        self.hop_length.addItems(["64", "128", "256"])

        
        #AFFICHAGE
        self.label = QLabel("Beats marqués : 0")
        self.label1 = QLabel()

        # === Graphe ===
        pg.setConfigOption("background", 'k')
        pg.setConfigOption("foreground", 'w')
        self.plot_widget = pg.PlotWidget(title="Forme d'onde")
        self.plot_widget.setLabel('bottom', "temps", units='s')
        self.plot_widget.setLabel('left', "Amplitude")
        self.waveform_curve = self.plot_widget.plot([], [], pen=None,
                                                    brush=pg.mkBrush(100, 200, 150, 100),
                                                    fillLevel=0)
        self.lecteur_ligne = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('y', width=2))
        self.plot_widget.addItem(self.lecteur_ligne)


    
        # === Layout ===
        self.central = QWidget()
        self.layout = QVBoxLayout()
        
        #media controle
        media_controls = QHBoxLayout()
        media_controls.addWidget(self.btn_prev)
        media_controls.addWidget(self.btn_player)
        media_controls.addWidget(self.btn_next)
        #box parametre 
        #debut
        duration_debut_layout =QVBoxLayout()
        duration_debut_layout.addWidget(self.debut_bttn_label)
        duration_debut_layout.addWidget(self.debut_bttn)
        
        #durée
        duration_layout =QVBoxLayout()
        duration_layout.addWidget(self.duration_bttn_label)
        duration_layout.addWidget(self.duration_bttn)
        
        #RMS
        rms_layout = QVBoxLayout()
        rms_layout.addWidget(self.pourcentage_box_label)
        rms_layout.addWidget(self.pourcentage_box)

        #resolution
        hop_length_layout = QVBoxLayout()
        hop_length_layout.addWidget(self.hop_length_label)
        hop_length_layout.addWidget(self.hop_length)



        paremetre_layout = QHBoxLayout()
        paremetre_layout.addLayout(duration_debut_layout)
        paremetre_layout.addLayout(duration_layout)
        paremetre_layout.addLayout(rms_layout)
        paremetre_layout.addLayout(hop_length_layout)
        

        #chargement
        chargement_layout=QHBoxLayout()
        chargement_layout.addWidget(self.load_bttn)
        chargement_layout.addWidget(self.load_final_json)
        
        self.layout.addWidget(self.plot_widget)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.time_label)
        self.layout.addLayout(media_controls)
        self.layout.addWidget(self.bttn_detect)
        self.layout.addLayout(paremetre_layout)
        self.layout.addLayout(chargement_layout)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.label1)

        self.central.setLayout(self.layout)
        self.setCentralWidget(self.central)


    def convetir_mp3_wav(self,path):
        #recupere le nom sans extension
        base,_=os.path.splitext(path)
        out_wav = f"{base}.wav"
        cmd = [
            "ffmpeg" , "-y", "i",path,"-acodec" , "pcm_s16le","-ar" , "44100" , "-ac" , "2" , out_wav                
        ]
        subprocess.run(cmd , check=True)
        return out_wav


    def load_audio(self):
        self.file_name, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier audio", "", "Audio (*.wav *.mp3)")
        if not self.file_name:
           return

        #conversion vers  .wav
        if self.file_name.lower().endswith('.mp3'):
            self.file_name=self.convetir_mp3_wav(self.file_name)
        
        media = QMediaContent(QUrl.fromLocalFile(str(Path(self.file_name).resolve())))
        self.player.setMedia(media)
        self.audio = AudioSegment.from_file(self.file_name)
        #ajuster a duree 
        info = sd.info(self.file_name)
        self.duree = info.frames / info.samplerate
        self.duration_bttn.setMaximum(int(self.duree))
        self.duration_bttn.setValue(min(60, int(self.duree)))

        #suppression des lignes rouge de la detection  
        for ligne in self.beat_lignes:
            self.plot_widget.removeItem(ligne)
        self.beat_lignes.clear()
        
        self.y, self.sr = librosa.load(self.file_name, sr=None)
        times = np.arange(len(self.y)) / self.sr
        self.waveform_curve.setData(times, self.y)
        #affichage des deux axes X et Y
        self.plot_widget.setXRange(0, times[-1], padding=0.02)
        self.plot_widget.setYRange(np.min(self.y), np.max(self.y), padding=0.1)
        
          
    def on_duration_changed(self,duration):
        self.slider.setRange(0,duration)
        self.slider.setEnabled(True)
        self.time_label.setText(f"00:00 / {self.format_time(duration / 1000)}")
   
    def on_position(self , pos_ms ):
        #le palyer une fois changer de position
        self.slider.setValue(pos_ms)
        self.lecteur_ligne.setPos(pos_ms/1000)
        # Met à jour le label temps
        self.time_label.setText(
            f"{self.format_time(pos_ms / 1000)} / {self.format_time(self.duree)}"
        )

   
    def appel_detect_beat(self):
        if not self.file_name:
            return
        #recupere les parametre
        resolution = int(self.hop_length.currentText())
        rms_value = self.pourcentage_box.value()
        self.duration = self.duration_bttn.value()
        self.debut_extrait = self.debut_bttn.value()
        #appels a la fonction
        self.detect_beats(resolution, rms_value, self.debut_extrait ,self.duration)

    def detect_beats(self ,resolution, rms_value,start ,duree, output_path="beats.json"):
        #extraxtion de l'audio
        self.trimmed=self.audio[int(start*1000):int((start+duree)*1000)]
        output_file = Path("audio_extrait.wav")
        #exportation
        self.trimmed.export(str(output_file), format="wav")
        #le recuperer pour faire la detection avec
        wav_path = output_file.resolve()    
        y, sr = librosa.load(self.file_name,offset=start ,duration = duree)
        rms = librosa.feature.rms(y=y, hop_length=resolution)[0]
        onset_beats = librosa.onset.onset_detect(y=y, sr=sr, hop_length=resolution)
        onset_times = librosa.frames_to_time(onset_beats, sr=sr, hop_length=resolution)
        rms_beats = rms[onset_beats]
        th = (rms_value / 100) * np.max(rms)

        self.beat_times = [round(float(t+start), 3) for t, r in zip(onset_times, rms_beats) if r >= th]
        self.beat_times_extrait = [ i - start for i in self.beat_times]
         #covertir en milliseconde
        self.liste_beats_ms = sorted(int(t*1000) for t in self.beat_times_extrait)
        self.btn_player.setEnabled(True)
        
        with open(output_path, "w") as f:
            json.dump({
                "audio_path":  str(wav_path),
                "duration": duree,
                "beats_seconds": self.beat_times_extrait,
                }, f, indent=4)

        for ligne in self.beat_lignes:
            self.plot_widget.removeItem(ligne)
        self.beat_lignes.clear()

        for beat in self.beat_times:
            ligne = pg.InfiniteLine(pos=beat, angle=90, pen=pg.mkPen('r', width=1, style=Qt.DashLine))
            self.plot_widget.addItem(ligne)
            self.beat_lignes.append(ligne)

        self.label.setText(f"Beats marqués : {len(self.beat_times)}")
        self.label1.setText(f"Exporté dans : {output_path}")


    def playAudio(self):
        if self.player.state() == QMediaPlayer.PlayingState:
           self.player.pause()
           self.btn_player.setText("Play")
           self.timer.stop()
        else:
            self.player.play()
            self.btn_player.setText("Pause")
            self.timer.start(100)
     

    def update_slider(self):
        pos = self.player.position()
        self.slider.setValue(pos)
        self.time_label.setText(
            f"{self.format_time(pos / 1000)} / {self.format_time(self.duree)}"
        )

    def slider_moved(self, position):
        self.player.setPosition(position)

    def goto_previous_beat(self):
        if not self.beat_times:
            return
        self.current_beat_index = max(0, self.current_beat_index - 1)
        self.jump_to_beat()

    def goto_next_beat(self):
        if not self.beat_times:
            return
        self.current_beat_index = min(len(self.beat_times) - 1, self.current_beat_index + 1)
        self.jump_to_beat()

    def jump_to_beat(self):
        if 0 <= self.current_beat_index < len(self.beat_times):
            ms = int(self.beat_times[self.current_beat_index] * 1000)
            self.player.setPosition(ms)
            self.timer.start(100)

    def format_time(self, seconds):
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m:02d}:{s:02d}"
    

    def keyPressEvent(self, event):
      key = event.key()
      if key == Qt.Key_Space:
          self.playAudio()
      elif key == Qt.Key_Right:
          self.goto_next_beat()
      elif key == Qt.Key_Left:
          self.goto_previous_beat()
      elif key == Qt.Key_L:
          self.load_audio()
      elif key == Qt.Key_D:
          if self.file_name and hasattr(self, 'y') and hasattr(self, 'sr'):
              resolution = int(self.hop_length.currentText())
              rms_value = self.pourcentage_box.value()
              duree = self.duration_bttn.value()
              self.detect_beats(self.y, self.sr, resolution, rms_value, duree)
      elif key == Qt.Key_E:
          self.Exporte_nouvel_audio()
     
    def Exporte_nouvel_audio(self):
        output = self.trimmed[:] #copie de l'audio
        for t in  self.liste_beats_ms: 
            output = output.overlay(self.click , position = t)
        output.export("audio_with_click.wav",format="wav")
        print("Exporté - > audio_with_click.wav ")
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoDetect()
    window.show()
    sys.exit(app.exec_())
