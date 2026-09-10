from django.core.validators import RegexValidator
from django.db import models

from apps.core.models import TimeStampedModel

from .validators import normalize_curp, validate_curp


class EmploymentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Activo"
    INACTIVE = "INACTIVE", "Inactivo"
    UNKNOWN = "UNKNOWN", "No informado"


class AdministrativeSystem(TimeStampedModel):
    code = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(r"^[A-Z0-9_]+$", "Use letras, números y guion bajo.")],
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "sistema administrativo"
        verbose_name_plural = "sistemas administrativos"

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Person(TimeStampedModel):
    curp = models.CharField(max_length=18, unique=True, validators=[validate_curp])
    full_name = models.CharField(max_length=250, blank=True)
    employment_status = models.CharField(
        max_length=10,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.UNKNOWN,
    )
    systems = models.ManyToManyField(
        AdministrativeSystem,
        through="PersonSystemMembership",
        related_name="people",
        blank=True,
    )

    class Meta:
        ordering = ("curp",)
        verbose_name = "persona"
        verbose_name_plural = "personas"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(curp__regex=r"^[A-Z0-9]{18}$"),
                name="people_person_curp_basic_format",
            )
        ]

    def clean(self):
        self.curp = normalize_curp(self.curp)
        validate_curp(self.curp)

    def save(self, *args, **kwargs):
        self.curp = normalize_curp(self.curp)
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.curp} · {self.full_name}" if self.full_name else self.curp


class PersonSystemMembership(models.Model):
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="system_memberships")
    system = models.ForeignKey(
        AdministrativeSystem,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    first_seen_in = models.ForeignKey(
        "sources.PayrollImport",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="memberships_first_seen",
    )
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("person", "system"), name="unique_person_system")
        ]
        verbose_name = "pertenencia administrativa"
        verbose_name_plural = "pertenencias administrativas"

    def __str__(self):
        return f"{self.person.curp} · {self.system.code}"
