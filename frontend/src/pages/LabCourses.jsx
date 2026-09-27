import React from 'react';
import Courses from './Courses';

/** Lab Courses listing — same UI as Courses, separate dataset (is_lab=true). */
export default function LabCourses() {
  return <Courses isLab />;
}
