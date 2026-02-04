import sys
import numpy as np
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel,
    QFileDialog, QHBoxLayout, QSlider
)
from PyQt5.QtCore import QTimer, QUrl , Qt
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import pyqtgraph as pg
from pydub import AudioSegment
import json
import util

class BeatDetector(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Détection de Beat - Audio Tool")
        self.setGeometry(200, 200, 1000, 500)

        self.audio = None
        self.audio_data = None
        self.sample_rate = 44100
        self.position = 0
        self.beats = []
        self.auto_beat_lines=[]

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_cursor)

        self.player = QMediaPlayer()
        self.player.positionChanged.connect(self.sync_cursor_with_audio)
        self.slider = QSlider(Qt.Horizontal)
        self.player.durationChanged.connect(self.on_duration_changed)


        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Graphiques
        graph_layout = QHBoxLayout()
        self.waveform_widget = pg.PlotWidget(title="Forme d’onde")
        self.waveform_plot = None  # Initialisé plus tard
        self.cursor_wave = pg.InfiniteLine(angle=90, movable=True, pen='b')
        self.waveform_widget.addItem(self.cursor_wave)
        self.playhead_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('y', width=2))
        self.waveform_widget.addItem(self.playhead_line)
        
        #self.cursor_wave.sigPositionChanged.connect(self.cursor_moved)


        #curseur 

        self.slider.setEnabled(False)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.slider_moved)

        self.energy_widget = pg.PlotWidget(title="Énergie")
        self.energy_plot = self.energy_widget.plot()
        self.cursor_energy = pg.InfiniteLine(angle=90, movable=True, pen='g')
        self.energy_widget.addItem(self.cursor_energy)
        #self.cursor_energy.sigPositionChanged.connect(self.cursor_moved)
       # Boutons de zoom alignés verticalement
        zoom_btn_layout = QVBoxLayout()
        self.zoom_in_btn = QPushButton("Zoom +")
        self.zoom_out_btn = QPushButton("Zoom -")
        self.reset_zoom_btn = QPushButton("Zoom par défaut")

        zoom_btn_layout.addWidget(self.zoom_in_btn)
        zoom_btn_layout.addWidget(self.zoom_out_btn)
        zoom_btn_layout.addWidget(self.reset_zoom_btn)
        zoom_btn_layout.addStretch()  # Pour les repousser vers le haut

        # Layout principal des graphes + zoom
        graph_layout = QHBoxLayout()
        graph_layout.addWidget(self.waveform_widget)
        graph_layout.addWidget(self.energy_widget)
        graph_layout.addLayout(zoom_btn_layout)
        layout.addLayout(graph_layout)
        layout.addWidget(self.slider)

        # Boutons
        btn_layout = QVBoxLayout()
        self.load_btn = QPushButton("Charger Audio")
        self.play_btn = QPushButton("Play")
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.mark_btn = QPushButton("Marquer le beat")
        self.prev_beat_btn = QPushButton("Beat <-")
        self.next_beat_btn = QPushButton("Beat ->")

        
        self.export_beats_btn = QPushButton("Exporter les Beats")
        self.import_auto_btn = QPushButton("Importer détection auto des Beats")

        # Layout 
        nav_layout = QHBoxLayout()
        util_layout = QHBoxLayout()
        beat_layout= QHBoxLayout()
        zoom_layout = QHBoxLayout()

       # util_layout.addStretch()
        for btn in [self.load_btn  ,self.export_beats_btn , self.import_auto_btn ]  : util_layout.addWidget(btn)
        #util_layout.addStretch()

        for btn in [ self.prev_beat_btn, self.mark_btn, self.next_beat_btn] : beat_layout.addWidget(btn)

        #nav_layout.addStretch()
        for btn in [self.prev_btn , self.play_btn, self.next_btn]  : nav_layout.addWidget(btn)
        #nav_layout.addStretch()

        #zoom_layout.addStretch()
        for btn in [self.zoom_in_btn, self.zoom_out_btn, self.reset_zoom_btn ]:zoom_layout.addWidget(btn)
        #zoom_layout.addStretch()


        btn_layout.addLayout(nav_layout)
        btn_layout.addLayout(beat_layout)
        btn_layout.addLayout(util_layout)
        btn_layout.addLayout(zoom_layout)


        layout.addLayout(btn_layout)

        # Label
        self.label = QLabel("Beats marqués : 0")
        layout.addWidget(self.label)

        self.setLayout(layout)

        # Connexions
        self.load_btn.clicked.connect(self.load_audio)
        self.play_btn.clicked.connect(self.play_audio)
        self.prev_btn.clicked.connect(self.prev_frame)
        self.next_btn.clicked.connect(self.next_frame)
        self.mark_btn.clicked.connect(self.mark_beat)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        self.export_beats_btn.clicked.connect(self.export_beats)
        self.import_auto_btn.clicked.connect(self.import_auto_beats)


  

        self.prev_beat_btn.clicked.connect(self.goto_previous_beat)
        self.next_beat_btn.clicked.connect(self.goto_next_beat)
        self.current_beat_index = -1


    def load_audio(self):
        self.beats=[]
        
        for line in self.auto_beat_lines:
            self.waveform_widget.removeItem(line)
            self.energy_widget.removeItem(line)
        self.auto_beat_lines.clear()

        file_path, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier audio", "", "Audio Files (*.wav *.mp3)")
        file_path = util.sanitize_path(file_path)
        if file_path:
            self.audio = AudioSegment.from_file(file_path)
            self.audio = self.audio.set_channels(1).set_frame_rate(self.sample_rate)
            self.audio_data = np.array(self.audio.get_array_of_samples())

            # Forme d’onde
            if self.waveform_plot is None:
                self.waveform_plot = self.waveform_widget.plot()

            self.waveform_plot.setData(self.audio_data / max(abs(self.audio_data)))

            # Énergie
            frame_size = 1024
            hop_size = 512
            energy = [
                np.sum(self.audio_data[i:i + frame_size] ** 2)
                for i in range(0, len(self.audio_data) - frame_size, hop_size)
            ]
            energy = np.array(energy)
            energy_time = np.linspace(0, len(self.audio_data) / self.sample_rate, len(energy))
            self.energy_plot.setData(energy_time, energy / np.max(energy))

            # Charger audio dans QMediaPlayer
            media = QMediaContent(QUrl.fromLocalFile(str(Path(file_path).resolve())))
            self.player.setMedia(media)
            print("Media Status:", self.player.mediaStatus())
            print("Durée (ms) indiquée par QMediaPlayer :", self.player.duration())


            # Réinitialiser
            self.cursor_wave.setPos(0)
            self.cursor_energy.setPos(0)
            self.position = 0
            self.beats = []
            self.label.setText("Beats marqués : 0")
    
    def import_auto_beats(self):
        path, _ = QFileDialog.getOpenFileName(self, "Charger détection automatique", "", "JSON Files (*.json)")
        if not path:
            return

        try:
            with open(path, 'r') as f:
                data = json.load(f)

            # Charger l'audio depuis le JSON
            audio_path = data.get("audio_path", "")
            if not Path(audio_path).exists():
                print(f"Audio introuvable : {audio_path}")
                return

            audio_path = util.sanitize_path(audio_path)
            self.audio = AudioSegment.from_file(audio_path)
            self.audio = self.audio.set_channels(1).set_frame_rate(self.sample_rate)
            self.audio_data = np.array(self.audio.get_array_of_samples())

            if self.waveform_plot is None:
                 self.waveform_plot = self.waveform_widget.plot()

            self.waveform_plot.setData(self.audio_data / max(abs(self.audio_data)))


            # Énergie
            frame_size = 1024
            hop_size = 512
            energy = [
                np.sum(self.audio_data[i:i + frame_size] ** 2)
                for i in range(0, len(self.audio_data) - frame_size, hop_size)
            ]
            energy = np.array(energy)
            energy_time = np.linspace(0, len(self.audio_data) / self.sample_rate, len(energy))
            self.energy_plot.setData(energy_time, energy / np.max(energy))

            # Charger dans QMediaPlayer
            media = QMediaContent(QUrl.fromLocalFile(str(Path(audio_path).resolve())))
            self.player.setMedia(media)

            # Reset curseurs
            self.cursor_wave.setPos(0)
            self.cursor_energy.setPos(0)
            self.position = 0

            # Afficher les beats détectés automatiquement
            auto_beats = data.get("beats_seconds", [])

            for beat in auto_beats:
                if beat not in self.beats:
                    self.beats.append(beat)

                self.beats.sort()
                self.label.setText(f"Beats marqués : {len(self.beats)}")

            self.show_auto_beats(auto_beats)

            print(f"Audio chargé : {audio_path}")
            print(f"{len(auto_beats)} beats automatiques importés et affichés.")

        except Exception as e:
            print(f"Erreur : {e}")


       

    def show_auto_beats(self, beat_list):
        # Supprimer anciennes lignes
        for line in self.auto_beat_lines:
            self.waveform_widget.removeItem(line)
            self.energy_widget.removeItem(line)
        self.auto_beat_lines = []

        for beat_sec in beat_list:
            # ligne pour energy_widget : pos = secondes
            line_energy = pg.InfiniteLine(pos=beat_sec, angle=90, pen=pg.mkPen('y', style=Qt.DashLine))
            self.energy_widget.addItem(line_energy)

            #ligne pour waveform_widget : pos = indice = secondes * sample_rate
            x_sample = beat_sec * self.sample_rate
            line_waveform = pg.InfiniteLine(pos=x_sample, angle=90, pen=pg.mkPen('y', style=Qt.DashLine))
            self.waveform_widget.addItem(line_waveform)

            self.auto_beat_lines.append(line_energy)
            self.auto_beat_lines.append(line_waveform)





    def play_audio(self):
        if self.player.mediaStatus() != QMediaPlayer.NoMedia:
            if self.player.state() == QMediaPlayer.PlayingState:
                self.player.pause()
                self.timer.stop()
                self.play_btn.setText("Play")
            else:
                self.player.play()
                self.timer.start()
                self.play_btn.setText("Stop")



    def stop_audio(self):
        self.player.stop()
        self.timer.stop()

    def next_frame(self):
        self.position += 500  # avancer de 500ms
        self.player.setPosition(self.position)  # <-- repositionne l'audio
        self.update_cursors_from_position()
    
    def prev_frame(self):
        self.position = max(0, self.position - 500)
        self.player.setPosition(self.position)  # <-- repositionne l'audio
        self.update_cursors_from_position()

    def mark_beat(self):
        time_in_sec = round(self.cursor_energy.value(), 3)

        # Si déjà marqué (tolérance ±0.02s) → on supprime
        existing = [b for b in self.beats if abs(b - time_in_sec) < 0.02]
        if existing:
            for b in existing:
                self.beats.remove(b)
            print(f"Beat supprimé à {time_in_sec:.3f} sec")
        else:
            self.beats.append(time_in_sec)
            print(f"Beat marqué à {time_in_sec:.3f} sec")

        self.label.setText(f"Beats marqués : {len(self.beats)}")


    def zoom_in(self):
        self.waveform_widget.getViewBox().scaleBy((0.8, 0.8))
        self.energy_widget.getViewBox().scaleBy((0.8, 0.8))

    def zoom_out(self):
        self.waveform_widget.getViewBox().scaleBy((1.25, 1.25))
        self.energy_widget.getViewBox().scaleBy((1.25, 1.25))

    def reset_zoom(self):
        self.waveform_widget.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)
        self.energy_widget.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)

    def cursor_moved(self):
        # Déplacement manuel → on synchronise
        sample_index = self.cursor_wave.value()
        sec = sample_index / self.sample_rate
        self.position = int(sec * 1000)
        self.cursor_energy.setPos(sec)
        self.cursor_wave.setPos(sample_index)

    def update_cursors_from_position(self):
        sec = self.position / 1000
        self.cursor_energy.setPos(sec)
        self.cursor_wave.setPos(sec * self.sample_rate)

    def sync_cursor_with_audio(self, new_pos_ms):
        self.playhead_line.setPos(new_pos_ms/1000)
        self.slider.setValue(new_pos_ms)
        self.cursor_wave.setPos(new_pos_ms/1000)
        self.cursor_energy.setPos(new_pos_ms/1000)
        self.position = new_pos_ms
        self.update_cursors_from_position()


    def update_cursor(self):
        # (inutilisé ici, mais peut servir pour un timer si nécessaire)
        self.update_cursors_from_position()
        self.slider.setValue(self.player.position())


     #gestion des touches clavier 
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Space:
            self.play_audio()
        elif key == Qt.Key_Right:
            self.next_frame()
        elif key == Qt.Key_Left:
            self.prev_frame()
        elif key == Qt.Key_F:
            self.mark_beat()
        elif event.modifiers() & Qt.ControlModifier or event.modifiers() & Qt.MetaModifier:
            if key == Qt.Key_Plus or key == Qt.Key_Equal:
                self.zoom_in()
            elif key == Qt.Key_Minus:
                self.zoom_out()
        elif key== Qt.Key_L:
            self.load_audio()
        elif key == Qt.Key_E:
            self.export_beats()

    def export_beats(self):
        if self.beats:
            file_path, _ = QFileDialog.getSaveFileName(self, "Exporter les Beats", "", "JSON Files (*.json)")
            self.beats = sorted(self.beats)

            if file_path:
                data = {
                    "beats_seconds": self.beats,
                    "audio_path": str(self.player.currentMedia().canonicalUrl().toLocalFile())
                }
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=4)
                print(f"Beats exportés avec succès vers : {file_path}")


    #les bouton
    def goto_previous_beat(self):
        if not self.beats:
            return
        self.current_beat_index = max(0, self.current_beat_index - 1)
        self.jump_to_beat()

    def goto_next_beat(self):
        if not self.beats:
            return
        self.current_beat_index = min(len(self.beats) - 1, self.current_beat_index + 1)
        self.jump_to_beat()

    def jump_to_beat(self):
        if 0 <= self.current_beat_index < len(self.beats):
            ms = int(self.beats[self.current_beat_index] * 1000)
            self.player.setPosition(ms)
            self.timer.start(100)



    def slider_moved(self, position):
        self.player.setPosition(position)
        for i , b in enumerate( self.beats):
            if b > self.position:
                self.next_beat_index = i
                break
            else :
                self.next_beat_index = len(self.beats)
                
    def on_duration_changed(self,duration):
        self.slider.setRange(0,duration)
        self.slider.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BeatDetector()
    window.show()
    sys.exit(app.exec_())
