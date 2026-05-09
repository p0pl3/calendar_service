import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { getEvent, updateEvent, deleteEvent } from '../api/events';
import { getReminders, createReminder, deleteReminder } from '../api/reminders';

const s = {
  page: { minHeight: '100vh', background: '#f5f7fb' },
  nav: { background: '#4f46e5', color: '#fff', padding: '1rem 2rem', display: 'flex', gap: '1rem', alignItems: 'center' },
  backBtn: { background: 'rgba(255,255,255,0.2)', border: 'none', color: '#fff', padding: '0.4rem 0.9rem', borderRadius: '4px', cursor: 'pointer' },
  navTitle: { fontWeight: 700, fontSize: '1.1rem' },
  main: { maxWidth: '700px', margin: '2rem auto', padding: '0 1rem' },
  card: { background: '#fff', borderRadius: '8px', padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', marginBottom: '1.5rem' },
  title: { fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' },
  meta: { color: '#6b7280', fontSize: '0.9rem', marginBottom: '0.3rem' },
  desc: { marginTop: '0.75rem', lineHeight: 1.6 },
  sectionTitle: { fontWeight: 700, marginBottom: '0.75rem', fontSize: '1.05rem' },
  reminderItem: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.6rem 0', borderBottom: '1px solid #f3f4f6' },
  reminderInfo: { fontSize: '0.9rem' },
  badge: { fontSize: '0.7rem', padding: '0.15rem 0.4rem', borderRadius: '3px', background: '#e0e7ff', color: '#3730a3', marginLeft: '0.3rem' },
  deleteBtn: { background: '#fee2e2', color: '#dc2626', border: 'none', padding: '0.3rem 0.6rem', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' },
  form: { marginTop: '1rem', display: 'grid', gap: '0.6rem' },
  input: { width: '100%', padding: '0.5rem 0.7rem', border: '1px solid #ddd', borderRadius: '4px', fontSize: '0.95rem' },
  label: { fontSize: '0.8rem', color: '#555', display: 'block', marginBottom: '0.15rem' },
  addBtn: { background: '#4f46e5', color: '#fff', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' },
  dangerBtn: { background: '#dc2626', color: '#fff', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer' },
  btnRow: { display: 'flex', gap: '0.5rem', marginTop: '1rem' },
  checkboxRow: { display: 'flex', gap: '1rem', alignItems: 'center' },
};

export default function EventDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [reminders, setReminders] = useState([]);
  const [reminderForm, setReminderForm] = useState({ remind_at: '', channels: ['email'], message: '', });

  useEffect(() => {
    getEvent(id).then(setEvent).catch(() => navigate('/'));
    getReminders({ event_id: id }).then(setReminders).catch(() => {});
  }, [id, navigate]);

  const handleDeleteEvent = async () => {
    if (!window.confirm('Удалить событие?')) return;
    await deleteEvent(id);
    navigate('/');
  };

  const toggleChannel = (ch) => {
    setReminderForm((f) => ({
      ...f,
      channels: f.channels.includes(ch) ? f.channels.filter((c) => c !== ch) : [...f.channels, ch],
    }));
  };

  const handleAddReminder = async (e) => {
    e.preventDefault();
    try {
      const data = await createReminder({
        event_id: id,
        remind_at: new Date(reminderForm.remind_at).toISOString(),
        channels: reminderForm.channels,
        message: reminderForm.message || undefined,
      });
      setReminders((r) => [...r, data]);
      setReminderForm({ remind_at: '', channels: ['email'], message: '' });
    } catch (err) {
      alert(err.response?.data?.detail || 'Error creating reminder');
    }
  };

  const handleDeleteReminder = async (rid) => {
    await deleteReminder(rid);
    setReminders((r) => r.filter((x) => x.id !== rid));
  };

  if (!event) return <div style={{ padding: '2rem' }}>Загрузка...</div>;

  return (
    <div style={s.page}>
      <nav style={s.nav}>
        <button style={s.backBtn} onClick={() => navigate('/')}>← Назад</button>
        <span style={s.navTitle}>{event.title}</span>
      </nav>
      <div style={s.main}>
        <div style={s.card}>
          <div style={s.title}>{event.title}</div>
          <div style={s.meta}>Начало: {format(new Date(event.start_time), 'dd MMMM yyyy HH:mm', { locale: ru })}</div>
          {event.end_time && <div style={s.meta}>Конец: {format(new Date(event.end_time), 'dd MMMM yyyy HH:mm', { locale: ru })}</div>}
          {event.location && <div style={s.meta}>Место: {event.location}</div>}
          {event.description && <div style={s.desc}>{event.description}</div>}
          <div style={s.btnRow}>
            <button style={s.dangerBtn} onClick={handleDeleteEvent}>Удалить событие</button>
          </div>
        </div>

        <div style={s.card}>
          <div style={s.sectionTitle}>Напоминания ({reminders.length})</div>
          {reminders.map((r) => (
            <div key={r.id} style={s.reminderItem}>
              <div style={s.reminderInfo}>
                {format(new Date(r.remind_at), 'dd.MM.yyyy HH:mm')}
                {r.channels.map((ch) => <span key={ch} style={s.badge}>{ch}</span>)}
                {r.message && <span style={{ ...s.badge, background: '#fef9c3', color: '#713f12' }}>{r.message}</span>}
                <span style={{ ...s.badge, background: r.status === 'pending' ? '#dcfce7' : '#f3f4f6', color: r.status === 'pending' ? '#166534' : '#6b7280' }}>{r.status}</span>
              </div>
              <button style={s.deleteBtn} onClick={() => handleDeleteReminder(r.id)}>×</button>
            </div>
          ))}

          <form onSubmit={handleAddReminder} style={s.form}>
            <div>
              <label style={s.label}>Время напоминания</label>
              <input style={s.input} type="datetime-local" value={reminderForm.remind_at} onChange={(e) => setReminderForm({ ...reminderForm, remind_at: e.target.value })} required />
            </div>
            <div>
              <label style={s.label}>Каналы</label>
              <div style={s.checkboxRow}>
                <label style={{ display: 'flex', gap: '0.3rem', alignItems: 'center', cursor: 'pointer' }}>
                  <input type="checkbox" checked={reminderForm.channels.includes('email')} onChange={() => toggleChannel('email')} />
                  email
                </label>
              </div>
            </div>
            <div>
              <label style={s.label}>Сообщение (необязательно)</label>
              <input style={s.input} value={reminderForm.message} onChange={(e) => setReminderForm({ ...reminderForm, message: e.target.value })} placeholder="Текст напоминания..." />
            </div>
            <button type="submit" style={s.addBtn}>Добавить напоминание</button>
          </form>
        </div>
      </div>
    </div>
  );
}
