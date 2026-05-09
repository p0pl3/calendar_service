import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { addMonths, format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, isSameMonth, startOfWeek, endOfWeek } from 'date-fns';
import { ru } from 'date-fns/locale';
import { getEvents, createEvent, deleteEvent } from '../api/events';
import { logout } from '../api/auth';

const s = {
  page: { minHeight: '100vh', background: '#f5f7fb' },
  nav: { background: '#4f46e5', color: '#fff', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  navTitle: { fontWeight: 700, fontSize: '1.2rem' },
  navBtn: { background: 'rgba(255,255,255,0.2)', border: 'none', color: '#fff', padding: '0.4rem 0.9rem', borderRadius: '4px', cursor: 'pointer' },
  main: { maxWidth: '900px', margin: '2rem auto', padding: '0 1rem' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' },
  monthNav: { display: 'flex', gap: '0.5rem', alignItems: 'center' },
  monthBtn: { background: '#e0e7ff', border: 'none', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer' },
  monthLabel: { fontWeight: 600, fontSize: '1.1rem', minWidth: '160px', textAlign: 'center' },
  addBtn: { background: '#4f46e5', color: '#fff', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '1px', background: '#ddd', border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden' },
  dayHeader: { background: '#f3f4f6', padding: '0.5rem', textAlign: 'center', fontSize: '0.75rem', fontWeight: 600, color: '#6b7280' },
  day: { background: '#fff', minHeight: '90px', padding: '0.4rem', cursor: 'pointer' },
  dayOther: { background: '#fafafa', minHeight: '90px', padding: '0.4rem' },
  dayToday: { background: '#eef2ff' },
  dayNum: { fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.2rem' },
  eventChip: { background: '#c7d2fe', color: '#3730a3', fontSize: '0.7rem', padding: '0.1rem 0.3rem', borderRadius: '3px', marginBottom: '0.15rem', cursor: 'pointer', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  modal: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 },
  modalCard: { background: '#fff', borderRadius: '8px', padding: '2rem', width: '100%', maxWidth: '480px', boxShadow: '0 8px 32px rgba(0,0,0,0.15)' },
  modalTitle: { fontWeight: 700, fontSize: '1.1rem', marginBottom: '1rem' },
  field: { marginBottom: '0.8rem' },
  label: { display: 'block', fontSize: '0.8rem', color: '#555', marginBottom: '0.2rem' },
  input: { width: '100%', padding: '0.5rem 0.7rem', border: '1px solid #ddd', borderRadius: '4px', fontSize: '0.95rem' },
  btnRow: { display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' },
  cancelBtn: { background: '#f3f4f6', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' },
  submitBtn: { background: '#4f46e5', color: '#fff', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' },
};

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
const today = new Date();

export default function CalendarPage() {
  const [currentMonth, setCurrentMonth] = useState(startOfMonth(today));
  const [events, setEvents] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', start_time: '', end_time: '', location: '' });
  const navigate = useNavigate();

  const loadEvents = useCallback(async () => {
    try {
      const from_date = startOfMonth(currentMonth).toISOString();
      const to_date = endOfMonth(currentMonth).toISOString();
      const data = await getEvents({ from_date, to_date, limit: 500 });
      setEvents(data);
    } catch (_) {}
  }, [currentMonth]);

  useEffect(() => { loadEvents(); }, [loadEvents]);

  const calStart = startOfWeek(startOfMonth(currentMonth), { weekStartsOn: 1 });
  const calEnd = endOfWeek(endOfMonth(currentMonth), { weekStartsOn: 1 });
  const days = eachDayOfInterval({ start: calStart, end: calEnd });

  const eventsOnDay = (day) => events.filter((e) => isSameDay(new Date(e.start_time), day));

  const handleLogout = async () => {
    try { await logout(); } catch (_) {}
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await createEvent({ ...form, start_time: new Date(form.start_time).toISOString(), end_time: form.end_time ? new Date(form.end_time).toISOString() : undefined });
      setShowModal(false);
      setForm({ title: '', description: '', start_time: '', end_time: '', location: '' });
      loadEvents();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error creating event');
    }
  };

  return (
    <div style={s.page}>
      <nav style={s.nav}>
        <span style={s.navTitle}>Календарь событий</span>
        <button style={s.navBtn} onClick={handleLogout}>Выйти</button>
      </nav>
      <div style={s.main}>
        <div style={s.header}>
          <div style={s.monthNav}>
            <button style={s.monthBtn} onClick={() => setCurrentMonth((m) => addMonths(m, -1))}>‹</button>
            <span style={s.monthLabel}>{format(currentMonth, 'LLLL yyyy', { locale: ru })}</span>
            <button style={s.monthBtn} onClick={() => setCurrentMonth((m) => addMonths(m, 1))}>›</button>
          </div>
          <button style={s.addBtn} onClick={() => setShowModal(true)}>+ Новое событие</button>
        </div>
        <div style={s.grid}>
          {WEEKDAYS.map((d) => <div key={d} style={s.dayHeader}>{d}</div>)}
          {days.map((day) => {
            const isOther = !isSameMonth(day, currentMonth);
            const isToday = isSameDay(day, today);
            return (
              <div key={day.toISOString()} style={{ ...(isOther ? s.dayOther : s.day), ...(isToday ? s.dayToday : {}) }}>
                <div style={s.dayNum}>{format(day, 'd')}</div>
                {eventsOnDay(day).map((ev) => (
                  <div key={ev.id} style={s.eventChip} onClick={() => navigate(`/events/${ev.id}`)} title={ev.title}>
                    {ev.title}
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>

      {showModal && (
        <div style={s.modal} onClick={() => setShowModal(false)}>
          <div style={s.modalCard} onClick={(e) => e.stopPropagation()}>
            <div style={s.modalTitle}>Новое событие</div>
            <form onSubmit={handleCreate}>
              {[['title', 'Название *'], ['description', 'Описание'], ['location', 'Место']].map(([name, label]) => (
                <div key={name} style={s.field}>
                  <label style={s.label}>{label}</label>
                  <input style={s.input} value={form[name]} onChange={(e) => setForm({ ...form, [name]: e.target.value })} required={name === 'title'} />
                </div>
              ))}
              <div style={s.field}>
                <label style={s.label}>Начало *</label>
                <input style={s.input} type="datetime-local" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} required />
              </div>
              <div style={s.field}>
                <label style={s.label}>Конец</label>
                <input style={s.input} type="datetime-local" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
              </div>
              <div style={s.btnRow}>
                <button type="button" style={s.cancelBtn} onClick={() => setShowModal(false)}>Отмена</button>
                <button type="submit" style={s.submitBtn}>Создать</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
