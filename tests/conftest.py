"""Helper condivisi: generatore di PDF minimi per i test."""


def pdf_minimo(testo: str) -> bytes:
    """Costruisce un PDF di una pagina con una riga di testo, senza dipendenze."""
    contenuto = f"BT /F1 12 Tf 72 720 Td ({testo}) Tj ET".encode("latin-1")
    oggetti = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(contenuto), contenuto),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    corpo = bytearray(b"%PDF-1.4\n")
    posizioni = []
    for i, oggetto in enumerate(oggetti, 1):
        posizioni.append(len(corpo))
        corpo += b"%d 0 obj\n%s\nendobj\n" % (i, oggetto)
    inizio_xref = len(corpo)
    corpo += b"xref\n0 %d\n0000000000 65535 f \n" % (len(oggetti) + 1)
    for posizione in posizioni:
        corpo += b"%010d 00000 n \n" % posizione
    corpo += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(oggetti) + 1,
        inizio_xref,
    )
    return bytes(corpo)
