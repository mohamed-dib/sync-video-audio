from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget,QDialog,QGridLayout,QHBoxLayout,QVBoxLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore     import Qt
from  detect_beats_manuelle import BeatDetector
from detect_beats_automatique import AutoDetect
from pres_synchronisation_video import VideoSelector
from pres_synchronisation_multiple import MultiClipSelector
import sys

class Detection_choice(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Choix de méthode de détection des beats")
        self.resize(500, 600)
        #buttons
        self.detection_beats = QPushButton("Traitement de l'audio \n(détection des beats)")
        self.synchonisation = QPushButton("Synchonisation")

           # Style des boutons
        for bouton in [ self.detection_beats, self.synchonisation]:
            bouton.setFixedSize(350, 200)
            bouton.setFont(QFont('Serif', 15))

        #layout
        bouton_layout=QVBoxLayout()
        bouton_layout.setAlignment(Qt.AlignCenter)
        bouton_layout.addWidget(self.detection_beats)
        bouton_layout.addWidget(self.synchonisation)
      
        layout_principale = QVBoxLayout()
        layout_principale.addLayout(bouton_layout)

        container=QWidget()
        container.setLayout(layout_principale)
        self.setCentralWidget(container)

        self.detection_beats.clicked.connect(self.audio_choice)
        self.synchonisation.clicked.connect(self.synchonisation_page)
       
    
    def audio_choice(self):
        self.auto_detect=QPushButton("detection automatique des \n beats avec Librosa")
        self.manuelle_detect=QPushButton("detection manuelle des beats")
         #affichage de la fenetre 
        self.auto_detect.setFixedSize(370,300)
        self.manuelle_detect.setFixedSize(370,300)
        audio_layout=QHBoxLayout()
        audio_layout.addWidget(self.auto_detect)
        audio_layout.addWidget(self.manuelle_detect)
        layout_principale = QVBoxLayout()
        layout_principale.addLayout(audio_layout)
        container=QWidget()
        container.setLayout(layout_principale)
        self.setCentralWidget(container)

        self.auto_detect.clicked.connect(self.auto_choice)
        self.manuelle_detect.clicked.connect(self.manuelle_choice)
    
    


    def auto_choice(self):
        self.viewer = AutoDetect()
        self.viewer.show()
       
    def manuelle_choice(self):
          self.viewer = BeatDetector()
          self.viewer.show()

    def one_video_choice(self):
        self.viewer=VideoSelector()
        self.viewer.show()


    def multiclips_choice(self):
       self.viewer=MultiClipSelector()
       self.viewer.show()


    def synchonisation_page(self):
        self.one_video=QPushButton("Synchronisation d'une seule \n Vidéo")
        self.multiclip=QPushButton("Synchronisation des multiclips")

        self.one_video.setFixedSize(370,300)
        self.multiclip.setFixedSize(370,300)
         #affichage de la fenetre 
        synchro_layout=QHBoxLayout()
        synchro_layout.addWidget(self.one_video)
        synchro_layout.addWidget(self.multiclip)
        layout_principale = QVBoxLayout()
        layout_principale.addLayout(synchro_layout)
        container=QWidget()
        container.setLayout(layout_principale)
        self.setCentralWidget(container)

        self.one_video.clicked.connect(self.one_video_choice)
        self.multiclip.clicked.connect(self.multiclips_choice)
        
def main():
    app = QApplication(sys.argv)
    Start = Detection_choice()
    Start.show()
    
    

if __name__ == "__main__":
    main()