import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, 
    QVBoxLayout, QWidget ,QSpinBox,QFileDialog
) 

from interface_video import VideoImageSelecteur
from synchonisation_une_video import SyncApp
class VideoSelector(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synchronisation d'une vidéo")
        self.resize(500, 200)

        self.traiter = QPushButton("Traitez la vidéo")
        self.traiter.clicked.connect(self.traitement)

        self.synch_btn = QPushButton("commencer la synchronisation")
        self.synch_btn.setEnabled(False)
        self.synch_btn.clicked.connect(self.synchronisation)
        # Layout
        self.central = QWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.traiter)
        self.layout.addWidget(self.synch_btn)
        self.central.setLayout(self.layout)
        self.setCentralWidget(self.central)

    def traitement(self):
        video_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionnez une vidéo",
            "",  # dossier de départ (vide = dossier courant)
            "Fichiers vidéo (*.mp4 *.avi *.mov *.mkv)"
        )
        if video_path:
            # Si l'utilisateur a choisi un fichier, on l'utilise
            self.synch_btn.setEnabled(True)
            self.video_selected = VideoImageSelecteur(video_path)
            self.video_selected.show()

    def synchronisation(self):
        self.window= SyncApp()
        self.window.show()

def main():
    app = QApplication(sys.argv)
    window = VideoSelector()
    window.show()

if __name__ == "__main__":
   main()