import { useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

/** Resolve /courses vs /lab-courses base path from the current URL. */
export default function useCourseNav() {
  const { pathname } = useLocation();
  const isLabRoute = pathname.startsWith('/lab-courses');
  const basePath = isLabRoute ? '/lab-courses' : '/courses';
  const listLabel = isLabRoute ? 'Lab Courses' : 'Courses';
  return { isLabRoute, basePath, listLabel };
}

/** Keep URL base (/courses vs /lab-courses) in sync with course.is_lab. */
export function useCourseTypeRedirect(course) {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { isLabRoute } = useCourseNav();

  useEffect(() => {
    if (!course || course.is_lab == null) return;
    if (!!course.is_lab === isLabRoute) return;
    const suffix = location.pathname.replace(/^\/(lab-)?courses\/[^/]+/, '') || '';
    const base = course.is_lab ? '/lab-courses' : '/courses';
    navigate(`${base}/${id}${suffix}`, { replace: true });
  }, [course, isLabRoute, id, location.pathname, navigate]);
}
