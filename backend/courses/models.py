from django.conf import settings
from django.db import models


class Course(models.Model):
    """One offering of a subject: unique per faculty + session (academic year)."""
    class Semester(models.TextChoices):
        ODD = 'ODD', 'Odd'
        EVEN = 'EVEN', 'Even'

    course_code = models.CharField(max_length=30)
    course_name = models.CharField(max_length=255)
    program_name = models.CharField(max_length=120, blank=True, help_text='e.g. M.Tech CSE, B.Tech CSE')
    department = models.CharField(max_length=255, blank=True, help_text='e.g. Department of CSE & IT')
    nba_code = models.CharField(max_length=20, blank=True)
    is_lab = models.BooleanField(
        default=False,
        help_text='Lab course offering (separate list; different Students & Marks sub-tabs).',
    )
    semester = models.CharField(max_length=6, choices=Semester.choices)
    academic_year = models.CharField(max_length=20, help_text='Session, e.g. 2024-25 or 2024-2025')
    credits = models.PositiveSmallIntegerField(default=3)
    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courses', limit_choices_to={'role': 'FACULTY'},
    )

    doc_title = models.CharField(max_length=255, default='Detailed Syllabus')
    institute = models.CharField(max_length=255, blank=True)
    institute_sub = models.CharField(max_length=255, blank=True)
    logo_fallback = models.CharField(max_length=80, default='LOGO')
    watermark_text = models.CharField(max_length=80, blank=True)
    coordinator_names = models.CharField(max_length=500, blank=True)

    t1_marks = models.PositiveSmallIntegerField(default=20)
    t2_marks = models.PositiveSmallIntegerField(default=20)
    end_sem_marks = models.PositiveSmallIntegerField(default=35)
    ta_marks = models.PositiveSmallIntegerField(default=25)
    pbl = models.TextField(blank=True)
    po_count = models.PositiveSmallIntegerField(default=3)
    pso_count = models.PositiveSmallIntegerField(default=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-academic_year', 'course_code']
        constraints = [
            models.UniqueConstraint(
                fields=['course_code', 'academic_year', 'faculty'],
                name='unique_course_per_faculty_session',
            ),
        ]

    def __str__(self):
        return f'{self.course_code} — {self.course_name} ({self.academic_year})'

    @property
    def eval_total(self):
        return (self.t1_marks or 0) + (self.t2_marks or 0) + (self.end_sem_marks or 0) + (self.ta_marks or 0)

    def po_pso_keys(self):
        keys = [f'PO{i}' for i in range(1, (self.po_count or 0) + 1)]
        keys += [f'PSO{i}' for i in range(1, (self.pso_count or 0) + 1)]
        return keys


class CourseOutcome(models.Model):
    """SRS 'Course Outcomes' table: CO_ID · Course_ID · CO_Code · Description · Cognitive_Level."""
    class CognitiveLevel(models.TextChoices):
        REMEMBER = 'REMEMBER', 'Remember (C1)'
        UNDERSTAND = 'UNDERSTAND', 'Understand (C2)'
        APPLY = 'APPLY', 'Apply (C3)'
        ANALYZE = 'ANALYZE', 'Analyze (C4)'
        EVALUATE = 'EVALUATE', 'Evaluate (C5)'
        CREATE = 'CREATE', 'Create / Design (C6)'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='outcomes')
    co_code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    cognitive_level = models.CharField(max_length=12, choices=CognitiveLevel.choices)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('course', 'co_code')

    def __str__(self):
        return self.co_code


class CoPoMapping(models.Model):
    """SRS 3.4 CO-PO-PSO Mapping — level 0–3 plus justification used in the CD document."""
    course_outcome = models.ForeignKey(CourseOutcome, on_delete=models.CASCADE, related_name='mappings')
    po_key = models.CharField(max_length=8)
    level = models.PositiveSmallIntegerField(null=True, blank=True)
    justification = models.TextField(blank=True)

    class Meta:
        unique_together = ('course_outcome', 'po_key')

    def __str__(self):
        return f'{self.course_outcome.co_code} → {self.po_key} = {self.level}'


class LectureModule(models.Model):
    """Lecture-wise breakup / module plan for the Course Description."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    order = models.PositiveSmallIntegerField(default=0)
    serial_no = models.CharField(max_length=10, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    topics = models.TextField(blank=True)
    lectures = models.PositiveSmallIntegerField(default=0)
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.course.course_code} module {self.serial_no or self.order}'


class CourseBook(models.Model):
    class Kind(models.TextChoices):
        TEXT = 'TEXT', 'Text Book'
        REFERENCE = 'REFERENCE', 'Reference Book'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='books')
    kind = models.CharField(max_length=12, choices=Kind.choices)
    title = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['kind', 'order']

    def __str__(self):
        return self.title[:60]
