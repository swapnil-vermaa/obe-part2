from django.db import transaction
from rest_framework import serializers
from .access import faculty_owns_course
from .models import Course, CourseOutcome, CoPoMapping, LectureModule, CourseBook


class CoPoMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoPoMapping
        fields = ['id', 'course_outcome', 'po_key', 'level', 'justification']

    def validate_course_outcome(self, course_outcome):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and not faculty_owns_course(user, course_outcome.course):
            raise serializers.ValidationError('You can only map outcomes on your own courses.')
        return course_outcome


class CourseOutcomeSerializer(serializers.ModelSerializer):
    mappings = CoPoMappingSerializer(many=True, required=False)

    class Meta:
        model = CourseOutcome
        fields = ['id', 'course', 'co_code', 'description', 'cognitive_level', 'order', 'mappings']
        extra_kwargs = {'description': {'required': False, 'allow_blank': True}}

    def validate_course(self, course):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and not faculty_owns_course(user, course):
            raise serializers.ValidationError('You can only edit outcomes on your own courses.')
        return course

    def create(self, validated_data):
        mappings_data = validated_data.pop('mappings', [])
        co = CourseOutcome.objects.create(**validated_data)
        for m in mappings_data:
            CoPoMapping.objects.create(course_outcome=co, **m)
        return co

    def update(self, instance, validated_data):
        mappings_data = validated_data.pop('mappings', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if mappings_data is not None:
            instance.mappings.all().delete()
            for m in mappings_data:
                CoPoMapping.objects.create(course_outcome=instance, **m)
        return instance


class LectureModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LectureModule
        fields = ['id', 'order', 'serial_no', 'subtitle', 'topics', 'lectures', 'remarks']
        extra_kwargs = {'id': {'read_only': False, 'required': False}}


class CourseSerializer(serializers.ModelSerializer):
    outcomes = CourseOutcomeSerializer(many=True, required=False)
    faculty_name = serializers.SerializerMethodField()
    modules = LectureModuleSerializer(many=True, required=False)
    text_books = serializers.ListField(child=serializers.CharField(allow_blank=True), required=False, write_only=True)
    reference_books = serializers.ListField(child=serializers.CharField(allow_blank=True), required=False, write_only=True)
    eval_total = serializers.IntegerField(read_only=True)
    po_pso_keys = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'course_code', 'course_name', 'program_name', 'department', 'nba_code', 'is_lab',
            'semester', 'academic_year',
            'credits', 'faculty', 'faculty_name', 'outcomes', 'created_at',
            'doc_title', 'institute', 'institute_sub', 'logo_fallback', 'watermark_text',
            'coordinator_names', 't1_marks', 't2_marks', 'end_sem_marks', 'ta_marks',
            'pbl', 'eval_total', 'modules', 'text_books', 'reference_books',
            'po_count', 'pso_count', 'po_pso_keys',
        ]
        extra_kwargs = {
            'faculty': {'required': False, 'allow_null': True},
            'program_name': {'required': False, 'allow_blank': True},
            'department': {'required': False, 'allow_blank': True},
            'nba_code': {'required': False, 'allow_blank': True},
            'is_lab': {'required': False},
        }
        # UniqueConstraint(course_code, academic_year, faculty) would otherwise
        # force faculty in the payload. Faculty users are assigned in validate().
        validators = []

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_faculty_role', False):
            attrs['faculty'] = user
        faculty = attrs.get('faculty', getattr(self.instance, 'faculty', None))
        code = attrs.get('course_code', getattr(self.instance, 'course_code', None))
        year = attrs.get('academic_year', getattr(self.instance, 'academic_year', None))
        if code and year:
            qs = Course.objects.filter(course_code=code, academic_year=year, faculty=faculty)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    'This course code already exists for this faculty in this session.'
                )
        return attrs

    def get_faculty_name(self, obj):
        if not obj.faculty:
            return None
        return obj.faculty.get_full_name() or obj.faculty.username

    def get_po_pso_keys(self, obj):
        return obj.po_pso_keys()

    def validate_po_count(self, value):
        if value < 1 or value > 15:
            raise serializers.ValidationError('PO count must be between 1 and 15.')
        return value

    def validate_pso_count(self, value):
        if value < 0 or value > 8:
            raise serializers.ValidationError('PSO count must be between 0 and 8.')
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        books = list(instance.books.all())
        data['text_books'] = [b.title for b in books if b.kind == CourseBook.Kind.TEXT]
        data['reference_books'] = [b.title for b in books if b.kind == CourseBook.Kind.REFERENCE]
        return data

    def _replace_modules(self, course, modules_data):
        course.modules.all().delete()
        for i, row in enumerate(modules_data):
            row = dict(row)
            row.pop('id', None)
            serial = row.get('serial_no') or f'{i + 1}.'
            LectureModule.objects.create(
                course=course,
                order=i,
                serial_no=serial,
                subtitle=row.get('subtitle') or '',
                topics=row.get('topics') or '',
                lectures=row.get('lectures') or 0,
                remarks=row.get('remarks') or '',
            )

    def _replace_books(self, course, text_books, reference_books):
        if text_books is None and reference_books is None:
            return
        if text_books is not None:
            course.books.filter(kind=CourseBook.Kind.TEXT).delete()
            for i, title in enumerate(text_books):
                if str(title).strip():
                    CourseBook.objects.create(course=course, kind=CourseBook.Kind.TEXT, title=title.strip(), order=i)
        if reference_books is not None:
            course.books.filter(kind=CourseBook.Kind.REFERENCE).delete()
            for i, title in enumerate(reference_books):
                if str(title).strip():
                    CourseBook.objects.create(course=course, kind=CourseBook.Kind.REFERENCE, title=title.strip(), order=i)

    def create(self, validated_data):
        with transaction.atomic():
            outcomes_data = validated_data.pop('outcomes', [])
            modules_data = validated_data.pop('modules', [])
            text_books = validated_data.pop('text_books', [])
            reference_books = validated_data.pop('reference_books', [])
            course = Course.objects.create(**validated_data)
            for i, co_data in enumerate(outcomes_data):
                mappings_data = co_data.pop('mappings', [])
                co_data.pop('order', None)
                co = CourseOutcome.objects.create(course=course, order=i, **co_data)
                for m in mappings_data:
                    CoPoMapping.objects.create(course_outcome=co, **m)
            self._replace_modules(course, modules_data)
            self._replace_books(course, text_books, reference_books)
            return course

    def update(self, instance, validated_data):
        with transaction.atomic():
            outcomes_data = validated_data.pop('outcomes', None)
            modules_data = validated_data.pop('modules', None)
            text_books = validated_data.pop('text_books', None)
            reference_books = validated_data.pop('reference_books', None)
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            allowed = set(instance.po_pso_keys())
            CoPoMapping.objects.filter(course_outcome__course=instance).exclude(po_key__in=allowed).delete()
            if modules_data is not None:
                self._replace_modules(instance, modules_data)
            self._replace_books(instance, text_books, reference_books)
            if outcomes_data is not None:
                # Outcomes are managed via /outcomes/; ignore accidental nested replace on PATCH.
                pass
            return instance
