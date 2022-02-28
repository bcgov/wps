from app.utils.daily_pdf_gen import generate_daily_pdf


def test_ros():
    assert generate_daily_pdf() == True
