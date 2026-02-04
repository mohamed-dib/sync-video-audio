import sys
from PyQt5.QtWidgets import QApplication, QWidget,QLabel
from PyQt5.QtCore import Qt ,QRect
from PyQt5.QtGui import QMovie , QPainter ,QFont,QColor
from index import Detection_choice


class MonInterface(QLabel):
    def __init__(self,gif_path):
        super().__init__()
        self.gif = QMovie(gif_path)
        if not self.gif.isValid():
            raise FileNotFoundError(f"Impossible de charger le GIF : {gif_path}")
        self.setMovie(self.gif)
        self.gif.frameChanged.connect(self.update)
        self.gif.start()
        
        self.button_text = "Accédez à l'application"
        self.button_rect = QRect(0, 0, 400, 50) #dimension bouton

    
    def paintEvent(self , event):
        super().paintEvent(event)
        
        texte=QPainter(self)
        texte.setRenderHint(QPainter.Antialiasing)
        font = QFont("Helvetica",24,QFont.Bold)
        texte.setFont(font)
        texte.setPen(QColor(255,255,255))
        texte.drawText(self.rect(),Qt.AlignTop|Qt.AlignHCenter ,"Synchronisation d'une Vidéo \n avec une Musique")

        w = self.width() 
        h = self.height()
        btn_w= self.button_rect.width() 
        btn_h= self.button_rect.height()
        self.button_rect.moveTo((w-btn_w)//2, h - btn_h - 40)

        # fond du bouton
        texte.setPen(Qt.NoPen)
        texte.setBrush(QColor(255, 255, 255, 150))            # semi-transparent
        texte.drawRoundedRect(self.button_rect, 10, 10)

        # texte du bouton
        texte.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 14, QFont.Bold)
        texte.setFont(font)
        texte.drawText(self.button_rect, Qt.AlignCenter, self.button_text)
        
        texte.end()
    def mousePressEvent(self, event):
        if self.button_rect.contains(event.pos()):
            self.d =Detection_choice()
            self.d.show()
        else:
            super().mousePressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MonInterface("mongif.gif")
    w.resize(800, 450)
    w.setFixedSize(w.size())
    w.show()
    sys.exit(app.exec_())