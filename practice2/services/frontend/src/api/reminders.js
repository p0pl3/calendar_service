import client from './client';

export const getReminders = (params) =>
  client.get('/reminders/', { params }).then((r) => r.data);

export const createReminder = (data) =>
  client.post('/reminders/', data).then((r) => r.data);

export const updateReminder = (id, data) =>
  client.put(`/reminders/${id}`, data).then((r) => r.data);

export const deleteReminder = (id) => client.delete(`/reminders/${id}`);
