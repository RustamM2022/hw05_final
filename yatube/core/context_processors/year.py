from django.utils import timezone


def year(request) -> int:
    real_year = timezone.now()
    return {
        "year": real_year.year
    }
