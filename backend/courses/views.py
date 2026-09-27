from rest_framework import viewsets, permissions
from .models import Course, CourseOutcome, CoPoMapping
from .serializers import CourseSerializer, CourseOutcomeSerializer, CoPoMappingSerializer


def faculty_course_qs(user, qs):
    if user.is_faculty_role:
        return qs.filter(faculty=user)
    return qs


class CourseViewSet(viewsets.ModelViewSet):
    """
    Faculty see only their own course offerings (per session).
    Admins see everything and can assign faculty.
    """
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = Course.objects.prefetch_related('outcomes__mappings', 'modules', 'books').select_related('faculty')
        qs = faculty_course_qs(self.request.user, qs)
        year = self.request.query_params.get('academic_year') or self.request.query_params.get('session')
        if year:
            qs = qs.filter(academic_year=year)
        is_lab = self.request.query_params.get('is_lab')
        if is_lab is not None and is_lab != '':
            qs = qs.filter(is_lab=str(is_lab).lower() in ('1', 'true', 'yes'))
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        extra = {}
        if user.is_faculty_role:
            extra['faculty'] = user
            if not serializer.validated_data.get('coordinator_names'):
                extra['coordinator_names'] = user.get_full_name() or user.username
        serializer.save(**extra)

    def perform_update(self, serializer):
        if self.request.user.is_faculty_role:
            serializer.save(faculty=self.request.user)
        else:
            serializer.save()


class CourseOutcomeViewSet(viewsets.ModelViewSet):
    serializer_class = CourseOutcomeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = CourseOutcome.objects.select_related('course').prefetch_related('mappings')
        if self.request.user.is_faculty_role:
            qs = qs.filter(course__faculty=self.request.user)
        course_id = self.request.query_params.get('course')
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


class CoPoMappingViewSet(viewsets.ModelViewSet):
    serializer_class = CoPoMappingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = CoPoMapping.objects.select_related('course_outcome__course')
        if self.request.user.is_faculty_role:
            qs = qs.filter(course_outcome__course__faculty=self.request.user)
        return qs
