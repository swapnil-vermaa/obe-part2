from django.db.models import Avg, Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from attainments.models import Attainment, ProgramAttainment
from courses.models import Course


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = Course.objects.select_related('faculty').all()
        if request.user.is_faculty_role:
            courses = courses.filter(faculty=request.user)

        courses = courses.annotate(
            outcome_count=Count('outcomes', distinct=True),
            attainment_count=Count(
                'attainments',
                filter=Q(attainments__final_attainment__isnull=False),
                distinct=True,
            ),
            avg_final=Avg('attainments__final_attainment'),
            avg_level=Avg('attainments__attainment_level'),
        ).order_by('-academic_year', 'course_code')

        course_rows = list(courses)
        course_ids = [c.id for c in course_rows]

        pending = sum(
            1 for c in course_rows
            if c.outcome_count > 0 and c.attainment_count < c.outcome_count
        )

        attainments = Attainment.objects.filter(course_id__in=course_ids)
        overall_avg = attainments.aggregate(avg=Avg('final_attainment'))['avg']
        po_avg = ProgramAttainment.objects.filter(course_id__in=course_ids).aggregate(avg=Avg('percentage'))['avg']

        level_distribution = {str(i): 0 for i in range(4)}
        for row in attainments.exclude(attainment_level__isnull=True).values('attainment_level').annotate(n=Count('id')):
            level_distribution[str(row['attainment_level'])] = row['n']

        return Response({
            'course_count': len(course_rows),
            'outcome_count': sum(c.outcome_count for c in course_rows),
            'pending_attainment': pending,
            'average_final_attainment': round(float(overall_avg), 2) if overall_avg is not None else None,
            'average_po_attainment': round(float(po_avg), 2) if po_avg is not None else None,
            'level_distribution': level_distribution,
            'courses': [
                {
                    'id': c.id,
                    'course_code': c.course_code,
                    'course_name': c.course_name,
                    'is_lab': c.is_lab,
                    'semester': c.semester,
                    'academic_year': c.academic_year,
                    'outcome_count': c.outcome_count,
                    'attainment_count': c.attainment_count,
                    'avg_final': round(float(c.avg_final), 2) if c.avg_final is not None else None,
                    'avg_level': round(float(c.avg_level), 2) if c.avg_level is not None else None,
                    'faculty_name': (c.faculty.get_full_name() or c.faculty.username) if c.faculty else None,
                    'pending': c.outcome_count > 0 and c.attainment_count < c.outcome_count,
                }
                for c in course_rows
            ],
        })
