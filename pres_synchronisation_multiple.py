import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, 
    QVBoxLayout, QWidget ,QSpinBox,QFileDialog
)
import os
from interface_video_multiple import VideoImageSelecteur
from synchronisation_multiclip import MultiSyncApp

class MultiClipSelector(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Traitement des vidéos")
        self.resize(500, 200)
        self.btn_liste = []

        self.video_Number_label = QLabel("Choisissez le nombre de vidéos souhaité à traiter :")
        self.video_Number = QSpinBox()
        self.video_Number.setRange(1, 5)
        self.video_Number.setValue(1)

        self.confirme = QPushButton("Importer les vidéo")
        self.confirme.clicked.connect(self.traitement)

        self.synch_btn = QPushButton("commencer la synchronisation")
        self.synch_btn.clicked.connect(self.synchronisation)
        # Layout
        self.central = QWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.video_Number_label)
        self.layout.addWidget(self.video_Number)
        self.layout.addWidget(self.confirme)
        self.layout.addWidget(self.synch_btn)

        
        self.central.setLayout(self.layout)
        self.setCentralWidget(self.central)

    def traitement(self):
        # Nettoyage précédent
        for btn in self.btn_liste:
            self.layout.removeWidget(btn)
            btn.deleteLater()

        self.btn_liste = []
        self.video_selectors = [None] * self.video_Number.value()

        for i in range(self.video_Number.value()):
            btn = QPushButton(f"Vidéo {i + 1}")
            btn.setEnabled(i == 0)  # Seul le premier bouton est actif au départ
            self.layout.addWidget(btn)
            self.btn_liste.append(btn)

            # Connexion dynamique avec index capturé
            btn.clicked.connect(lambda _, index=i: self.traitement_video(index))
       
        

    def traitement_video(self, index):
        video_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Sélectionnez la vidéo {index + 1}",
            "",
            "Fichiers vidéo (*.mp4 *.avi *.mov *.mkv)"
        )

        if video_path:
            def enable_next():
                if index + 1 < len(self.btn_liste):
                    self.btn_liste[index + 1].setEnabled(True)

            selector = VideoImageSelecteur(video_path,index+1, on_close_callback=enable_next)
            self.video_selectors[index] = selector
            selector.show()
            
            videopath = os.path.basename(video_path)
            label = QLabel(f"Vidéo {index + 1} : {videopath} Succés !")
            self.layout.addWidget(label)

    def synchronisation(self):
        self.window= MultiSyncApp()
        self.window.show()

def main():
    app = QApplication(sys.argv)
    window = MultiClipSelector()
    window.show()

if __name__ == "__main__":
   main()