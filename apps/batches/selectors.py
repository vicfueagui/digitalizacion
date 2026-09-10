from .models import IntakeBatch


def batches_for_user(user):
    if not user.is_authenticated or not user.has_perm("batches.view_intakebatch"):
        return IntakeBatch.objects.none()
    if user.is_superuser or user.has_perm("records.view_all_records"):
        return IntakeBatch.objects.all()
    return IntakeBatch.objects.filter(
        records__assignments__digitalizer=user,
        records__assignments__ended_at__isnull=True,
    ).distinct()
