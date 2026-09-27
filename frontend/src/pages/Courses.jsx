import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

const emptyForm = {
  course_code: '', course_name: '', program_name: '', nba_code: '', semester: 'ODD',
  academic_year: '', credits: 3, faculty: '', po_count: 3, pso_count: 2,
};

export default function Courses({ isLab = false }) {
  const { isAdmin } = useAuth();
  const [courses, setCourses] = useState([]);
  const [facultyList, setFacultyList] = useState([]);
  const [sessionFilter, setSessionFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState('');

  const basePath = isLab ? '/lab-courses' : '/courses';
  const title = isLab ? 'Lab Courses' : 'Courses';
  const newLabel = isLab ? '+ New Lab Course' : '+ New Course';
  const formTitle = editingId
    ? (isLab ? 'Edit lab course' : 'Edit course')
    : (isLab ? 'New lab course' : 'New course');
  const submitLabel = editingId
    ? (isLab ? 'Update Lab Course' : 'Update Course')
    : (isLab ? 'Create Lab Course' : 'Create Course');

  function load() {
    api.get('/courses/', { params: { is_lab: isLab } }).then((res) => setCourses(res.data.results ?? res.data));
    if (isAdmin) {
      api.get('/auth/users/?role=FACULTY').then((res) => setFacultyList(res.data.results ?? res.data));
    }
  }

  useEffect(load, [isAdmin, isLab]);

  const sessions = [...new Set(courses.map((c) => c.academic_year).filter(Boolean))];
  const visible = sessionFilter ? courses.filter((c) => c.academic_year === sessionFilter) : courses;

  function resetForm() {
    setShowForm(false);
    setEditingId(null);
    setForm(emptyForm);
    setError('');
  }

  function startEdit(c, e) {
    e.preventDefault();
    e.stopPropagation();
    setEditingId(c.id);
    setShowForm(true);
    setError('');
    setForm({
      course_code: c.course_code || '',
      course_name: c.course_name || '',
      program_name: c.program_name || '',
      nba_code: c.nba_code || '',
      semester: c.semester || 'ODD',
      academic_year: c.academic_year || '',
      credits: c.credits ?? 3,
      faculty: c.faculty ?? '',
      po_count: c.po_count ?? 3,
      pso_count: c.pso_count ?? 2,
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    const payload = {
      course_code: form.course_code,
      course_name: form.course_name,
      program_name: form.program_name,
      nba_code: form.nba_code,
      is_lab: isLab,
      semester: form.semester,
      academic_year: form.academic_year,
      credits: Number(form.credits) || 3,
      po_count: Number(form.po_count) || 3,
      pso_count: Number(form.pso_count) || 0,
    };
    if (isAdmin) {
      payload.faculty = form.faculty ? Number(form.faculty) : null;
    }
    try {
      if (editingId) {
        await api.patch(`/courses/${editingId}/`, payload);
      } else {
        await api.post('/courses/', { ...payload, outcomes: [] });
      }
      resetForm();
      load();
    } catch (err) {
      setError(JSON.stringify(err.response?.data || 'Failed to save course'));
    }
  }

  async function deleteCourse(c, e) {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm(`Delete ${c.course_code} — ${c.course_name}? Students, marks, and mapping will also be removed.`)) return;
    setError('');
    try {
      await api.delete(`/courses/${c.id}/`);
      if (editingId === c.id) resetForm();
      load();
    } catch (err) {
      setError(JSON.stringify(err.response?.data || 'Failed to delete course'));
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6 gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
          {sessions.length > 0 && (
            <select className="border rounded px-2 py-1.5 text-sm" value={sessionFilter} onChange={(e) => setSessionFilter(e.target.value)}>
              <option value="">All sessions</option>
              {sessions.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          )}
        </div>
        <button
          onClick={() => { if (showForm) resetForm(); else { setShowForm(true); setEditingId(null); setForm(emptyForm); } }}
          className="bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 rounded text-sm font-semibold"
        >
          {showForm ? 'Cancel' : newLabel}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 mb-6 grid grid-cols-2 gap-4">
          {error && <div className="col-span-2 bg-red-50 text-red-700 text-xs rounded p-2">{error}</div>}
          <p className="col-span-2 text-sm font-semibold text-slate-700">
            {formTitle}
          </p>
          <input placeholder="Course Code (e.g. 17M11CS111)" className="border rounded px-3 py-2 text-sm"
            value={form.course_code} onChange={(e) => setForm({ ...form, course_code: e.target.value })} required />
          <input placeholder="NBA Code (e.g. C110)" className="border rounded px-3 py-2 text-sm"
            value={form.nba_code} onChange={(e) => setForm({ ...form, nba_code: e.target.value })} />
          <input placeholder="Course / subject name" className="border rounded px-3 py-2 text-sm col-span-2"
            value={form.course_name} onChange={(e) => setForm({ ...form, course_name: e.target.value })} required />
          <input placeholder="Program" className="border rounded px-3 py-2 text-sm col-span-2"
            value={form.program_name} onChange={(e) => setForm({ ...form, program_name: e.target.value })} />
          <select className="border rounded px-3 py-2 text-sm" value={form.semester}
            onChange={(e) => setForm({ ...form, semester: e.target.value })}>
            <option value="ODD">Odd</option>
            <option value="EVEN">Even</option>
          </select>
          <label className="block text-sm">
            <span className="block text-xs font-medium text-slate-600 mb-1">Session / academic year</span>
            <input placeholder="e.g. 2024-25" className="w-full border rounded px-3 py-2 text-sm"
              value={form.academic_year} onChange={(e) => setForm({ ...form, academic_year: e.target.value })} required />
          </label>
          <label className="block text-sm">
            <span className="block text-xs font-medium text-slate-600 mb-1">Credits</span>
            <input type="number" className="w-full border rounded px-3 py-2 text-sm"
              value={form.credits} onChange={(e) => setForm({ ...form, credits: Number(e.target.value) })} />
          </label>
          <label className="block text-sm">
            <span className="block text-xs font-medium text-slate-600 mb-1">Number of POs</span>
            <input type="number" min="1" max="15" className="w-full border rounded px-3 py-2 text-sm"
              value={form.po_count} onChange={(e) => setForm({ ...form, po_count: Number(e.target.value) })} />
          </label>
          <label className="block text-sm">
            <span className="block text-xs font-medium text-slate-600 mb-1">Number of PSOs</span>
            <input type="number" min="0" max="8" className="w-full border rounded px-3 py-2 text-sm"
              value={form.pso_count} onChange={(e) => setForm({ ...form, pso_count: Number(e.target.value) })} />
          </label>
          {isAdmin && (
            <select className="border rounded px-3 py-2 text-sm" value={form.faculty}
              onChange={(e) => setForm({ ...form, faculty: e.target.value })}>
              <option value="">Assign faculty later</option>
              {facultyList.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.first_name} {f.last_name} (@{f.username})
                </option>
              ))}
            </select>
          )}
          <button type="submit" className="col-span-2 bg-slate-900 text-white py-2 rounded text-sm font-semibold">
            {submitLabel}
          </button>
        </form>
      )}

      {!showForm && error && <div className="bg-red-50 text-red-700 text-xs rounded p-2 mb-4">{error}</div>}

      <div className="bg-white shadow rounded-lg divide-y">
        {visible.length === 0 && (
          <p className="p-6 text-sm text-slate-400">
            {isLab ? 'No lab courses yet — create one above.' : 'No courses yet — create one above.'}
          </p>
        )}
        {visible.map((c) => (
          <div key={c.id} className="flex items-center justify-between p-4 hover:bg-slate-50 gap-3">
            <Link to={`${basePath}/${c.id}`} className="min-w-0 flex-1">
              <p className="font-semibold text-slate-900">{c.course_code} — {c.course_name}</p>
              <p className="text-xs text-slate-500">
                {c.program_name ? `${c.program_name} · ` : ''}Session {c.academic_year} · {c.semester} · {c.credits} credits
                {c.faculty_name ? ` · ${c.faculty_name}` : ' · Unassigned'}
              </p>
            </Link>
            <div className="flex items-center gap-3 shrink-0">
              <span className="text-xs text-slate-400">{c.outcomes?.length ?? 0} COs</span>
              <button type="button" onClick={(e) => startEdit(c, e)} className="text-xs text-slate-600 hover:underline">Edit</button>
              <button type="button" onClick={(e) => deleteCourse(c, e)} className="text-xs text-red-600 hover:underline">Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
