import datetime

from fpdf import FPDF
from fpdf.html import HTMLMixin


class PriceList(FPDF, HTMLMixin):
    def header(self):
        self.cell(80)
        self.cell(30, 10, 'Прайс-лист', 1, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.cell(0, 10,
                  "Отчет сгенерирован автоматически, на основе данных от " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                  0, 0, 'C')

    def __init__(self):
        super().__init__()
        self.add_font("dejavu-sans", style="", fname="./fonts/DejaVuSans.ttf")
        self.add_font("dejavu-sans", style="b", fname="./fonts/DejaVuSans-Bold.ttf")
        self.set_font('dejavu-sans', size=10)