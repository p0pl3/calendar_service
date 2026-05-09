import client from './client';

export const register = (data) =>
  client.post('/auth/register', data).then((r) => r.data);

export const login = async (email, password) => {
  const params = new URLSearchParams();
  params.append('username', email);
  params.append('password', password);
  const r = await client.post('/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return r.data;
};

export const logout = () => client.post('/auth/logout');

export const getMe = () => client.get('/users/me').then((r) => r.data);

export const updateMe = (data) =>
  client.put('/users/me', data).then((r) => r.data);
