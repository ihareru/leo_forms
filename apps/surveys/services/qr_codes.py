from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_M


def generate_qr_code_png(data: str) -> bytes:
    """
    Создаёт QR-код в формате PNG.

    В QR-код записывается абсолютная публичная ссылка на форму.
    """

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    buffer = BytesIO()
    image.save(
        buffer,
        format="PNG",
    )

    return buffer.getvalue()