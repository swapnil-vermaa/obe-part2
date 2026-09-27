import React from 'react';
import { NavLink } from 'react-router-dom';
import useCourseNav, { useCourseTypeRedirect } from '../hooks/useCourseNav';

export default function CourseSubnav({ courseId, course }) {
  const { basePath } = useCourseNav();
  useCourseTypeRedirect(course);
  const link = 'px-3 py-1.5 rounded text-sm font-medium';
  const active = 'bg-slate-900 text-white';
  const idle = 'text-slate-600 hover:bg-slate-100';

  return (
    <div className="flex flex-wrap gap-2 mb-6 no-print">
      <NavLink
        to={`${basePath}/${courseId}/description`}
        className={({ isActive }) => `${link} ${isActive ? active : idle}`}
      >
        Course Description
      </NavLink>
      <NavLink
        to={`${basePath}/${courseId}/opening-report`}
        className={({ isActive }) => `${link} ${isActive ? active : idle}`}
      >
        Opening Report
      </NavLink>
      <NavLink
        to={`${basePath}/${courseId}`}
        end
        className={({ isActive }) => `${link} ${isActive ? active : idle}`}
      >
        Attainment
      </NavLink>
      <NavLink
        to={`${basePath}/${courseId}/assessments`}
        className={({ isActive }) => `${link} ${isActive ? active : idle}`}
      >
        Students & Marks
      </NavLink>
      <NavLink
        to={`${basePath}/${courseId}/assessment-tools`}
        className={({ isActive }) => `${link} ${isActive ? active : idle}`}
      >
        Assessment Tools
      </NavLink>
      <NavLink
        to={`${basePath}/${courseId}/closing-report`}
        className={({ isActive }) => `${link} ${isActive ? active : idle}`}
      >
        Closing Report
      </NavLink>
    </div>
  );
}
