from .models import PersonnelRecord


def records_for_user(user):
    if not user.is_authenticated:
        return PersonnelRecord.objects.none()
    queryset = PersonnelRecord.objects.all()
    if user.is_superuser or user.has_perm("records.view_all_records"):
        return queryset
    if user.has_perm("records.view_personnelrecord"):
        return queryset.filter(assignments__digitalizer=user, assignments__ended_at__isnull=True).distinct()
    return queryset.none()


def user_can_access_record(user, record):
    return records_for_user(user).filter(pk=record.pk).exists()
