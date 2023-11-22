from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def generate_pdf(ingredients):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="shoping-list.pdf"'

    pdfmetrics.registerFont(TTFont('FreeSans', 'data/FreeSans.ttf'))

    canvas_obj = canvas.Canvas(response, pagesize=A4)
    canvas_obj.setTitle('СПИСОК ПОКУПОК')

    begin_position_x, begin_position_y = 30, 750

    canvas_obj.setFont('FreeSans', 25)
    canvas_obj.drawString(
        begin_position_x, begin_position_y, 'Список покупок: ')
    begin_position_y -= 35
    canvas_obj.setFont('FreeSans', 18)

    for number, item in enumerate(ingredients, start=1):
        if begin_position_y < 100:
            begin_position_y = 750
            canvas_obj.showPage()
            canvas_obj.setFont('FreeSans', 18)
            canvas_obj.drawString(
                begin_position_x, begin_position_y, 'Список покупок: ')
            begin_position_y -= 35

        begin_position_y -= 10

        canvas_obj.drawString(
            begin_position_x,
            begin_position_y,
            f'№{number}: {item["name"]} - {item["total"]} {item["unit"]} '
        )
        begin_position_y -= 30

    canvas_obj.showPage()
    canvas_obj.save()

    return response
